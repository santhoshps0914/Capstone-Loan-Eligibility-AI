from fastapi.testclient import TestClient
from service.coordinator_service import app


client = TestClient(app)


def test_chat_endpoint_answers_a_general_question():
    resp = client.post("/chat", json={"message": "What credit score do I need?"})
    assert resp.status_code == 200
    data = resp.json()
    assert set(["answer", "sources", "mode", "suggestions"]).issubset(data.keys())
    assert "700" in data["answer"]
    assert data["mode"] == "rules"


def test_chat_endpoint_uses_the_supplied_assessment_context():
    resp = client.post(
        "/chat",
        json={
            "message": "Why does my application need review?",
            "context": {
                "decision": "Needs Manual Review",
                "credit_score": 695,
                "emi_ratio": 0.41,
                "reasoning": ["emi_ratio: FAILED (0.41) - should be <= 0.40"],
            },
        },
    )
    assert resp.status_code == 200
    assert "0.41" in resp.json()["answer"]


def test_chat_endpoint_rejects_an_empty_message():
    resp = client.post("/chat", json={"message": ""})
    assert resp.status_code == 422


def test_chat_endpoint_accepts_prior_history():
    resp = client.post(
        "/chat",
        json={
            "message": "And the age limit?",
            "history": [
                {"role": "user", "content": "What credit score do I need?"},
                {"role": "assistant", "content": "Above 700."},
            ],
        },
    )
    assert resp.status_code == 200


def test_chat_info_endpoint_reports_capabilities():
    resp = client.get("/chat/info")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["llm_enabled"], bool)
    assert len(data["suggested_questions"]) > 0
