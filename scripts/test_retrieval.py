"""
Quick retrieval smoke test.
Tests the embedding + Qdrant search pipeline directly (no HTTP).

Usage:
    uv run python scripts/test_retrieval.py

Expects:
    - Qdrant running on localhost:6333
    - At least one document ingested in the 'regulations' collection
"""

import asyncio
import sys
import os

# Add project root to path so app.* imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.sparse_embedding_service import SparseEmbeddingService
from app.repositories.vector_repository import VectorRepository
from app.utils.citations import format_citation
from qdrant_client import AsyncQdrantClient


TEST_QUERIES = [
    "What are the contactless payment transaction limits in Nigeria?",
    "What are the consumer protection obligations for financial institutions?",
    "What licensing requirements apply to payment service providers?",
]


async def run():
    print(f"\n{'='*70}")
    print("  RETRIEVAL SMOKE TEST")
    print(f"  Qdrant: {settings.qdrant_host}:{settings.qdrant_port}")
    print(f"  Collection: {settings.qdrant_collection_name}")
    print(f"  Embedding model: {settings.embedding_model_name}")
    print(f"{'='*70}\n")

    print("Loading embedding models...")
    embedder = EmbeddingService(settings.embedding_model_name)
    sparse_embedder = SparseEmbeddingService()
    print("Models ready.\n")

    client = AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    repo = VectorRepository(client)

    # Check collection stats
    info = await client.get_collection(settings.qdrant_collection_name)
    print(f"Collection stats: {info.points_count} points indexed\n")

    if info.points_count == 0:
        print("ERROR: No points in collection. Ingest documents first.")
        return

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[Query {i}] {query}")
        print("-" * 60)

        embedding = embedder.embed_text(query)
        sparse_query = sparse_embedder.embed(query)
        results = await repo.search(
            query_embedding=embedding,
            top_k=3,
            sparse_query=sparse_query,
        )

        if not results:
            print("  No results found.\n")
            continue

        for j, chunk in enumerate(results, 1):
            citation = format_citation(chunk)
            score = chunk.get("score", 0)
            text_preview = (chunk.get("text") or "")[:200].replace("\n", " ")
            print(f"  [{j}] score={score:.4f}  {citation}")
            print(f"       {text_preview}...")
            print()

    await client.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(run())
