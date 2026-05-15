# app/services/retrieval_service.py

from app.services.embedding_service import EmbeddingService
from app.repositories.vector_repository import VectorRepository
from app.utils.reranking import rerank


class RetrievalService:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository,
    ):
        self._embedding_service = embedding_service
        self._vector_repository = vector_repository

    async def retrieve(
        self,
        query: str,
        top_k: int = 20,
        top_n_reranked: int = 8,
        filter_regulator: str | None = None,
        filter_document: str | None = None,
    ) -> list[dict]:
        """
        Embed query → search Qdrant → rerank → return top_n_reranked chunks.
        Returns empty list if nothing found — callers must handle this.
        (No retrieval = no answer, per architecture principle)
        """
        query_vector = self._embedding_service.embed_text(query)

        results = await self._vector_repository.search(
            query_embedding=query_vector,
            top_k=top_k,
            filter_regulator=filter_regulator,
            filter_document=filter_document,
        )

        if not results:
            return []

        return rerank(query, results, top_n=top_n_reranked)