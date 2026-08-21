import os
import json
from pathlib import Path
from fastapi.testclient import TestClient
from service.coordinator_service import app


def test_audit_written_with_request_id(tmp_path):
    # Ensure logs directory is isolated per test run by using tmp_path
    # But our audit writer writes to project logs/ by default; remove existing file if present
    project_root = Path(__file__).resolve().parent.parent
    audit_file = project_root / "logs" / "audit.log"
    if audit_file.exists():
        audit_file.unlink()

    client = TestClient(app)
    req_id = "test-request-123"
    payload = {
        "name": "Audit User",
        "age": 40,
        "monthly_income": 5000,
        "existing_emi": 200,
        "credit_score": 740,
        "employment_type": "salaried",
        "loan_amount_required": 9000,
    }

    resp = client.post("/process", json=payload, headers={"X-Request-ID": req_id})
    assert resp.status_code == 200

    assert audit_file.exists(), "audit.log file should exist"
    # read last line
    with audit_file.open("r", encoding="utf-8") as f:
        lines = f.read().strip().splitlines()
    assert lines, "audit.log should contain at least one entry"
    last = json.loads(lines[-1])
    assert last.get("request_id") == req_id
    assert last.get("decision") in ("Eligible", "Not Eligible", "Needs Manual Review")
