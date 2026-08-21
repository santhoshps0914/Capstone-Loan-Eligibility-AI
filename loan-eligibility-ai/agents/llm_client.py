"""Provider-switching LLM client for the chat agent.

Exposes one interface — `LLMProvider.run_tool_loop()` — over two wire formats so
the rest of the app never branches on provider:

* `AnthropicProvider`  — native Messages API via the `anthropic` SDK.
* `OpenRouterProvider` — OpenAI-compatible chat/completions via the `openai` SDK,
  which is the only format OpenRouter accepts (it has no `/v1/messages`).

Selection is by environment variable, checked in this order:
  1. ANTHROPIC_API_KEY -> AnthropicProvider  (native API wins when both are set)
  2. OPENROUTER_API_KEY -> OpenRouterProvider
  3. neither -> `get_provider()` returns None and the chat feature reports itself
     as unconfigured instead of raising at import time.

Tools are declared once in the neutral shape `{name, description, input_schema}`
(JSON Schema) and translated per provider here.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Cap on agentic loop iterations, so a misbehaving model cannot spin forever.
MAX_TOOL_ITERATIONS = 6

# `max_tokens` for chat replies. Deliberately modest — replies are short and
# conversational, and this keeps well clear of SDK HTTP timeouts.
MAX_TOKENS = 4096

DEFAULT_ANTHROPIC_MODEL = "claude-opus-5"
DEFAULT_OPENROUTER_MODEL = "anthropic/claude-opus-5"


def load_dotenv(path: Optional[Path] = None) -> None:
    """Populate os.environ from a `.env` file without adding a dependency.

    Existing environment variables always win, so an exported key overrides the
    file. Silently does nothing when the file is absent.
    """
    env_path = path or Path(__file__).resolve().parent.parent / ".env"
    try:
        raw = env_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return

    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class ToolCall:
    """One model request to run a tool, normalised across providers."""

    def __init__(self, call_id: str, name: str, arguments: Dict[str, Any]) -> None:
        self.call_id = call_id
        self.name = name
        self.arguments = arguments


class LLMProvider:
    """Common surface for a chat completion with a client-side tool loop."""

    name = "unknown"
    model = "unknown"

    def run_tool_loop(
        self,
        system: str,
        history: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        execute_tool: Callable[[str, Dict[str, Any]], Any],
    ) -> Dict[str, Any]:
        """Run the conversation to completion, executing tools as requested.

        Args:
            system: System prompt.
            history: Prior turns as `{"role": "user"|"assistant", "content": str}`,
                ending with the newest user message.
            tools: Neutral tool specs — `{name, description, input_schema}`.
            execute_tool: Callback `(name, arguments) -> JSON-serialisable result`.

        Returns:
            `{"reply": str, "tools_used": List[str]}`
        """
        raise NotImplementedError


class AnthropicProvider(LLMProvider):
    """Native Anthropic Messages API with a manual agentic loop."""

    name = "anthropic"

    def __init__(self, api_key: str, model: Optional[str] = None) -> None:
        import anthropic  # imported lazily so the app runs without the SDK

        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
        self._effort = os.environ.get("CHAT_EFFORT", "medium")

    @staticmethod
    def _to_native_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["input_schema"],
            }
            for t in tools
        ]

    def run_tool_loop(self, system, history, tools, execute_tool):
        messages: List[Dict[str, Any]] = [
            {"role": m["role"], "content": m["content"]} for m in history
        ]
        native_tools = self._to_native_tools(tools)
        tools_used: List[str] = []

        for _ in range(MAX_TOOL_ITERATIONS):
            response = self._client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=messages,
                tools=native_tools,
                thinking={"type": "adaptive"},
                output_config={"effort": self._effort},
            )

            if response.stop_reason == "refusal":
                return {
                    "reply": "I'm not able to answer that one. Please ask me about "
                             "loan eligibility, the assessment criteria, or your "
                             "application.",
                    "tools_used": tools_used,
                }

            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            if not tool_use_blocks:
                text = "".join(b.text for b in response.content if b.type == "text")
                return {"reply": text.strip(), "tools_used": tools_used}

            messages.append({"role": "assistant", "content": response.content})

            results = []
            for block in tool_use_blocks:
                tools_used.append(block.name)
                payload, is_error = _safe_execute(execute_tool, block.name, block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": payload,
                    "is_error": is_error,
                })
            messages.append({"role": "user", "content": results})

        return {
            "reply": "I wasn't able to finish working that out. Could you rephrase "
                     "or ask something more specific?",
            "tools_used": tools_used,
        }


class OpenRouterProvider(LLMProvider):
    """OpenAI-compatible chat/completions against OpenRouter's gateway."""

    name = "openrouter"
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str, model: Optional[str] = None) -> None:
        from openai import OpenAI  # imported lazily so the app runs without the SDK

        self._client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.model = model or os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)

    @staticmethod
    def _to_native_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ]

    def run_tool_loop(self, system, history, tools, execute_tool):
        messages: List[Dict[str, Any]] = [{"role": "system", "content": system}]
        messages += [{"role": m["role"], "content": m["content"]} for m in history]
        native_tools = self._to_native_tools(tools)
        tools_used: List[str] = []

        for _ in range(MAX_TOOL_ITERATIONS):
            response = self._client.chat.completions.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                messages=messages,
                tools=native_tools,
            )
            choice = response.choices[0]
            message = choice.message

            if not message.tool_calls:
                return {"reply": (message.content or "").strip(), "tools_used": tools_used}

            # Echo the assistant turn back verbatim, including the tool calls.
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ],
            })

            for tc in message.tool_calls:
                tools_used.append(tc.function.name)
                try:
                    arguments = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    arguments = {}
                payload, _ = _safe_execute(execute_tool, tc.function.name, arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": payload,
                })

        return {
            "reply": "I wasn't able to finish working that out. Could you rephrase "
                     "or ask something more specific?",
            "tools_used": tools_used,
        }


def _safe_execute(
    execute_tool: Callable[[str, Dict[str, Any]], Any],
    name: str,
    arguments: Any,
) -> tuple:
    """Run a tool, returning `(serialised_result, is_error)`.

    A tool that raises is reported back to the model as an error result rather
    than aborting the turn — the model can then apologise or ask for what's
    missing instead of the user seeing a 500.
    """
    if not isinstance(arguments, dict):
        arguments = {}
    try:
        result = execute_tool(name, arguments)
    except Exception as exc:  # noqa: BLE001 - surfaced to the model, not swallowed
        logger.warning("tool %s failed: %s", name, exc)
        return f"Error running {name}: {exc}", True

    if isinstance(result, str):
        return result, False
    try:
        return json.dumps(result, default=str), False
    except (TypeError, ValueError):
        return str(result), False


def get_provider() -> Optional[LLMProvider]:
    """Build a provider from the environment, or None if no key is configured."""
    load_dotenv()

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key:
        try:
            return AnthropicProvider(anthropic_key)
        except ImportError:
            logger.warning("ANTHROPIC_API_KEY is set but the `anthropic` package is missing")

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if openrouter_key:
        try:
            return OpenRouterProvider(openrouter_key)
        except ImportError:
            logger.warning("OPENROUTER_API_KEY is set but the `openai` package is missing")

    return None
