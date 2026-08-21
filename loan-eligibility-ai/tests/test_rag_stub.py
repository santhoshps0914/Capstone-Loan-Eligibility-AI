from agents.rag_stub import RAGClientStub
from agents.coordinator import CoordinatorAgent


def test_rag_stub_returns_docs():
    rag = RAGClientStub()
    docs = rag.query("credit score and EMI")
    assert isinstance(docs, list)
    assert len(docs) > 0


def test_coordinator_includes_rag_evidence():
    coord = CoordinatorAgent()
    data = {
        "name": "Bob",
        "age": 30,
        "monthly_income": 4000,
        "existing_emi": 200,
        "credit_score": 720,
        "employment_type": "salaried",
        "loan_amount_required": 6000,
    }
    res = coord.process_application(data)
    assert "rag_evidence" in res
    assert isinstance(res["rag_evidence"], list)
