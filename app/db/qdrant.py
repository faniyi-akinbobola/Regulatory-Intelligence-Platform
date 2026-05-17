import logging
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams, SparseIndexParams
from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncQdrantClient | None = None


async def get_qdrant_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
    return _client


async def init_qdrant_collection() -> None:
    """Creates the regulations collection with dense + sparse vector support if it doesn't exist."""
    client = await get_qdrant_client()
    exists = await client.collection_exists(settings.qdrant_collection_name)
    if not exists:
        await client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config={
                "dense": VectorParams(
                    size=settings.embedding_dimension,
                    distance=Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                )
            },
        )
        logger.info(
            "[QDRANT] Created collection '%s' with dense (dim=%d) + sparse (BM25) vectors",
            settings.qdrant_collection_name,
            settings.embedding_dimension,
        )
    else:
        info = await client.get_collection(settings.qdrant_collection_name)
        has_sparse = bool(info.config.params.sparse_vectors)
        if not has_sparse:
            logger.warning(
                "[QDRANT] Collection '%s' exists without sparse vector config. "
                "Run `python scripts/reset_collection.py` to enable hybrid search, "
                "then re-ingest all documents.",
                settings.qdrant_collection_name,
            )


async def recreate_qdrant_collection() -> None:
    """
    Drop and recreate the collection with the current schema (dense + sparse).
    WARNING: All indexed data is lost. Re-ingest all documents after calling this.
    """
    client = await get_qdrant_client()
    await client.delete_collection(settings.qdrant_collection_name)
    logger.warning("[QDRANT] Dropped collection '%s'", settings.qdrant_collection_name)
    await init_qdrant_collection()
    logger.info("[QDRANT] Recreated collection '%s' with hybrid vector schema", settings.qdrant_collection_name)