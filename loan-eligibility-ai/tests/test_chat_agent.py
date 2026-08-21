"""Tests for the customer support chat agent.

No test here touches the network: the optional LLM path is exercised with
injected fake responders.
"""

from agents.chat_agent import (
    NO_ASSESSMENT_ANSWER,
    OUT_OF_SCOPE_ANSWER,
    ChatAgent,
    ResponderError,
)
from agents.chat_llm import build_responder


ASSESSMENT = {
    "decision": "Needs Manual Review",
    "credit_score": 695,
    "emi_ratio": 0.35,
    "new_emi": 15000.0,
    "age": 35,
    "employment_type": "salaried",
    "reasoning": ["credit_score: FAILED (695) - credit score must exceed 700"],
    "recommendations": ["Improve your credit score from 695 to above 700"],
}


class FakeResponder:
    """Records calls and returns a canned answer."""

    def __init__(self, answer="Rephrased answer from the model."):
        self.answer = answer
        self.calls = []

    def respond(self, message, kb_snippets, applicant_context=None, history=None):
        self.calls.append(message)
        return self.answer


class BrokenResponder:
    def __init__(self):
        self.calls = []

    def respond(self, message, kb_snippets, applicant_context=None, history=None):
        self.calls.append(message)
        raise ResponderError("simulated outage")


def test_general_faq_question_is_answered_from_rules():
    res = ChatAgent().answer("What credit score do I need?")
    assert res["mode"] == "rules"
    assert "700" in res["answer"]
    assert res["sources"], "a general FAQ answer should cite its source"


def test_out_of_scope_question_gets_scoped_reply_with_suggestions():
    res = ChatAgent().answer("Who won the cricket match last night?")
    assert res["answer"] == OUT_OF_SCOPE_ANSWER
    assert res["mode"] == "rules"
    assert len(res["suggestions"]) > 0


def test_result_aware_emi_ratio_uses_the_applicants_own_number():
    res = ChatAgent().answer("What is my EMI ratio?", context=ASSESSMENT)
    assert "35" in res["answer"]
    assert res["mode"] == "rules"


def test_result_aware_why_question_echoes_the_rule_checks():
    res = ChatAgent().answer("Why does my application need review?", context=ASSESSMENT)
    assert "credit score must exceed 700" in res["answer"]


def test_result_aware_improvement_question_echoes_recommendations():
    res = ChatAgent().answer("What can I do to improve my chances?", context=ASSESSMENT)
    assert "above 700" in res["answer"]


def test_result_aware_question_without_context_says_no_assessment_yet():
    res = ChatAgent().answer("What is my EMI ratio?")
    assert res["answer"].startswith(NO_ASSESSMENT_ANSWER)
    assert res["mode"] == "rules"


def test_sensitive_input_is_refused_and_never_reaches_the_responder():
    responder = FakeResponder()
    res = ChatAgent(responder=responder).answer("My card number is 4111 1111 1111 1111")
    assert "don't share" in res["answer"]
    assert responder.calls == [], "sensitive text must not be forwarded to the model"


def test_responder_answer_is_used_and_reported_as_llm_mode():
    responder = FakeResponder()
    res = ChatAgent(responder=responder).answer("What credit score do I need?")
    assert res["mode"] == "llm"
    assert res["answer"] == "Rephrased answer from the model."
    assert res["sources"], "LLM answers still cite the policy snippets used"
    assert len(responder.calls) == 1


def test_responder_failure_falls_back_to_the_rules_answer():
    responder = BrokenResponder()
    res = ChatAgent(responder=responder).answer("What credit score do I need?")
    assert res["mode"] == "rules"
    assert "700" in res["answer"]
    assert len(responder.calls) == 1


def test_responder_is_bypassed_for_exact_result_questions():
    responder = FakeResponder()
    res = ChatAgent(responder=responder).answer("What is my EMI ratio?", context=ASSESSMENT)
    assert res["mode"] == "rules"
    assert responder.calls == [], "exact numbers should not cost an API call"


def test_empty_message_is_handled():
    res = ChatAgent().answer("   ")
    assert res["answer"] == OUT_OF_SCOPE_ANSWER


def test_llm_enabled_flag_reflects_the_responder():
    assert ChatAgent().llm_enabled is False
    assert ChatAgent(responder=FakeResponder()).llm_enabled is True


def test_build_responder_returns_none_without_opt_in(monkeypatch):
    monkeypatch.delenv("LOAN_CHAT_LLM", raising=False)
    assert build_responder() is None


def test_build_responder_stays_disabled_when_flag_is_falsy(monkeypatch):
    monkeypatch.setenv("LOAN_CHAT_LLM", "0")
    assert build_responder() is None
