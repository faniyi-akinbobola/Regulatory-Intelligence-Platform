from sentence_transformers import CrossEncoder
import logging

logger = logging.getLogger(__name__)

_reranker: CrossEncoder | None = None


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")
    return _reranker


def rerank_chunks(query: str, chunks: list[dict], top_k: int = 6) -> list[dict]:
    if not chunks:
        return []

    reranker = _get_reranker()
    pairs = [(query, chunk.get("text", "")) for chunk in chunks]

    try:
        scores = reranker.predict(pairs)
        ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in ranked[:top_k]]
    except Exception as e:
        logger.warning("[RERANKER] Reranking failed, returning original order: %s", e)
        return chunks[:top_k]