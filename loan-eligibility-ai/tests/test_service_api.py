from fastapi.testclient import TestClient
from service.coordinator_service import app


def test_process_endpoint():
    client = TestClient(app)
    payload = {
        "name": "API User",
        "age": 32,
        "monthly_income": 4500,
        "existing_emi": 200,
        "credit_score": 730,
        "employment_type": "salaried",
        "loan_amount_required": 8000,
    }
    resp = client.post("/process", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "decision" in data
    assert "reasoning" in data
    assert "rag_evidence" in data
