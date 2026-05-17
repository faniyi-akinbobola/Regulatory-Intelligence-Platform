import uuid
import hashlib
import logging
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SparseVector,
)
from app.utils.chunking import DocumentChunk
from app.core.config import settings

logger = logging.getLogger(__name__)


def _chunk_id(document_name: str, chunk_index: int) -> str:
    """Deterministic UUID from document name + chunk index. Same chunk = same ID."""
    key = f"{document_name}::{chunk_index}"
    return str(uuid.UUID(hashlib.md5(key.encode()).hexdigest()))


def _rrf_fusion(
    dense_hits: list,
    sparse_hits: list,
    k: int = 60,
) -> list[dict]:
    """
    Reciprocal Rank Fusion across dense and sparse result lists.
    Returns deduplicated, merged result list sorted by fused score.
    """
    scores: dict[str, float] = {}
    id_to_payload: dict[str, dict] = {}

    for rank, hit in enumerate(dense_hits):
        pid = str(hit.id)
        scores[pid] = scores.get(pid, 0.0) + 1.0 / (rank + k)
        id_to_payload[pid] = hit.payload

    for rank, hit in enumerate(sparse_hits):
        pid = str(hit.id)
        scores[pid] = scores.get(pid, 0.0) + 1.0 / (rank + k)
        if pid not in id_to_payload:
            id_to_payload[pid] = hit.payload

    sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return [
        {
            "score": score,
            "text": id_to_payload[pid].get("text"),
            "source": id_to_payload[pid].get("source"),
            "page": id_to_payload[pid].get("page"),
            "section": id_to_payload[pid].get("section"),
            "title": id_to_payload[pid].get("title"),
            "hierarchy": id_to_payload[pid].get("hierarchy"),
            "regulator": id_to_payload[pid].get("regulator"),
            "document_type": id_to_payload[pid].get("document_type"),
            "issued_date": id_to_payload[pid].get("issued_date"),
        }
        for pid, score in sorted_ids
    ]


class VectorRepository:

    def __init__(self, client: AsyncQdrantClient):
        self._client = client
        self._collection = settings.qdrant_collection_name

    async def upsert(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
        sparse_embeddings: list[tuple[list[int], list[float]]] | None = None,
    ) -> int:
        """
        Upserts chunks + embeddings into Qdrant.
        Uses deterministic IDs — re-ingesting the same document overwrites, not duplicates.
        When sparse_embeddings are provided, stores both dense and sparse vectors
        for hybrid (BM25 + semantic) search. Falls back to dense-only if not provided.
        Returns number of points upserted.
        """
        points = []
        for i, (chunk, dense_vec) in enumerate(zip(chunks, embeddings)):
            if sparse_embeddings:
                sparse_indices, sparse_values = sparse_embeddings[i]
                vector = {
                    "dense": dense_vec,
                    "sparse": SparseVector(
                        indices=sparse_indices,
                        values=sparse_values,
                    ),
                }
            else:
                # Legacy: dense-only (collection without sparse vector config)
                vector = {"dense": dense_vec}

            points.append(
                PointStruct(
                    id=_chunk_id(chunk.document_name, chunk.chunk_index),
                    vector=vector,
                    payload=chunk.metadata | {
                        "text": chunk.text,
                        "hierarchy": chunk.hierarchy,
                    },
                )
            )

        await self._client.upsert(
            collection_name=self._collection,
            points=points,
        )
        return len(points)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 15,
        filter_document: str | None = None,
        filter_regulator: str | None = None,
        filter_document_type: str | None = None,
        sparse_query: tuple[list[int], list[float]] | None = None,
    ) -> list[dict]:
        """
        Hybrid semantic + BM25 search with optional metadata filters.
        When sparse_query is provided, performs parallel dense + sparse search
        and merges results with Reciprocal Rank Fusion (RRF).
        Falls back to dense-only if sparse_query is not given.
        """
        must_conditions = []
        if filter_document:
            must_conditions.append(
                FieldCondition(key="source", match=MatchValue(value=filter_document))
            )
        if filter_regulator:
            must_conditions.append(
                FieldCondition(key="regulator", match=MatchValue(value=filter_regulator))
            )
        if filter_document_type:
            must_conditions.append(
                FieldCondition(key="document_type", match=MatchValue(value=filter_document_type))
            )

        query_filter = Filter(must=must_conditions) if must_conditions else None

        # Dense (semantic) search — using named "dense" vector
        dense_response = await self._client.query_points(
            collection_name=self._collection,
            query=query_embedding,
            using="dense",
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )

        if sparse_query is None:
            # Dense-only fallback (old schema or no sparse query provided)
            return [
                {
                    "score": hit.score,
                    "text": hit.payload.get("text"),
                    "source": hit.payload.get("source"),
                    "page": hit.payload.get("page"),
                    "section": hit.payload.get("section"),
                    "title": hit.payload.get("title"),
                    "hierarchy": hit.payload.get("hierarchy"),
                    "regulator": hit.payload.get("regulator"),
                    "document_type": hit.payload.get("document_type"),
                    "issued_date": hit.payload.get("issued_date"),
                }
                for hit in dense_response.points
            ]

        # Sparse (BM25) search — using named "sparse" vector
        sparse_indices, sparse_values = sparse_query
        try:
            sparse_response = await self._client.query_points(
                collection_name=self._collection,
                query=SparseVector(indices=sparse_indices, values=sparse_values),
                using="sparse",
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
            )
            sparse_hits = sparse_response.points
        except Exception as e:
            logger.warning("[HYBRID] Sparse search failed, falling back to dense-only: %s", e)
            sparse_hits = []

        return _rrf_fusion(dense_response.points, sparse_hits)

    async def delete_document(self, document_name: str) -> None:
        """Removes all chunks belonging to a document. Useful for replacing a document."""
        await self._client.delete(
            collection_name=self._collection,
            points_selector=Filter(
                must=[FieldCondition(key="source", match=MatchValue(value=document_name))]
            ),
        )