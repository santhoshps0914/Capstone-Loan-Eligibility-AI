"""Tests for the optional Claude responder.

The Anthropic client is stubbed, so these exercise the real request-building
and error-mapping code without making a network call.
"""

import anthropic
import httpx
import pytest

from agents.chat_agent import ResponderError
from agents.chat_llm import ClaudeResponder, _format_context


SNIPPETS = [{"id": "faq-credit-score", "content": "What credit score do I need? Above 700."}]


class FakeBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class FakeResponse:
    def __init__(self, text="Above 700 is what you need.", stop_reason="end_turn"):
        self.content = [FakeBlock(text)] if text is not None else []
        self.stop_reason = stop_reason


class FakeMessages:
    """Captures the kwargs passed to messages.create, or raises `error`."""

    def __init__(self, response=None, error=None):
        self.response = response or FakeResponse()
        self.error = error
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, response=None, error=None):
        self.messages = FakeMessages(response=response, error=error)


def _api_error(cls, status_code):
    """Build a real SDK exception without touching the network."""
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status_code, request=request, json={"error": {"message": "x"}})
    return cls("boom", response=response, body=None)


def test_successful_response_returns_the_text():
    client = FakeClient(FakeResponse("Above 700 is what you need."))
    responder = ClaudeResponder(client=client, model="claude-opus-5")

    answer = responder.respond("What credit score do I need?", SNIPPETS)

    assert answer == "Above 700 is what you need."
    kwargs = client.messages.kwargs
    assert kwargs["model"] == "claude-opus-5"
    assert kwargs["max_tokens"] == 1024
    assert "loan eligibility" in kwargs["system"]
    assert kwargs["output_config"] == {"effort": "low"}


def test_snippets_and_question_are_sent_to_the_model():
    client = FakeClient()
    ClaudeResponder(client=client).respond("What credit score do I need?", SNIPPETS)

    content = client.messages.kwargs["messages"][-1]["content"]
    assert "faq-credit-score" in content
    assert "What credit score do I need?" in content


def test_history_is_replayed_and_truncated_to_six_turns():
    client = FakeClient()
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"turn {i}"}
               for i in range(10)]

    ClaudeResponder(client=client).respond("And the age limit?", SNIPPETS, history=history)

    messages = client.messages.kwargs["messages"]
    assert len(messages) == 7  # 6 replayed turns + the new question
    assert messages[0]["content"] == "turn 4"


def test_applicant_context_is_included_when_present():
    client = FakeClient()
    ClaudeResponder(client=client).respond(
        "Why do I need review?",
        SNIPPETS,
        applicant_context={"decision": "Needs Manual Review", "credit_score": 695},
    )

    content = client.messages.kwargs["messages"][-1]["content"]
    assert "Needs Manual Review" in content
    assert "695" in content


def test_format_context_handles_a_missing_assessment():
    assert "No assessment" in _format_context(None)
    assert "No assessment" in _format_context({})


@pytest.mark.parametrize(
    "error",
    [
        _api_error(anthropic.BadRequestError, 400),
        _api_error(anthropic.AuthenticationError, 401),
        _api_error(anthropic.PermissionDeniedError, 403),
        _api_error(anthropic.NotFoundError, 404),
        _api_error(anthropic.RateLimitError, 429),
        _api_error(anthropic.InternalServerError, 500),
        anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com")),
    ],
)
def test_every_api_error_becomes_a_responder_error(error):
    """ChatAgent only catches ResponderError, so nothing else may escape."""
    responder = ClaudeResponder(client=FakeClient(error=error))
    with pytest.raises(ResponderError):
        responder.respond("What credit score do I need?", SNIPPETS)


def test_refusal_is_treated_as_a_failure():
    client = FakeClient(FakeResponse("", stop_reason="refusal"))
    with pytest.raises(ResponderError):
        ClaudeResponder(client=client).respond("What credit score do I need?", SNIPPETS)


def test_empty_response_is_treated_as_a_failure():
    client = FakeClient(FakeResponse(""))
    with pytest.raises(ResponderError):
        ClaudeResponder(client=client).respond("What credit score do I need?", SNIPPETS)
