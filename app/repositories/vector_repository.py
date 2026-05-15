import uuid
import hashlib
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from app.utils.chunking import DocumentChunk
from app.core.config import settings


def _chunk_id(document_name: str, chunk_index: int) -> str:
    """Deterministic UUID from document name + chunk index. Same chunk = same ID."""
    key = f"{document_name}::{chunk_index}"
    return str(uuid.UUID(hashlib.md5(key.encode()).hexdigest()))


class VectorRepository:

    def __init__(self, client: AsyncQdrantClient):
        self._client = client
        self._collection = settings.qdrant_collection_name

    async def upsert(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> int:
        """
        Upserts chunks + embeddings into Qdrant.
        Uses deterministic IDs — re-ingesting the same document overwrites, not duplicates.
        Returns number of points upserted.
        """
        points = [
            PointStruct(
                id=_chunk_id(chunk.document_name, chunk.chunk_index),
                vector=embedding,
                payload=chunk.metadata | {
                    "text": chunk.text,
                    "hierarchy": chunk.hierarchy,
                },
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

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
    ) -> list[dict]:
        """
        Semantic search with optional metadata filters.
        filter_document: restrict to a specific document name
        filter_regulator: restrict to a specific regulator tag
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

        query_filter = Filter(must=must_conditions) if must_conditions else None

        results = await self._client.search(
            collection_name=self._collection,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )

        return [
            {
                "score": hit.score,
                "text": hit.payload.get("text"),
                "source": hit.payload.get("source"),
                "page": hit.payload.get("page"),
                "section": hit.payload.get("section"),
                "title": hit.payload.get("title"),
                "hierarchy": hit.payload.get("hierarchy"),
            }
            for hit in results
        ]

    async def delete_document(self, document_name: str) -> None:
        """Removes all chunks belonging to a document. Useful for replacing a document."""
        await self._client.delete(
            collection_name=self._collection,
            points_selector=Filter(
                must=[FieldCondition(key="source", match=MatchValue(value=document_name))]
            ),
        )