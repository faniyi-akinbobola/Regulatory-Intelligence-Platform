"""
Sparse embedding service using BM25 via fastembed.
Generates sparse vectors for Qdrant hybrid search (dense + sparse).

The Qdrant/bm25 model is a pure statistical model with no neural network —
no GPU required and the model is tiny (~1 MB).
"""

import logging
from fastembed import SparseTextEmbedding

logger = logging.getLogger(__name__)

_model: SparseTextEmbedding | None = None


def _get_model() -> SparseTextEmbedding:
    global _model
    if _model is None:
        logger.info("[SPARSE] Loading BM25 sparse model (Qdrant/bm25)...")
        _model = SparseTextEmbedding(model_name="Qdrant/bm25")
        logger.info("[SPARSE] BM25 sparse model ready")
    return _model


class SparseEmbeddingService:
    """Generates sparse BM25 vectors for Qdrant native sparse vector support."""

    def embed(self, text: str) -> tuple[list[int], list[float]]:
        """Returns (indices, values) for a single text."""
        model = _get_model()
        result = next(model.embed([text]))
        return result.indices.tolist(), result.values.tolist()

    def embed_batch(self, texts: list[str]) -> list[tuple[list[int], list[float]]]:
        """Batch sparse embedding. More efficient than calling embed() in a loop."""
        model = _get_model()
        return [(r.indices.tolist(), r.values.tolist()) for r in model.embed(texts)]
