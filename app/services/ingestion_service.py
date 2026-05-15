import hashlib
import logging
from pathlib import Path
from app.utils.parsers import parse_document
from app.utils.chunking import chunk_document, DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.repositories.vector_repository import VectorRepository

logger = logging.getLogger(__name__)


def _file_hash(pdf_path: str) -> str:
    """SHA256 hash of file contents for document-level deduplication."""
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


class IngestionService:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_repository: VectorRepository,
    ):
        self._embedding_service = embedding_service
        self._vector_repository = vector_repository

    async def ingest(self, pdf_path: str, regulator: str | None = None, document_type: str | None = None) -> dict:
        """
        Full ingestion pipeline: parse → chunk → embed → store.
        Returns a summary dict with chunk count and document metadata.
        """
        file_name = Path(pdf_path).name
        logger.info("[INGEST] Starting ingestion: %s (regulator=%s, type=%s)", file_name, regulator, document_type)

        file_hash = _file_hash(pdf_path)
        logger.debug("[INGEST] File hash: %s", file_hash)

        logger.info("[PARSE] Parsing document: %s", file_name)
        parsed = parse_document(pdf_path)
        logger.info("[PARSE] Parsed %d pages from %s", parsed.total_pages, file_name)

        full_text = parsed.full_text().strip()
        if not full_text:
            logger.warning(
                "[PARSE] No text extracted from %s — likely a scanned/image PDF. "
                "OCR is not yet supported. Skipping.",
                file_name,
            )
            raise ValueError(
                f"No text extracted from {file_name}. "
                "This appears to be a scanned PDF. OCR support is not yet implemented."
            )

        logger.info("[CHUNK] Chunking document: %s (%d chars)", file_name, len(full_text))
        chunks = chunk_document(parsed)
        logger.info("[CHUNK] Produced %d chunks from %s", len(chunks), file_name)

        if not chunks:
            logger.error("[CHUNK] Zero chunks after chunking %s — unexpected.", file_name)
            raise ValueError(f"Chunking produced no output for {file_name}.")

        # Enrich chunk metadata with regulator/type for Qdrant payload filtering
        for chunk in chunks:
            if regulator:
                chunk.metadata["regulator"] = regulator
            if document_type:
                chunk.metadata["document_type"] = document_type

        logger.info("[EMBED] Generating embeddings for %d chunks...", len(chunks))
        texts = [chunk.text for chunk in chunks]
        embeddings = self._embedding_service.embed_texts(texts)  # sync — no await
        logger.info("[EMBED] Embeddings generated for %s", file_name)

        logger.info("[STORE] Upserting %d vectors to Qdrant...", len(chunks))
        count = await self._vector_repository.upsert(chunks, embeddings)
        logger.info("[STORE] Successfully stored %d chunks for %s", count, file_name)

        return {
            "file_name": file_name,
            "file_hash": file_hash,
            "total_pages": parsed.total_pages,
            "chunks_ingested": count,
        }