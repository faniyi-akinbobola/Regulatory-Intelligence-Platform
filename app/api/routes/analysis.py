import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import OptionalUser
from app.graph.workflow import workflow
from app.models.requests import BusinessAnalysisRequest, ComplianceGapRequest
from app.models.responses import AnalysisInitiatedResponse, ComplianceReportResponse

router = APIRouter(prefix="/analyze", tags=["analysis"])

# In-memory store for reports — will be replaced by DB later
_reports: dict[str, dict] = {}


async def _run_workflow(
    report_id: str,
    query: str,
    organization_context: str | None = None,
    target_regulators: list[str] | None = None,
) -> None:
    """
    Background task that invokes the compiled LangGraph workflow.
    Stores the result in _reports keyed by report_id.
    """
    try:
        _reports[report_id] = {"status": "running", "report": None, "trace": []}

        # Build the initial state the workflow expects
        initial_state = {
            "query": query,
            "session_id": report_id,
            "organization_context": organization_context,
            "target_regulators": target_regulators or [],
            "iteration_count": 0,
            "max_iterations": 3,
            "agent_trace": [],
        }

        # Invoke the LangGraph workflow
        result = await workflow.ainvoke(initial_state)

        _reports[report_id] = {
            "status": "completed",
            "report": result.get("final_report", {}),
            "trace": result.get("agent_trace", []),
        }

    except Exception as e:
        _reports[report_id] = {
            "status": "failed",
            "error": str(e),
            "report": None,
            "trace": [],
        }


@router.post(
    "/business",
    response_model=AnalysisInitiatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate multi-agent regulatory analysis for a business model",
)
async def analyze_business(
    request: BusinessAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: OptionalUser,
) -> AnalysisInitiatedResponse:
    report_id = str(uuid.uuid4())

    background_tasks.add_task(
        _run_workflow,
        report_id=report_id,
        query=request.business_description,
        organization_context=str(request.organization_context) if request.organization_context else None,
        target_regulators=request.target_regulators,
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
) -> AnalysisInitiatedResponse:
    """
    Compares the business description against ingested regulations
    and identifies missing controls, gaps, and obligations not yet met.
    """
    report_id = str(uuid.uuid4())

    # Build a gap-focused query so the workflow knows what to look for
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
        target_regulators=request.target_regulators,
    )

    return AnalysisInitiatedResponse(
        report_id=uuid.UUID(report_id),
        workflow_status="pending",
        message="Gap analysis initiated. Poll /analyze/report/{report_id} for results.",
    )


@router.get(
    "/report/{report_id}",
    summary="Retrieve a completed compliance analysis report",
)
async def get_report(
    report_id: str,
) -> dict:
    if report_id not in _reports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )
    return _reports[report_id]


@router.get(
    "/report/{report_id}/stream",
    summary="Stream agent workflow progress as server-sent events",
)
async def stream_report(
    report_id: str,
) -> StreamingResponse:
    """
    Streams real-time agent progress back to the client using
    Server-Sent Events. The client stays connected and receives
    an update each time an agent completes its step.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        import asyncio
        import json

        seen_steps: set[int] = set()
        max_polls = 120  # 2 minute timeout

        for _ in range(max_polls):
            report = _reports.get(report_id)

            if report:
                # Stream any new agent trace steps
                for i, step in enumerate(report.get("trace", [])):
                    if i not in seen_steps:
                        seen_steps.add(i)
                        yield f"data: {json.dumps(step)}\n\n"

                # If workflow is done, send final event and close
                if report["status"] in ("completed", "failed"):
                    yield f"data: {json.dumps({'event': 'done', 'status': report['status']})}\n\n"
                    break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )