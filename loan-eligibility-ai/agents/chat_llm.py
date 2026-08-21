"""Optional Claude-backed responder for the customer support chatbot.

This module is the only place in the project that talks to an external model.
It is deliberately opt-in: `build_responder()` returns `None` unless
`LOAN_CHAT_LLM` is set, so the default deployment stays fully offline and the
rules engine in `agents/chat_agent.py` answers every question on its own.

Enable with:
    export LOAN_CHAT_LLM=1
    export ANTHROPIC_API_KEY=sk-ant-...      # or run `ant auth login`
    export LOAN_CHAT_MODEL=claude-opus-5     # optional override
"""

from typing import Any, Dict, List, Optional
import logging
import os

from agents.chat_agent import ResponderError


logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-5"
MAX_TOKENS = 1024
# A customer is watching a spinner, so cap how long a turn can hang before we
# fall back to the rules answer. The UI gives /chat 30s in total.
REQUEST_TIMEOUT = 12.0
MAX_RETRIES = 1

SYSTEM_PROMPT = """You are the customer support assistant for a loan eligibility \
screening tool. You answer basic customer questions about the eligibility \
criteria, what a result means, and what happens next.

Rules you must follow:
- Answer only from the policy snippets and applicant result provided in the \
user message. If they do not cover the question, say you don't have that \
information and suggest contacting a loan officer.
- Never invent or guess a threshold, interest rate, fee, tenure or timeline.
- Never promise or imply that a loan will be approved. Every result is an \
automated screening outcome subject to review by a loan officer — say so when \
you discuss a decision.
- Do not give personalised financial, tax or legal advice.
- Never ask the customer for account numbers, card numbers, PAN, Aadhaar, OTPs \
or passwords.
- Be warm and plain-spoken. Keep answers under 120 words and use no more than \
four short bullet points."""


def _truthy(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _format_context(applicant_context: Optional[Dict[str, Any]]) -> str:
    """Render the applicant's assessment for the prompt.

    Only assessment fields are included — the chat path never receives the
    applicant's name, so there is nothing identifying to leak here.
    """
    if not applicant_context:
        return "No assessment has been submitted yet."

    labels = [
        ("decision", "Decision"),
        ("credit_score", "Credit score"),
        ("emi_ratio", "EMI-to-income ratio"),
        ("new_emi", "Estimated new EMI"),
        ("age", "Age"),
        ("employment_type", "Employment type"),
    ]
    lines = [f"- {label}: {applicant_context[key]}"
             for key, label in labels if applicant_context.get(key) is not None]

    for key, label in (("reasoning", "Rule checks"), ("recommendations", "Recommendations")):
        for item in applicant_context.get(key) or []:
            lines.append(f"- {label}: {item}")

    return "\n".join(lines) or "No assessment has been submitted yet."


def _build_user_message(
    message: str,
    kb_snippets: List[Dict[str, str]],
    applicant_context: Optional[Dict[str, Any]],
) -> str:
    snippets = "\n".join(
        f"[{s.get('id', 'policy')}] {s.get('content', '')}" for s in kb_snippets
    ) or "No relevant policy snippets were found."

    return (
        f"Policy snippets:\n{snippets}\n\n"
        f"This applicant's assessment:\n{_format_context(applicant_context)}\n\n"
        f"Customer question: {message}"
    )


class ClaudeResponder:
    """Rephrases retrieved policy snippets into a conversational answer."""

    def __init__(self, client: Any, model: str = DEFAULT_MODEL) -> None:
        self._client = client
        self._model = model

    def respond(
        self,
        message: str,
        kb_snippets: List[Dict[str, str]],
        applicant_context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        import anthropic

        messages: List[Dict[str, str]] = []
        for turn in (history or [])[-6:]:
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})

        messages.append({
            "role": "user",
            "content": _build_user_message(message, kb_snippets, applicant_context),
        })

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                # Answers are short and factual — low effort keeps the chat snappy.
                output_config={"effort": "low"},
                messages=messages,
            )
        # Most specific first: a 400 is our bug, a 429 is transient, a
        # connection error is the network. All degrade to the rules answer.
        except anthropic.BadRequestError as exc:
            raise ResponderError(f"bad request: {exc}") from exc
        except anthropic.AuthenticationError as exc:
            raise ResponderError("authentication failed — check ANTHROPIC_API_KEY") from exc
        except anthropic.PermissionDeniedError as exc:
            raise ResponderError("API key lacks permission for this model") from exc
        except anthropic.NotFoundError as exc:
            raise ResponderError(f"unknown model {self._model!r}") from exc
        except anthropic.RateLimitError as exc:
            raise ResponderError("rate limited") from exc
        except anthropic.APIStatusError as exc:
            raise ResponderError(f"API error {exc.status_code}") from exc
        except anthropic.APIConnectionError as exc:
            raise ResponderError(f"connection error: {exc}") from exc

        if response.stop_reason == "refusal":
            raise ResponderError("model declined to answer")

        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        if not text.strip():
            raise ResponderError("empty response")
        return text.strip()


def build_responder() -> Optional[Any]:
    """Build a `ClaudeResponder`, or return `None` to stay in rules-only mode.

    Gated on `LOAN_CHAT_LLM` rather than on the mere presence of a credential:
    a zero-argument `anthropic.Anthropic()` also picks up `ANTHROPIC_AUTH_TOKEN`
    and any `ant auth login` profile, and a developer having one of those in
    their shell must not silently turn a Streamlit form into a billed API caller.
    """
    if not _truthy(os.getenv("LOAN_CHAT_LLM")):
        logger.info("chat LLM disabled (set LOAN_CHAT_LLM=1 to enable)")
        return None

    try:
        import anthropic
    except ImportError:
        logger.warning("LOAN_CHAT_LLM is set but the 'anthropic' package is not installed")
        return None

    model = os.getenv("LOAN_CHAT_MODEL", DEFAULT_MODEL)
    try:
        # No hardcoded key: the SDK resolves ANTHROPIC_API_KEY, then
        # ANTHROPIC_AUTH_TOKEN, then an `ant auth login` profile.
        client = anthropic.Anthropic(timeout=REQUEST_TIMEOUT, max_retries=MAX_RETRIES)
    except Exception as exc:  # missing credentials, bad base URL, ...
        logger.warning("could not initialise Anthropic client: %s", exc)
        return None

    logger.info("chat LLM enabled", extra={"model": model})
    return ClaudeResponder(client=client, model=model)
