from sentence_transformers import CrossEncoder
from src.config import RERANKER_MODEL, TOP_K_FINAL

_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL)
    return _reranker

def rerank(query, candidates, top_k=TOP_K_FINAL):
    """candidates: list of dicts with 'text' key"""
    if not candidates:
        return []
    model = get_reranker()
    pairs = [[query, c["text"]] for c in candidates]
    scores = model.predict(pairs)
    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)
    ranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
    return ranked[:top_k]