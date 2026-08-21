"""RAG Retriever interface and simple in-memory vector retriever.

This file defines a small `Retriever` Protocol that production retrievers
should implement. It also includes a tiny `InMemoryVectorRetriever` which
constructs very small TF-like vectors over the stub documents and ranks by
cosine similarity. This is purely illustrative — replace with a real
vector DB client (FAISS, Pinecone, Milvus, etc.) in production.
"""

from typing import Protocol, List, Dict
import math


class Retriever(Protocol):
    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, str]]:
        ...


class InMemoryVectorRetriever:
    """Builds simple token-count vectors from provided documents and ranks by cosine similarity."""

    def __init__(self, docs: List[Dict[str, str]]):
        self.docs = docs
        # Precompute term vectors
        self.doc_vectors = [self._vectorize(d["content"]) for d in docs]

    def _vectorize(self, text: str):
        vec = {}
        for tok in text.lower().split():
            vec[tok] = vec.get(tok, 0) + 1
        return vec

    def _dot(self, a, b):
        s = 0.0
        for k, v in a.items():
            s += v * b.get(k, 0)
        return s

    def _norm(self, a):
        return math.sqrt(sum(v * v for v in a.values()))

    def _cosine(self, a, b):
        na = self._norm(a)
        nb = self._norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return self._dot(a, b) / (na * nb)

    def query(self, query_text: str, top_k: int = 3):
        qv = self._vectorize(query_text)
        scores = []
        for idx, dv in enumerate(self.doc_vectors):
            score = self._cosine(qv, dv)
            scores.append((score, self.docs[idx]))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [d for s, d in scores[:top_k]]
