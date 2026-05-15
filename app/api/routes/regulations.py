# from fastapi import FastAPI
# from app.services.ingestion_service import IngestionService

# app = FastAPI()

# @app.post("/regulations/upload")
# async def upload_regulations(path: str):
#     ingestion_service = IngestionService()
#     result = await ingestion_service.ingest(path)
#     return result

import hashlib
import tempfile
import os
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.postgres import get_db_session
from app.db.qdrant import get_qdrant_client
from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository
from app.services.embedding_service import EmbeddingService
from app.services.ingestion_service import IngestionService
from app.core.config import settings

router = APIRouter(prefix="/regulations", tags=["regulations"])

# Instantiated once at import time — model loads only on first request
_embedding_service = EmbeddingService(settings.embedding_model_name)


def _hash_upload(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_regulation(
    file: UploadFile = File(...),
    regulator: str = Form(..., description="e.g. CBN, SEC, NDIC, FIRS"),
    document_type: str = Form(..., description="e.g. Guideline, Circular, Act, Regulation"),
    notes: str | None = Form(None),
    db: AsyncSession = Depends(get_db_session),
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    file_bytes = await file.read()
    file_hash = _hash_upload(file_bytes)

    doc_repo = DocumentRepository(db)

    # Dedup check — reject if same content already ingested
    if await doc_repo.exists_by_hash(file_hash):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document with identical content already ingested. Skipping.",
        )

    # Write to temp file for parsers (they need a file path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        qdrant_client = await get_qdrant_client()
        vector_repo = VectorRepository(qdrant_client)
        ingestion_service = IngestionService(_embedding_service, vector_repo)

        result = await ingestion_service.ingest(tmp_path, regulator=regulator, document_type=document_type)

        await doc_repo.save({
            "file_name": file.filename,
            "file_hash": file_hash,
            "regulator": regulator,
            "document_type": document_type,
            "total_pages": result["total_pages"],
            "chunks_ingested": result["chunks_ingested"],
            "notes": notes,
        })

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    finally:
        os.unlink(tmp_path)  # always clean up temp file

    return {
        "message": "Document ingested successfully.",
        "file_name": file.filename,
        "regulator": regulator,
        "total_pages": result["total_pages"],
        "chunks_ingested": result["chunks_ingested"],
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def list_regulations(db: AsyncSession = Depends(get_db_session)):
    """Lists all ingested regulatory documents."""
    doc_repo = DocumentRepository(db)
    records = await doc_repo.get_all()
    return [
        {
            "id": r.id,
            "file_name": r.file_name,
            "regulator": r.regulator,
            "document_type": r.document_type,
            "total_pages": r.total_pages,
            "chunks_ingested": r.chunks_ingested,
            "ingested_at": r.ingested_at.isoformat(),
        }
        for r in records
    ]

@router.delete("/{doc_id}", status_code=status.HTTP_200_OK)
async def delete_regulation(
    doc_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    doc_repo = DocumentRepository(db)
    record = await doc_repo.get_by_id(doc_id)

    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")

    qdrant_client = await get_qdrant_client()
    vector_repo = VectorRepository(qdrant_client)
    await vector_repo.delete_document(record.file_name)

    await doc_repo.delete(doc_id)

    return {"message": f"Document '{record.file_name}' and all its chunks deleted."}