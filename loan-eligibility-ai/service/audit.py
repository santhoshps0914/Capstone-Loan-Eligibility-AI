import json
from pathlib import Path
from datetime import datetime


LOG_PATH = Path(__file__).resolve().parent.parent / "logs"
LOG_PATH.mkdir(parents=True, exist_ok=True)
AUDIT_FILE = LOG_PATH / "audit.log"


def write_audit(request_id: str, input_summary: dict, decision: str, rag_evidence: list):
    entry = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input": input_summary,
        "decision": decision,
        "rag_ids": [d.get("id") for d in rag_evidence] if rag_evidence else [],
    }
    # append as JSON line
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
