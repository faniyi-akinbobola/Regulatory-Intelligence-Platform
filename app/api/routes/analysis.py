import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db_session
from app.services.compliance_service import ComplianceService

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    query: str
    session_id: str | None = None
    organization_context: str | None = None


class ComplianceGapRequest(BaseModel):
    business_description: str
    session_id: str | None = None
    target_regulators: list[str] | None = None


@router.post(
    "/analyze-business",
    status_code=status.HTTP_200_OK,
    summary="Submit a compliance question and receive a structured analysis report",
)
async def analyze_business(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Main regulatory intelligence endpoint.
    Runs the full multi-agent workflow and returns a citation-backed compliance report.
    """
    session_id = uuid.UUID(request.session_id) if request.session_id else uuid.uuid4()

    try:
        result = await ComplianceService(db).analyze(
            query=request.query,
            session_id=session_id,
            organization_context=request.organization_context,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    return result


@router.post(
    "/compliance-gap",
    status_code=status.HTTP_200_OK,
    summary="Identify compliance gaps between a business and applicable regulations",
)
async def compliance_gap_analysis(
    request: ComplianceGapRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Compares the business description against ingested regulations
    and identifies missing controls, gaps, and unmet obligations.
    """
    session_id = uuid.UUID(request.session_id) if request.session_id else uuid.uuid4()

    try:
        result = await ComplianceService(db).analyze_gap(
            business_description=request.business_description,
            session_id=session_id,
            target_regulators=request.target_regulators,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    return result