"""Customer support Chat Agent.

Answers basic customer queries about loan eligibility. Two layers:

1. A deterministic layer (safety guard -> result-aware intents -> FAQ
   retrieval) that always works with no network access and no API key.
2. An optional `Responder` (see `agents/chat_llm.py`) that rephrases the
   retrieved FAQ snippets into a conversational answer. If it is absent or
   fails, the deterministic answer is returned instead.

Keeping the agent free of any network dependency is what makes it unit
testable, and it means the demo never breaks because a key is missing.
"""

from typing import Any, Dict, List, Optional, Protocol
import logging
import re

from agents.chat_knowledge import faq_by_id, faq_documents, suggested_questions
from agents.rag_interface import InMemoryVectorRetriever, Retriever


logger = logging.getLogger(__name__)


class ResponderError(RuntimeError):
    """Raised by a Responder when it cannot produce an answer.

    The agent catches this and falls back to the deterministic answer.
    """


class Responder(Protocol):
    """Optional conversational backend that rephrases retrieved snippets."""

    def respond(
        self,
        message: str,
        kb_snippets: List[Dict[str, str]],
        applicant_context: Optional[Dict[str, Any]],
        history: Optional[List[Dict[str, str]]],
    ) -> str:
        ...


# Words that carry no retrieval signal — dropped before scoring a question.
STOPWORDS = {
    "a", "about", "am", "an", "and", "any", "are", "as", "at", "be", "been",
    "by", "can", "could", "did", "do", "does", "for", "from", "get", "give",
    "has", "have", "how", "i", "if", "in", "is", "it", "its", "know", "many",
    "me", "much", "my", "need", "of", "on", "or", "please", "should", "so",
    "tell", "that", "the", "then", "there", "these", "this", "to", "was",
    "want", "what", "when", "where", "which", "who", "why", "will", "with",
    "would", "you", "your",
}

# Confidence floor below which we treat the question as out of scope.
CONFIDENCE_FLOOR = 0.34

OUT_OF_SCOPE_ANSWER = (
    "I can only help with questions about this loan eligibility check — "
    "the criteria we apply, what your result means, and what to do next. "
    "Try one of the suggested questions below, or contact a loan officer for "
    "anything else."
)

NO_ASSESSMENT_ANSWER = (
    "I don't have your assessment yet. Fill in the form and click "
    "'Evaluate Eligibility' first, then ask me again and I can explain your "
    "specific result."
)

SENSITIVE_DATA_ANSWER = (
    "⚠️ Please don't share account numbers, card numbers, PAN, Aadhaar, OTPs "
    "or passwords here — an eligibility check never needs them. I can still "
    "help with questions about the eligibility criteria and your result."
)

# Anything matching these means the message may contain sensitive identifiers.
_SENSITIVE_PATTERNS = [
    re.compile(r"\d[\d\s-]{10,}"),                      # long digit runs (cards, accounts)
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),              # PAN-shaped token
    re.compile(r"\baadha?ar\b", re.I),
    re.compile(r"\b(account|a/c|debit card|credit card)\s*(no|number|num)\b", re.I),
    re.compile(r"\b(otp|cvv|pin|password|passcode)\b", re.I),
]

# First-person markers: a result-aware intent only fires if the customer is
# asking about themselves, so "how do I improve a credit score" stays a
# general FAQ question rather than a lookup against their own result.
_FIRST_PERSON = re.compile(r"\b(my|mine|i|me|am|we|our)\b", re.I)


def _tokens(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS]


def _looks_sensitive(message: str) -> bool:
    return any(p.search(message) for p in _SENSITIVE_PATTERNS)


def _pct(value: Any) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "unavailable"


def _money(value: Any) -> str:
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "unavailable"


