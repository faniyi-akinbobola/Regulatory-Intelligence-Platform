import asyncio
import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import OptionalUser
from app.db.postgres import get_db_session
from app.models.requests import BusinessAnalysisRequest, ComplianceGapRequest
from app.models.responses import AnalysisInitiatedResponse, LLMMetrics, ReportStatusResponse
from app.services.compliance_service import ComplianceService

router = APIRouter(prefix="/analyze", tags=["analysis"])

# In-memory store for streaming progress — replaced by Redis later
_reports: dict[str, dict] = {}


async def _run_workflow(
    report_id: str,
    query: str,
    db: AsyncSession,
    organization_context: str | None = None,
    target_regulators: list[str] | None = None,
    session_id: str | None = None,
) -> None:
    """
    Background task that invokes ComplianceService which runs
    the full LangGraph multi-agent workflow and persists results to DB.
    """
    _reports[report_id] = {"status": "running", "report": None, "trace": []}
    try:
        if target_regulators:
            query = f"{query} Focus on these regulators: {', '.join(target_regulators)}."

        # Honour caller-supplied session_id so all queries from one UI session
        # are grouped under the same audit records. Fall back to report_id.
        effective_session_id = uuid.UUID(session_id) if session_id else uuid.UUID(report_id)

        result = await ComplianceService(db).analyze(
            query=query,
            session_id=effective_session_id,
            organization_context=organization_context,
        )
        _reports[report_id] = {
            "status": "completed",
            "report": result,
            "trace": result.get("agent_trace", []),
        }
    except Exception as exc:
        _reports[report_id] = {
            "status": "failed",
            "report": None,
            "error": str(exc),
            "trace": [],
        }


@router.post(
    "/analyze-business",
    status_code=status.HTTP_200_OK,
    summary="Submit a compliance question and receive a structured analysis report",
)
async def analyze_business(
    request: BusinessAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: OptionalUser,
    db: AsyncSession = Depends(get_db_session),
) -> AnalysisInitiatedResponse:
    report_id = str(uuid.uuid4())

    query = request.business_description
    if request.business_sector:
        query = f"[Sector: {request.business_sector}] {query}"

    background_tasks.add_task(
        _run_workflow,
        report_id=report_id,
        query=query,
        db=db,
        organization_context=request.organization_context,
        target_regulators=request.target_regulators,
        session_id=str(request.session_id) if request.session_id else None,
    )

    return AnalysisInitiatedResponse(
        report_id=uuid.UUID(report_id),
        workflow_status="pending",
        message="Analysis initiated. Poll /analyze/report/{report_id} for results.",
    )


@router.post(
    "/compliance-gap",
    response_model=AnalysisInitiatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Analyse compliance gaps between a business and applicable regulations",
)
async def compliance_gap_analysis(
    request: ComplianceGapRequest,
    background_tasks: BackgroundTasks,
    current_user: OptionalUser,
    db: AsyncSession = Depends(get_db_session),
) -> AnalysisInitiatedResponse:
    report_id = str(uuid.uuid4())

    gap_query = (
        f"Perform a compliance gap analysis for the following business: "
        f"{request.business_description}. "
        f"Identify missing controls, unmet obligations, and regulatory gaps."
    )

    if request.target_regulators:
        gap_query += f" Focus specifically on: {', '.join(request.target_regulators)}."

    background_tasks.add_task(
        _run_workflow,
        report_id=report_id,
        query=gap_query,
        db=db,
        target_regulators=request.target_regulators,
        session_id=str(request.session_id) if request.session_id else None,
    )

    return AnalysisInitiatedResponse(
        report_id=uuid.UUID(report_id),
        workflow_status="pending",
        message="Gap analysis initiated. Poll /analyze/report/{report_id} for results.",
    )


@router.get(
    "/report/{report_id}",
    response_model=ReportStatusResponse,
    summary="Retrieve a completed compliance analysis report",
)
async def get_report(report_id: str) -> ReportStatusResponse:
    if report_id not in _reports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )
    entry = _reports[report_id]
    result = entry.get("report") or {}
    raw_metrics = result.get("llm_metrics")
    llm_metrics = LLMMetrics(**raw_metrics) if raw_metrics else None
    return ReportStatusResponse(
        report_id=report_id,
        status=entry["status"],
        audit_id=result.get("audit_id"),
        session_id=result.get("session_id"),
        report=result.get("final_report"),
        error=entry.get("error"),
        llm_metrics=llm_metrics,
        grounding_score=result.get("grounding_score"),
        hallucination_risk=result.get("hallucination_risk"),
        iteration_count=result.get("iteration_count"),
        agent_trace=result.get("agent_trace"),
    )


@router.get(
    "/report/{report_id}/stream",
    summary="Stream agent workflow progress as server-sent events",
)
async def stream_report(report_id: str) -> StreamingResponse:
    """
    Streams real-time agent progress back to the client using
    Server-Sent Events. The client stays connected and receives
    an update each time an agent completes its step.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        seen_steps: set[int] = set()
        max_polls = 120

        for _ in range(max_polls):
            report = _reports.get(report_id)

            if report:
                for i, step in enumerate(report.get("trace", [])):
                    if i not in seen_steps:
                        seen_steps.add(i)
                        yield f"data: {json.dumps(step)}\n\n"

                if report["status"] in ("completed", "failed"):
                    yield f"data: {json.dumps({'event': 'done', 'status': report['status']})}\n\n"
                    break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )