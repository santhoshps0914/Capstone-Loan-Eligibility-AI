"""Coordinator (Triage) Agent

Simple in-process orchestrator that validates input, calls the EligibilityAgent,
and composes a human-readable response.
"""

from typing import Any, Dict, Optional
from schemas.models import Application
from agents.eligibility_agent import EligibilityAgent
from agents.rag_stub import RAGClientStub
from agents.rag_interface import Retriever


class CoordinatorAgent:
    def __init__(self, rag_client: Optional[Retriever] = None) -> None:
        self.eligibility = EligibilityAgent()
        # Accept any Retriever implementation. Default to the simple stub.
        self.rag: Retriever = rag_client or RAGClientStub()

    def process_application(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Parse and validate input using pydantic model
        app = Application(**data)

        # Delegate to EligibilityAgent
        result = self.eligibility.evaluate(app)

        # Optionally query RAG for related policy snippets to include as evidence.
        rag_query = f"credit score {app.credit_score} emi_ratio {round(result['emi_ratio'],3)}"
        rag_docs = self.rag.query(rag_query)

        # Compose a readable reasoning list
        reasoning = []
        for r in result["rule_results"]:
            status = "PASSED" if r["passed"] else "FAILED"
            reasoning.append(f"{r['rule']}: {status} ({r['value']}) - {r['note']}")

        return {
            "decision": result["decision"],
            "new_emi": result["new_emi"],
            "emi_ratio": result["emi_ratio"],
            "reasoning": reasoning,
            "rag_evidence": rag_docs,
        }
