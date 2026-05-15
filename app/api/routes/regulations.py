import uuid
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status
from app.api.dependencies import OptionalUser
from app.models.responses import (
    DocumentListResponse,
    DocumentStatusResponse,
    RegulationUploadResponse,
)

router = APIRouter(prefix="/regulations", tags=['regulations'])

async def _run_ingestion_pipeline(
        document_id: uuid.UUID,
        file_bytes: bytes,
        filename: str 
) -> None:
    """
    Background task that will hand off to the ingestion service.
    The actual implementation will be added once the ingestion service is ready.
    """
    print(f"Ingestion started for document {document_id} - {filename}")
    # ingestion service goes here later

@router.post(
    "/upload",
    response_model=RegulationUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a regulatory PDF for ingestion into the vector store",
)

async def upload_regulation(
    background_tasks: BackgroundTasks,
    current_user: OptionalUser,
    file: UploadFile = File(..., description="PDF file of the regulatory document"),
    title: str = Form(..., min_length=1, max_length=500),
    regulator: str = Form(..., description="e.g. CBN, SEC, NDIC, FIRS"),
    document_type: str | None = Form(default=None),
    version: str | None = Form(default=None),
) -> RegulationUploadResponse:
    # validate file type
    if file.content_type not in ("application/pdf", "application/actet-stream"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are accepted.",
        )
    
    # Read file
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    
    # Generate a document ID - the DB layer replaces this later
    document_id = uuid.uuid4()

    # Queue ingestion as a background task so the API responds immediately
    background_tasks.add_task(
        _run_ingestion_pipeline,
        document_id=document_id,
        file_bytes=file_bytes,
        filename=file.filename or "unknown.pdf",
    )

    return RegulationUploadResponse(
        document_id=document_id,
        title=title,
        regulator=regulator,
        status="pending",
        message="Document received and queued for ingestion.",
    )

@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all ingested regulatory documents",
)

async def list_documents(
    regulator: str | None = None,
    doc_status: str | None = None,
    limit: int=50,
    offset: int=0
) -> DocumentListResponse:
    # DB query goes here
    return DocumentListResponse(documents=[], total=0)


@router.get(
    "/{document_id}",
    response_model=DocumentStatusResponse,
    summary="Check ingestion status of a regulatory document",
)
async def get_document_status(
    document_id: uuid.UUID,
) -> DocumentStatusResponse:
    # DB query goes here

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Document not found."
    )


