import uuid
from fastapi import APIRouter, HTTPException, status
from app.models.responses import AuditTraceResponse
router = APIRouter(prefix="/audit", tags=["audit"])

@router.get(
    "/{report_id}",
    response_model=AuditTraceResponse,
    summary="Retrieve full agent workflow trace for a compliance report",
)
async def get_audit_trace(
    report_id: uuid.UUID,  
) -> AuditTraceResponse:
    """
    Returns the complete strp-by-step agent execution trace for a report.
    This supports explainability and auditability, you can see exactly what each agent did,
    what citations it used, and what reasoning it applied.
    """
    # b query goes in here
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Audit trace not found."
    )