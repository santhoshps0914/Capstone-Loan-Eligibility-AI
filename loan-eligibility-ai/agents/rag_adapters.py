"""Adapter examples for plugging real vector DB clients into the Retriever interface.

These are examples only — they show the shape of an adapter that implements
the `query(query_text, top_k)` method and returns a list of {"id":..., "content":...}.

FaissAdapter: sketch that builds a FAISS index from documents and queries using
an external embedding function (e.g., sentence-transformers).

PineconeAdapter: sketch that uses the Pinecone client to upsert vectors and
query for nearest neighbors, returning document content as evidence.

These adapters are intentionally small; adapt for your production embedding
pipeline and metadata storage.
"""

from typing import List, Dict, Callable


class FaissAdapter:
    """Minimal example adapter for FAISS.

    Usage:
      - provide `docs` as list of {"id": str, "content": str}
      - provide `embed_fn(texts: List[str]) -> List[List[float]]`

    This class does not import faiss at import-time to keep tests light. Use
    this pattern as a template when integrating FAISS.
    """

    def __init__(self, docs: List[Dict[str, str]], embed_fn: Callable[[List[str]], List[List[float]]]):
        self.docs = docs
        self.embed_fn = embed_fn
        # Defer heavy imports to runtime
        try:
            import faiss

            self.faiss = faiss
        except Exception:
            self.faiss = None

        # Build index
        self._build_index()

    def _build_index(self):
        texts = [d["content"] for d in self.docs]
        vectors = self.embed_fn(texts)
        if self.faiss is None:
            # Faiss not installed in POC environment — keep vectors for local ranking
            self._vectors = vectors
            return

        dim = len(vectors[0])
        index = self.faiss.IndexFlatIP(dim)
        import numpy as np

        arr = np.array(vectors).astype("float32")
        # normalize for IP similarity
        faiss.normalize_L2(arr)
        index.add(arr)
        self.index = index
        self._vectors = vectors

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, str]]:
        qvec = self.embed_fn([query_text])[0]
        if getattr(self, "index", None) is None:
            # Fallback: simple dot-product ranking with precomputed vectors
            scores = []
            for idx, v in enumerate(self._vectors):
                # dot
                score = sum(a * b for a, b in zip(qvec, v))
                scores.append((score, self.docs[idx]))
            scores.sort(key=lambda x: x[0], reverse=True)
            return [d for s, d in scores[:top_k]]

        import numpy as np

        q = np.array(qvec).astype("float32")
        faiss.normalize_L2(q.reshape(1, -1))
        D, I = self.index.search(q.reshape(1, -1), top_k)
        results = []
        for i in I[0]:
            results.append(self.docs[i])
        return results


class PineconeAdapter:
    """Minimal example adapter for Pinecone.

    Usage:
      - provide a `pinecone_client` and index name, and an `embed_fn`
      - call `upsert_documents` to upload docs, then use `query`

    This is a template — adjust metadata handling to your needs.
    """

    def __init__(self, pinecone_client, index_name: str, embed_fn: Callable[[List[str]], List[List[float]]]):
        self.client = pinecone_client
        self.index_name = index_name
        self.embed_fn = embed_fn

    def upsert_documents(self, docs: List[Dict[str, str]]):
        texts = [d["content"] for d in docs]
        vectors = self.embed_fn(texts)
        items = []
        for d, v in zip(docs, vectors):
            items.append({"id": d["id"], "values": v, "metadata": {"content": d["content"]}})
        idx = self.client.Index(self.index_name)
        idx.upsert(items)

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, str]]:
        qv = self.embed_fn([query_text])[0]
        idx = self.client.Index(self.index_name)
        resp = idx.query(qv, top_k=top_k, include_metadata=True)
        results = []
        for match in resp["matches"]:
            results.append({"id": match["id"], "content": match["metadata"].get("content", "")})
        return results
