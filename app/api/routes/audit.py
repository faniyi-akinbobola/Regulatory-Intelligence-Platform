from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.postgres import get_db_session
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/trace/{audit_id}", status_code=status.HTTP_200_OK)
async def get_audit_trace(
    audit_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieve the full audit trace for a completed workflow run.
    Returns agent decisions, citations, reasoning, risk assessment, and grounding score.
    """
    audit_service = AuditService(db)
    record = await audit_service.get_record(audit_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit record '{audit_id}' not found.",
        )

    return {
        "audit_id": str(record.id),
        "session_id": str(record.session_id),
        "query": record.query,
        "organization_context": record.organization_context,
        "status": record.status,
        "overall_risk_level": record.overall_risk_level,
        "hallucination_risk": record.hallucination_risk,
        "grounding_score": record.grounding_score,
        "iteration_count": record.iteration_count,
        "duration_ms": record.duration_ms,
        "created_at": record.created_at.isoformat(),
        "target_regulators": record.target_regulators,
        "agent_trace": record.agent_trace,
        "jurisdiction_result": record.jurisdiction_result,
        "reasoning_result": record.reasoning_result,
        "audit_result": record.audit_result,
        "citation_result": record.citation_result,
        "critic_result": record.critic_result,
        "final_report": record.final_report,
    }


@router.get("/session/{session_id}", status_code=status.HTTP_200_OK)
async def list_session_traces(
    session_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session),
):
    """List all audit traces for a session, newest first."""
    audit_service = AuditService(db)
    records = await audit_service.list_session_records(session_id, limit=limit)

    return [
        {
            "audit_id": str(r.id),
            "query": r.query,
            "status": r.status,
            "overall_risk_level": r.overall_risk_level,
            "hallucination_risk": r.hallucination_risk,
            "grounding_score": r.grounding_score,
            "iteration_count": r.iteration_count,
            "duration_ms": r.duration_ms,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]
