import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import OptionalUser
from app.models.requests import BusinessAnalysisRequest
from app.models.responses import AnalysisInitiatedResponse, ComplianceReportResponse

router = APIRouter(prefix="/analyze", tags=["analysis"])

async def _run_workflow(
        report_id: uuid.UUID,
        request: BusinessAnalysisRequest,
) -> None:
    """
    Backgrounf task that triggers the LanGraph multi-agent workflow.
    Actual wokflow goes here once the graph layer is ready."""
    print(f"Workflow started for report {report_id}")
    print(f"Business: {request.business_description[:100]}...")

    # graph.workflow.run_compliance_workflow() to be called here later

@router.post(
    "/business",
    response_model=AnalysisInitiatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initialize multi-agent regulatory analysis for a business model"
)

async def analyze_business(
    request: BusinessAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: OptionalUser,
) -> AnalysisInitiatedResponse:
    report_id = uuid.uuid4()

    # Trigger multi-agent workflow as a background task
    background_tasks.add_task(_run_workflow, report_id, request)

    return AnalysisInitiatedResponse(
        report_id=report_id,
        workflow_status="pending",
        message="Analysis initiated. Pull /analyze/report/{report_id} for results."
    )

@router.get(
    "/report/{report_id}",
    response_model=ComplianceReportResponse,
    summary="Retrieve a completed compliance analysis report",
)

async def get_report(
    report_id: uuid.UUID
) -> ComplianceReportResponse:
    # DB query goes here
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Report not found."
    )

@router.get(
    "/report/{report_id}/stream",
    summary="Stream agent workflow progress as server-sent events",
)
async def stream_report(
    report_id: uuid.UUID,
) -> StreamingResponse:
    """
    Streams real-time agent progress back to the client using
    Server-Sent Events (SSE). The client stays connected and receives
    updates as each agent completes its step
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        import asyncio
        import json

        # Placeholder events - real agent steps will be streamed here
        placeholder_steps = [
            {"agent": "orchestrator", "status": "running", "step": 1},
            {"agent": "jurisdiction_mapper", "status": "running", "step": 2},
            {"agent": "researcher", "status": "running", "step": 3},
            {"agent": "compliance_auditor", "status": "running", "step": 4},
            {"agent": "citation_verifier", "status": "running", "step": 5},
        ]

        for step in placeholder_steps:
            yield f"data: {json.dumps(step)}\n\n"
            await asyncio.sleep(1)

        yield f"data: {json.dumps({'event': 'done', 'status': 'completed'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

