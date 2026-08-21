from agents.rag_interface import InMemoryVectorRetriever
from agents.coordinator import CoordinatorAgent


def test_inmemory_vector_retriever_with_coordinator():
    docs = [
        {"id": "d1", "content": "Credit score above 700 is good"},
        {"id": "d2", "content": "EMI-to-income ratio should be <= 40%"},
    ]
    retriever = InMemoryVectorRetriever(docs)

    coord = CoordinatorAgent(rag_client=retriever)
    payload = {
        "name": "Swap User",
        "age": 28,
        "monthly_income": 4000,
        "existing_emi": 100,
        "credit_score": 710,
        "employment_type": "salaried",
        "loan_amount_required": 5000,
    }
    res = coord.process_application(payload)
    # Ensure rag evidence comes from our retriever
    assert "rag_evidence" in res
    assert isinstance(res["rag_evidence"], list)
