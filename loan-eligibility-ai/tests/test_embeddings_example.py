from agents.embeddings_example import demo_end_to_end, get_fallback_embed_fn


def test_demo_end_to_end_fallback():
    res = demo_end_to_end(use_sentence_transformers=False)
    assert "rag_evidence" in res
    assert isinstance(res["rag_evidence"], list)


def test_fallback_embed_fn():
    fn = get_fallback_embed_fn(dim=8)
    vecs = fn(["credit score above 700", "emi ratio <= 0.4"])
    assert len(vecs) == 2
    assert all(len(v) == 8 for v in vecs)
