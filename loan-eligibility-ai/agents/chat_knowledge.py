"""FAQ knowledge base for the customer support chatbot.

Answers here are derived from the actual rules implemented in
`agents/eligibility_agent.py` — keep the two in sync. If a threshold changes
there, update the matching entry below and the test that asserts on it.

Each entry is a dict with:
  id       - stable identifier used as the citation label in the UI
  question - the canonical phrasing of the question
  answer   - the customer-facing answer
  keywords - extra terms that should match this entry during retrieval
"""

from typing import Dict, List


FAQS: List[Dict[str, str]] = [
    {
        "id": "faq-credit-score",
        "question": "What credit score do I need to be eligible?",
        "answer": (
            "Your credit score must be above 700 to pass the credit check. "
            "Scores between 690 and 710 are treated as borderline and are sent "
            "for manual review rather than being rejected outright."
        ),
        "keywords": "credit score cibil minimum required 700 rating",
    },
    {
        "id": "faq-emi-ratio",
        "question": "What is the maximum EMI-to-income ratio allowed?",
        "answer": (
            "Your total EMI burden — existing EMIs plus the new loan EMI — must "
            "be at most 40% of your monthly income. Ratios between 38% and 42% "
            "are borderline and go to manual review."
        ),
        "keywords": "emi income ratio 40 percent obligation debt burden maximum limit",
    },
    {
        "id": "faq-age",
        "question": "What is the eligible age range?",
        "answer": "Applicants must be between 21 and 60 years old at the time of application.",
        "keywords": "age old young 21 60 years eligible range minimum maximum",
    },
    {
        "id": "faq-employment",
        "question": "Which employment types are accepted?",
        "answer": (
            "Salaried and government employment are treated as stable and "
            "strengthen your application. Self-employed and other categories are "
            "still accepted, but they do not count towards the stability check."
        ),
        "keywords": "employment job salaried govt government self-employed business work type",
    },
    {
        "id": "faq-emi-estimate",
        "question": "How is my new EMI calculated?",
        "answer": (
            "This assessment uses a simple, conservative estimate: the requested "
            "loan amount divided by 12. It is an indicative figure for screening "
            "only — your actual EMI depends on the final tenure and interest rate "
            "quoted by the lender."
        ),
        "keywords": "new emi calculated estimate monthly installment amount tenure interest",
    },
    {
        "id": "faq-manual-review",
        "question": "What does 'Needs Manual Review' mean?",
        "answer": (
            "It means your application is close to one of the thresholds rather "
            "than clearly outside it. A loan officer will look at your case "
            "personally and may still approve it."
        ),
        "keywords": "manual review yellow borderline pending what does mean status",
    },
    {
        "id": "faq-not-eligible",
        "question": "What does 'Not Eligible' mean and what can I do?",
        "answer": (
            "It means at least one required check — credit score, age, or EMI "
            "ratio — was missed by a clear margin. You can reapply after "
            "improving your credit score, reducing existing EMIs, or requesting a "
            "smaller loan amount."
        ),
        "keywords": "not eligible rejected declined red refused reapply again denied",
    },
    {
        "id": "faq-improve-score",
        "question": "How can I improve my credit score?",
        "answer": (
            "Pay every EMI and credit card bill on time, keep card utilisation "
            "below 30%, avoid opening several new credit accounts at once, and "
            "check your credit report for errors you can dispute. Scores usually "
            "take a few months to respond."
        ),
        "keywords": "improve increase raise credit score better fix repair boost",
    },
    {
        "id": "faq-reduce-emi-ratio",
        "question": "How can I reduce my EMI-to-income ratio?",
        "answer": (
            "Either lower the numerator or raise the denominator: close or "
            "prepay an existing loan, request a smaller loan amount, ask for a "
            "longer tenure, add a co-applicant's income, or apply after a salary "
            "increase."
        ),
        "keywords": "reduce lower emi ratio obligation smaller loan tenure co-applicant income",
    },
    {
        "id": "faq-colours",
        "question": "What do the green, yellow and red results mean?",
        "answer": (
            "Green means Eligible — all required checks passed. Yellow means "
            "Needs Manual Review — you are near a threshold. Red means Not "
            "Eligible — a required check was clearly missed."
        ),
        "keywords": "green yellow red colour color badge decision meaning legend status",
    },
    {
        "id": "faq-final-decision",
        "question": "Is this decision final?",
        "answer": (
            "No. This is an automated screening result based only on the details "
            "you entered. Every outcome is subject to verification and final "
            "approval by a loan officer."
        ),
        "keywords": "final binding guaranteed approval decision automated official confirm",
    },
    {
        "id": "faq-next-steps",
        "question": "What happens after I am found eligible?",
        "answer": (
            "A loan officer contacts you to verify your details and collect "
            "documents — typically identity and address proof, income proof such "
            "as salary slips or returns, and recent bank statements. Nothing is "
            "disbursed until that verification is complete."
        ),
        "keywords": "next steps after eligible documents paperwork proof contact disbursed process",
    },
    {
        "id": "faq-how-long",
        "question": "How long does the assessment take?",
        "answer": (
            "The automated assessment is instant — you see the result as soon as "
            "you submit the form, and you can download a PDF report immediately. "
            "Manual review by a loan officer takes longer."
        ),
        "keywords": "how long time take instant fast quick duration wait result",
    },
    {
        "id": "faq-data-privacy",
        "question": "Is my data stored?",
        "answer": (
            "This assessment tool keeps an internal audit record of each request "
            "for traceability. Please do not enter account numbers, card numbers, "
            "PAN, Aadhaar, OTPs or passwords anywhere in this tool — they are "
            "never required for an eligibility check."
        ),
        "keywords": "data stored privacy secure safe personal information audit share",
    },
    {
        "id": "faq-reapply",
        "question": "Can I run the assessment again with different numbers?",
        "answer": (
            "Yes. Adjust the loan amount, income or other details and click "
            "Evaluate Eligibility again — for example, requesting a smaller "
            "amount lowers your estimated EMI and improves your EMI ratio."
        ),
        "keywords": "again reapply retry resubmit change different amount recalculate",
    },
    {
        "id": "faq-interest-rate",
        "question": "What interest rate will I get?",
        "answer": (
            "This tool does not quote interest rates. It only checks eligibility "
            "against the screening criteria. Your rate is set by the lender based "
            "on their pricing policy and your final verified profile."
        ),
        "keywords": "interest rate roi pricing cost charges quote apr",
    },
]


def faq_documents() -> List[Dict[str, str]]:
    """Return the FAQ as retriever documents.

    The shape matches what `agents.rag_interface.InMemoryVectorRetriever`
    expects (`{"id", "content"}`), so the existing retriever can rank the FAQ
    without any new retrieval code.
    """
    return [
        {
            "id": f["id"],
            "content": f"{f['question']} {f['answer']} {f['keywords']}",
        }
        for f in FAQS
    ]


def faq_by_id(faq_id: str) -> Dict[str, str]:
    """Look up a single FAQ entry by its id. Returns {} when not found."""
    for f in FAQS:
        if f["id"] == faq_id:
            return f
    return {}


def suggested_questions(limit: int = 3) -> List[str]:
    """Return a few example questions to show the customer as starting points."""
    preferred = ["faq-credit-score", "faq-emi-ratio", "faq-manual-review", "faq-next-steps"]
    questions = [faq_by_id(i)["question"] for i in preferred if faq_by_id(i)]
    return questions[:limit]