class ChatAgent:
    """Answers basic customer queries, optionally via a conversational backend."""

    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        responder: Optional[Responder] = None,
    ) -> None:
        # Reuse the project's existing in-memory retriever over the FAQ.
        self.retriever: Retriever = retriever or InMemoryVectorRetriever(faq_documents())
        self.responder: Optional[Responder] = responder

    # ------------------------------------------------------------------ public

    @property
    def llm_enabled(self) -> bool:
        return self.responder is not None

    def answer(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Answer one customer message.

        Returns a dict with `answer`, `sources`, `mode` ("rules" or "llm") and
        `suggestions`.
        """
        message = (message or "").strip()
        if not message:
            return self._result(OUT_OF_SCOPE_ANSWER, [], "rules")

        # 1. Never let sensitive identifiers reach retrieval, logs or the LLM.
        if _looks_sensitive(message):
            return self._result(SENSITIVE_DATA_ANSWER, [], "rules")

        # 2. Questions about the customer's own result have exact answers.
        intent = self._match_intent(message)
        if intent is not None:
            resolved = self._answer_intent(intent, context)
            if resolved is not None:
                answer, source_ids = resolved
                sources = [d for d in (self._source(i) for i in source_ids) if d]
                return self._result(answer, sources, "rules")

            # The question was about their own result, but no assessment has
            # been submitted. Say so — and still answer generally if we can.
            general = self._retrieve(message)
            if general:
                faq = faq_by_id(general[0]["id"])
                answer = f"{NO_ASSESSMENT_ANSWER}\n\nIn general: {faq.get('answer', '')}".strip()
                return self._result(answer, general, "rules")
            return self._result(NO_ASSESSMENT_ANSWER, [], "rules")

        # 3. Rank the FAQ for everything else.
        sources = self._retrieve(message)
        if not sources:
            return self._result(OUT_OF_SCOPE_ANSWER, [], "rules")

        fallback_answer = faq_by_id(sources[0]["id"]).get("answer", OUT_OF_SCOPE_ANSWER)

        # 4. Let the responder rephrase, but never let it break the reply.
        if self.responder is not None:
            try:
                llm_answer = self.responder.respond(
                    message=message,
                    kb_snippets=sources,
                    applicant_context=context,
                    history=history,
                )
                if llm_answer and llm_answer.strip():
                    return self._result(llm_answer.strip(), sources, "llm")
                logger.warning("responder returned an empty answer; using FAQ text")
            except ResponderError as exc:
                logger.warning("responder unavailable, falling back to rules: %s", exc)

        return self._result(fallback_answer, sources, "rules")

    # ----------------------------------------------------------------- helpers

    def _result(self, answer: str, sources: List[Dict[str, str]], mode: str) -> Dict[str, Any]:
        return {
            "answer": answer,
            "sources": sources,
            "mode": mode,
            "suggestions": suggested_questions(),
        }

    def _source(self, faq_id: str) -> Dict[str, str]:
        """Render an FAQ entry as a citation the UI can display."""
        faq = faq_by_id(faq_id)
        if not faq:
            return {}
        return {"id": faq["id"], "content": f"{faq['question']} {faq['answer']}"}

    def _retrieve(self, message: str) -> List[Dict[str, str]]:
        """Return confident FAQ citations for a message, best first.

        Empty when nothing clears `CONFIDENCE_FLOOR` — i.e. the question is
        outside what this chatbot knows about.
        """
        docs = self.retriever.query(message, top_k=3)
        scored = [(self._confidence(message, d), d) for d in docs]
        scored = [(s, d) for s, d in scored if s >= CONFIDENCE_FLOOR]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for d in (self._source(doc["id"]) for _, doc in scored) if d]

    def _confidence(self, message: str, doc: Dict[str, str]) -> float:
        """Share of the question's meaningful words that appear in the document.

        `InMemoryVectorRetriever` returns ranked docs but not their scores, so
        the agent scores the returned candidates itself to decide whether the
        best match is actually relevant or just the least irrelevant.
        """
        q_tokens = set(_tokens(message))
        if not q_tokens:
            return 0.0
        d_tokens = set(_tokens(doc.get("content", "")))
        return len(q_tokens & d_tokens) / len(q_tokens)

    # ------------------------------------------------------------------ intents

    def _match_intent(self, message: str) -> Optional[str]:
        """Identify a question about the customer's own assessment."""
        if not _FIRST_PERSON.search(message):
            return None

        lowered = message.lower()

        def has(*terms: str) -> bool:
            return any(t in lowered for t in terms)

        # Ordered most specific first.
        if has("why") and has(
            "decision", "reject", "declin", "review", "eligib", "result",
            "refus", "denied", "fail",
        ):
            return "why"
        if has("recommend", "what should i do", "improve my application",
               "improve my chances", "improve my profile", "what can i do",
               "next step"):
            return "improve"
        if has("emi ratio", "emi-to-income", "emi to income", "ratio"):
            return "emi_ratio"
        if has("my emi", "my new emi", "my monthly payment", "my installment"):
            return "new_emi"
        if has("my credit score", "my score", "my cibil"):
            return "credit_score"
        if has("decision", "result", "am i eligible", "my status", "did i qualify",
               "was i approved", "my outcome"):
            return "decision"
        return None

    def _answer_intent(self, intent: str, context: Optional[Dict[str, Any]]):
        """Answer a result-aware intent.

        Returns `(answer, [faq_id, ...])`, or `None` when the assessment data
        this intent needs is not available.
        """
        ctx = context or {}
        if not ctx:
            return None

        if intent == "decision":
            decision = ctx.get("decision")
            if not decision:
                return None
            explain = {
                "Eligible": "All required checks passed.",
                "Needs Manual Review": (
                    "You are close to one of the thresholds, so a loan officer "
                    "will review your case personally."
                ),
                "Not Eligible": (
                    "At least one required check — credit score, age or EMI "
                    "ratio — was missed by a clear margin."
                ),
            }.get(decision, "")
            return (
                f"Your latest assessment result is: {decision}. {explain} "
                "This is an automated screening result and is subject to review "
                "by a loan officer."
            ).strip(), ["faq-colours", "faq-final-decision"]

        if intent == "why":
            reasoning = ctx.get("reasoning") or []
            decision = ctx.get("decision", "your result")
            if not reasoning:
                return None
            checks = "\n".join(f"- {r}" for r in reasoning)
            return (
                f"'{decision}' came from these checks:\n{checks}\n"
                "Each line shows the rule, whether it passed, and the value we used."
            ), ["faq-manual-review", "faq-not-eligible"]

        if intent == "improve":
            recs = ctx.get("recommendations") or []
            if not recs:
                if ctx.get("decision") == "Eligible":
                    return (
                        "Nothing to fix — your profile passed every check. A loan "
                        "officer will contact you to verify your details.",
                        ["faq-next-steps"],
                    )
                return None
            steps = "\n".join(f"{i}. {r}" for i, r in enumerate(recs, 1))
            return (
                f"Based on your assessment, here is what would help:\n{steps}"
            ), ["faq-improve-score", "faq-reduce-emi-ratio"]

        if intent == "emi_ratio":
            ratio = ctx.get("emi_ratio")
            if ratio is None:
                return None
            verdict = (
                "within the 40% limit" if float(ratio) <= 0.40
                else "above the 40% limit"
            )
            return (
                f"Your EMI-to-income ratio is {_pct(ratio)}, which is {verdict}. "
                "It combines your existing EMIs with the estimated EMI for this "
                "loan, divided by your monthly income."
            ), ["faq-emi-ratio", "faq-reduce-emi-ratio"]

        if intent == "new_emi":
            emi = ctx.get("new_emi")
            if emi is None:
                return None
            return (
                f"Your estimated EMI for this loan is {_money(emi)} per month. "
                "That is a conservative screening estimate (loan amount ÷ 12) — "
                "your actual EMI depends on the final tenure and interest rate."
            ), ["faq-emi-estimate"]

        if intent == "credit_score":
            score = ctx.get("credit_score")
            if score is None:
                return None
            verdict = (
                "above the 700 requirement" if int(score) > 700
                else "not above the 700 requirement"
            )
            return (
                f"The credit score used in your assessment was {score}, which is "
                f"{verdict}."
            ), ["faq-credit-score", "faq-improve-score"]

        return None
