"""Run embeddings demo with sentence-transformers if available.

Usage:
  .venv/bin/python examples/run_embeddings_demo.py

The script will attempt to import `sentence_transformers`. If available it will
run `demo_end_to_end(use_sentence_transformers=True)` and print the coordinator
response. Otherwise it will print instructions to install the package or run the
fallback demo inside `agents.embeddings_example`.
"""

import argparse
import json
import os
import sys
from typing import List, Dict

from agents.embeddings_example import demo_end_to_end, get_sentence_transformers_embed_fn, get_fallback_embed_fn


def run_with_adapter(adapter, payload: Dict):
    """Run coordinator with the provided adapter as the retriever."""
    from agents.coordinator import CoordinatorAgent

    coord = CoordinatorAgent(rag_client=adapter)
    return coord.process_application(payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-faiss", action="store_true", help="Use FaissAdapter if available")
    parser.add_argument("--use-pinecone", action="store_true", help="Use PineconeAdapter if credentials are set")
    parser.add_argument("--force-fallback", action="store_true", help="Use fallback embedder even if sentence-transformers is present")
    args = parser.parse_args()

    docs = [
        {"id": "d1", "content": "Credit score above 700 is considered healthy"},
        {"id": "d2", "content": "EMI-to-income ratio should usually be <= 40%"},
        {"id": "d3", "content": "Salaried and govt jobs are considered stable employment"},
    ]

    payload = {
        "name": "Demo User",
        "age": 34,
        "monthly_income": 6000,
        "existing_emi": 300,
        "credit_score": 730,
        "employment_type": "salaried",
        "loan_amount_required": 10000,
    }

    # Determine embedder
    embed_fn = None
    if not args.force_fallback:
        try:
            embed_fn = get_sentence_transformers_embed_fn()
        except Exception:
            embed_fn = None

    if embed_fn is None:
        embed_fn = get_fallback_embed_fn(dim=32)

    # Adapter selection
    if args.use_faiss:
        try:
            from agents.rag_adapters import FaissAdapter

            faiss_adapter = FaissAdapter(docs, embed_fn)
            print("Using FaissAdapter (local). Running coordinator...")
            res = run_with_adapter(faiss_adapter, payload)
            print(json.dumps(res, indent=2))
            return
        except Exception as e:
            print(f"FaissAdapter unavailable: {e}")

    if args.use_pinecone:
        try:
            import pinecone

            api_key = os.environ.get("PINECONE_API_KEY")
            env = os.environ.get("PINECONE_ENV")
            if not api_key or not env:
                print("PINECONE_API_KEY and PINECONE_ENV must be set to use PineconeAdapter")
            else:
                pinecone.init(api_key=api_key, environment=env)
                from agents.rag_adapters import PineconeAdapter

                client = pinecone
                idx_name = os.environ.get("PINECONE_INDEX", "loan-poc-index")
                adapter = PineconeAdapter(client, idx_name, embed_fn)
                # upsert docs
                adapter.upsert_documents(docs)
                print("Upserted docs to Pinecone index. Running coordinator...")
                res = run_with_adapter(adapter, payload)
                print(json.dumps(res, indent=2))
                return
        except Exception as e:
            print(f"Pinecone adapter/setup failed: {e}")

    # Default: run demo with in-memory retriever (sentence-transformers or fallback)
    use_st = embed_fn is not None and not isinstance(embed_fn, type(get_fallback_embed_fn()))
    if use_st:
        print("Running demo with sentence-transformers embedder and in-memory retriever...")
        res = demo_end_to_end(use_sentence_transformers=True)
    else:
        print("Running demo with fallback embedder and in-memory retriever...")
        res = demo_end_to_end(use_sentence_transformers=False)

    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
