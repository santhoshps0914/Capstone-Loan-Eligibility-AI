"""FastAPI service that exposes the CoordinatorAgent as an HTTP endpoint.

Run with:
  uvicorn service.coordinator_service:app --reload

This demonstrates how the coordinator can run as a separate process.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from schemas.models import Application
from agents.coordinator import CoordinatorAgent
from logging_config import configure_logging
from service.audit import write_audit
import uuid
import logging


configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Loan Eligibility Coordinator Service")

# Allow local Streamlit UI to call the service during development
app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost", "http://localhost:8501", "http://localhost"],
  allow_methods=["*"],
  allow_headers=["*"],
)

coord = CoordinatorAgent()


@app.post("/process")
def process_application(payload: Application, request: Request):
  """Accepts an `Application` payload, validates it via Pydantic, and returns the coordinator response.

  This endpoint reads `X-Request-ID` from the incoming headers or generates one,
  uses it for structured logs, and writes an audit entry to `logs/audit.log`.
  """
  request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
  logger.info("received request", extra={"request_id": request_id, "path": request.url.path})

  # `payload` is already validated by FastAPI/Pydantic
  res = coord.process_application(payload.model_dump())

  # Write audit entry
  try:
    input_summary = {
      "name": payload.name,
      "age": payload.age,
      "monthly_income": payload.monthly_income,
    }
  except Exception:
    input_summary = {}

  write_audit(request_id, input_summary, res.get("decision"), res.get("rag_evidence", []))
  logger.info("processed request", extra={"request_id": request_id, "decision": res.get("decision")})
  return res
