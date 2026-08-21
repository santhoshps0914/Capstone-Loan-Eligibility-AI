"""Simple RAG/MCP stub interface

This is a minimal replaceable stub that simulates a RAG (retrieval-augmented generation)
or MCP knowledge lookup. It returns a small set of 'documents' relevant to a query.

Replace this with a real client (vector DB + retriever) in production.
"""

from typing import List, Dict


class RAGClientStub:
    """Return a small set of stubbed documents for any query."""

    def __init__(self) -> None:
        # Example in-repo knowledge snippets
        self._docs = [
            {"id": "rules-1", "content": "Credit score above 700 is considered good."},
            {"id": "rules-2", "content": "EMI-to-income ratio should generally be <= 40%."},
            {"id": "rules-3", "content": "Preferred employment: salaried, govt."},
        ]

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, str]]:
        """Return top_k docs with a simple string-match ranking.

        This is intentionally trivial; a production retriever would score by vector similarity.
        """
        lowered = query_text.lower()
        scored = []
        for d in self._docs:
            score = 0
            if any(tok in d["content"].lower() for tok in lowered.split()):
                score += 1
            scored.append((score, d))

        # sort by score desc, then return top_k docs
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for s, d in scored[:top_k]]
