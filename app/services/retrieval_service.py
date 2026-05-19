import asyncio
import json
import logging
from datetime import date

from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.sparse_embedding_service import SparseEmbeddingService
from app.repositories.vector_repository import VectorRepository
from app.utils.reranking import rerank_chunks
from app.utils.llm_client import chat

logger = logging.getLogger(__name__)


def _freshness_multiplier(issued_date_str: str | None) -> float:
    """
    Returns a freshness multiplier 0.80–1.00 based on document age.
    Documents < 180 days old: 1.0 (no penalty).
    Linear decay to 0.80 over 5 years for older documents.
    Unknown date: 1.0 (neutral).
    """
    if not issued_date_str:
        return 1.0
    try:
        doc_date = date.fromisoformat(issued_date_str)
        age_days = max(0, (date.today() - doc_date).days)
        if age_days <= 180:
            return 1.0
        decay = max(0.80, 1.0 - ((age_days - 180) / 1825) * 0.20)
        return decay
    except Exception:
        return 1.0


class RetrievalService:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository,
        sparse_embedding_service: SparseEmbeddingService | None = None,
    ):
        self._embedder = embedding_service
        self._repo = vector_repository
        self._sparse_embedder = sparse_embedding_service or SparseEmbeddingService()

    async def retrieve(
        self,
        query: str,
        top_k: int = 15,
        rerank_top_k: int = 6,
        filter_regulators: list[str] | None = None,
        filter_document_type: str | None = None,
        compress: bool = True,
    ) -> list[dict]:
        """
        Full retrieval pipeline:
          1. Query rewriting (LLM) → 3 query variants
          2. Multi-query hybrid search (dense + BM25 sparse) per variant
          3. Deduplication by source::section key
          4. Post-retrieval metadata filtering (multi-regulator, document type)
          5. Cross-encoder reranking (bge-reranker-v2-m3)
          6. Temporal / freshness score boost
          7. MMR diversity filtering (deduplicate across sections)
          8. Contextual compression (LLM extracts only relevant sentences)
        """
        # ── Step 1: Query rewriting ──────────────────────────────────────────
        queries = await self._expand_queries(query)
        logger.info("[RETRIEVAL] Query variants: %s", queries)

        # ── Step 2: Multi-query hybrid retrieval ─────────────────────────────
        seen_keys: set[str] = set()
        all_chunks: list[dict] = []

        single_regulator = filter_regulators[0] if filter_regulators and len(filter_regulators) == 1 else None

        for q in queries:
            dense_embedding = self._embedder.embed_text(q)
            sparse_query = self._sparse_embedder.embed(q)

            results = await self._repo.search(
                query_embedding=dense_embedding,
                top_k=top_k,
                filter_regulator=single_regulator,
                filter_document_type=filter_document_type,
                sparse_query=sparse_query,
            )
            for chunk in results:
                chunk_key = f"{chunk.get('source')}::{chunk.get('section')}::{chunk.get('page')}"
                if chunk_key not in seen_keys:
                    seen_keys.add(chunk_key)
                    all_chunks.append(chunk)

        if not all_chunks:
            logger.warning("[RETRIEVAL] No chunks retrieved for query: %s", query)
            return []

        # ── Step 3: Post-retrieval metadata filter (multi-regulator) ─────────
        if filter_regulators and len(filter_regulators) > 1:
            all_chunks = [c for c in all_chunks if c.get("regulator") in filter_regulators]

        # ── Step 4: Cross-encoder reranking ──────────────────────────────────
        reranked = rerank_chunks(query=query, chunks=all_chunks, top_k=rerank_top_k * 2)

        # ── Step 5: Temporal / freshness scoring ─────────────────────────────
        for chunk in reranked:
            multiplier = _freshness_multiplier(chunk.get("issued_date"))
            if multiplier < 1.0:
                chunk["score"] = chunk.get("score", 1.0) * multiplier
                chunk["freshness_penalized"] = True
        reranked.sort(key=lambda c: c.get("score", 0), reverse=True)

        # ── Step 6: MMR diversity ─────────────────────────────────────────────
        diverse = self._apply_mmr(reranked, top_k=rerank_top_k)

        # ── Step 7: Contextual compression ───────────────────────────────────
        if compress:
            diverse = await self._compress_chunks(query, diverse)

        return diverse

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _expand_queries(self, query: str) -> list[str]:
        """
        Query rewriting: returns the original query + 2 legal rephrases.
        Uses the small LLM. Falls back to original-only on failure.
        """
        prompt = (
            "You are a Nigerian regulatory law expert. "
            "Given this query, produce 2 alternative phrasings using precise legal terminology "
            "a compliance professional would use when searching Nigerian financial regulations. "
            "Return ONLY a JSON array of 2 strings, no explanation.\n\n"
            f"Query: {query}"
        )
        try:
            content = await chat(
                messages=[{"role": "user", "content": prompt}],
                timeout=30.0,
            )
            clean = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            variants = json.loads(clean)
            return [query] + [v for v in variants[:2] if isinstance(v, str)]
        except Exception as exc:
            logger.debug("[RETRIEVAL] Query expansion failed (%s), using original only", exc)
            return [query]

    def _apply_mmr(self, chunks: list[dict], top_k: int) -> list[dict]:
        """
        Maximal Marginal Relevance: prevents returning multiple chunks from
        the same document section. Promotes cross-regulator diversity.
        """
        seen_sections: set[str] = set()
        result: list[dict] = []
        for chunk in chunks:
            section_key = f"{chunk.get('source')}::{chunk.get('section')}"
            if section_key not in seen_sections:
                seen_sections.add(section_key)
                result.append(chunk)
            if len(result) >= top_k:
                break
        return result

    async def _compress_chunk(self, query: str, chunk: dict) -> dict:
        """
        Contextual compression: asks the LLM to extract only the sentences
        from a chunk that directly answer the query.
        Skips chunks shorter than 300 characters (already focused).
        """
        text = chunk.get("text", "")
        if len(text) < 300:
            return chunk

        prompt = (
            f"Query: {query}\n\n"
            f"Regulation text:\n{text}\n\n"
            "Extract only the sentences from the text above that are directly relevant to the query. "
            "Return just the relevant sentences as plain text. "
            "If the full text is relevant, return it unchanged. "
            "If nothing is relevant, return an empty string."
        )
        try:
            compressed = await chat(
                messages=[{"role": "user", "content": prompt}],
                timeout=20.0,
            )
            compressed = compressed.strip()
            if compressed:
                chunk = chunk.copy()
                chunk["text"] = compressed
                chunk["compressed"] = True
        except Exception as exc:
            logger.debug("[COMPRESSION] Failed for chunk, keeping original: %s", exc)
        return chunk

    async def _compress_chunks(self, query: str, chunks: list[dict]) -> list[dict]:
        """Compress all chunks concurrently."""
        return list(await asyncio.gather(*[self._compress_chunk(query, c) for c in chunks]))
