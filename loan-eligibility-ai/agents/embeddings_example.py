"""Embedding wiring examples for the POC.

This module shows two example embedder factories:
- `get_sentence_transformers_embed_fn(model_name)`: uses `sentence_transformers` if installed.
- `get_fallback_embed_fn(dim)`: returns a deterministic, lightweight embedding used
  for local testing when heavyweight models are unavailable.

It also includes `demo_end_to_end()` which wires an embedder into
`InMemoryVectorRetriever`, injects it into `CoordinatorAgent`, and runs a sample
query to demonstrate retrieval evidence in the coordinator response.
"""

from typing import List, Callable
from agents.rag_interface import InMemoryVectorRetriever


def get_sentence_transformers_embed_fn(model_name: str = "all-MiniLM-L6-v2") -> Callable[[List[str]], List[List[float]]]:
    """Return an embedding function using sentence-transformers if available.

    If `sentence_transformers` is not installed, this will raise ImportError.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise ImportError("sentence-transformers not installed") from e

    model = SentenceTransformer(model_name)

    def embed_fn(texts: List[str]):
        vecs = model.encode(texts, convert_to_numpy=True)
        return [list(map(float, v)) for v in vecs]

    return embed_fn


def get_fallback_embed_fn(dim: int = 16):
    """Return a deterministic lightweight embedder for testing.

    This maps tokens to pseudo-random but deterministic vector positions using
    simple hashing; useful for local tests and CI where heavy models aren't available.
    """
    def embed_fn(texts: List[str]):
        out = []
        for t in texts:
            v = [0.0] * dim
            for i, tok in enumerate(t.lower().split()):
                idx = hash(tok) % dim
                v[idx] += (i + 1) * 0.1
            out.append(v)
        return out

    return embed_fn


def demo_end_to_end(use_sentence_transformers: bool = False):
    """Run an end-to-end retrieval + coordinator demo and return the coordinator response.

    If `use_sentence_transformers` is True, the function will attempt to use
    sentence-transformers; otherwise it uses the fallback embedder.
    """
    # Example documents
    docs = [
        {"id": "d1", "content": "Credit score above 700 is considered healthy"},
        {"id": "d2", "content": "EMI-to-income ratio should usually be <= 40%"},
        {"id": "d3", "content": "Salaried and govt jobs are considered stable employment"},
    ]

    if use_sentence_transformers:
        embed_fn = get_sentence_transformers_embed_fn()
    else:
        embed_fn = get_fallback_embed_fn(dim=32)

    retriever = InMemoryVectorRetriever(docs)
    # Note: InMemoryVectorRetriever expects docs at construction; embedding function
    # is only needed if you are using an adapter that requires embeddings. For this
    # demo we rely on the retriever's simple token-vectorization, but show how to
    # obtain an embed_fn for real adapters.

    # Wire retriever into coordinator
    from agents.coordinator import CoordinatorAgent

    coord = CoordinatorAgent(rag_client=retriever)

    payload = {
        "name": "Demo User",
        "age": 34,
        "monthly_income": 6000,
        "existing_emi": 300,
        "credit_score": 730,
        "employment_type": "salaried",
        "loan_amount_required": 10000,
    }

    res = coord.process_application(payload)
    return res
