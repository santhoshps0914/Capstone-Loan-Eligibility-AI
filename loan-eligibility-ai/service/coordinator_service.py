"""FastAPI service that exposes the CoordinatorAgent as an HTTP endpoint.

Run with:
  uvicorn service.coordinator_service:app --reload

This demonstrates how the coordinator can run as a separate process.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from schemas.models import Application, ChatInfoResponse, ChatRequest, ChatResponse
from agents.coordinator import CoordinatorAgent
from agents.chat_agent import ChatAgent
from agents.chat_knowledge import suggested_questions
from agents.chat_llm import build_responder
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

# Built once at import. `build_responder()` returns None unless LOAN_CHAT_LLM
# is set, in which case the agent answers from its rules engine alone.
chat_agent = ChatAgent(responder=build_responder())


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


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request):
  """Answer a basic customer query about eligibility criteria or their result.

  Mirrors `/process`: reads `X-Request-ID` from the headers or generates one,
  logs it, and writes an audit entry.

  The raw question is never logged or audited — only its length and the FAQ
  entries that matched. Customers do sometimes type account details into a
  chat box, and `logs/audit.log` is plaintext.
  """
  request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
  logger.info(
    "received chat request",
    extra={"request_id": request_id, "path": request.url.path, "message_length": len(payload.message)},
  )

  context = payload.context.model_dump() if payload.context else None
  history = [turn.model_dump() for turn in payload.history[-6:]]

  res = chat_agent.answer(payload.message, context=context, history=history)

  write_audit(
    request_id,
    {"message_length": len(payload.message), "has_context": context is not None},
    f"chat:{res['mode']}",
    res.get("sources", []),
  )
  logger.info("answered chat request", extra={"request_id": request_id, "mode": res["mode"]})
  return res


@app.get("/chat/info", response_model=ChatInfoResponse)
def chat_info():
  """Report chat capabilities so the UI can render a mode badge and prompts."""
  return {
    "llm_enabled": chat_agent.llm_enabled,
    "suggested_questions": suggested_questions(),
  }
