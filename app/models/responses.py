from uuid import UUID
from pydantic import BaseModel


class AnalysisInitiatedResponse(BaseModel):
    report_id: UUID
    workflow_status: str
    message: str


class LLMMetrics(BaseModel):
    """Token usage and cost for a single workflow run."""
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    model: str = "gpt-4o-mini"


class ReportStatusResponse(BaseModel):
    """Response for GET /analyze/report/{id} — the poll endpoint."""
    report_id: str
    status: str  # running | completed | failed
    audit_id: str | None = None
    session_id: str | None = None
    report: dict | None = None
    error: str | None = None
    llm_metrics: LLMMetrics | None = None
    # Audit metadata surfaced from workflow state
    grounding_score: float | None = None
    hallucination_risk: str | None = None
    iteration_count: int | None = None
    agent_trace: list[dict] | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, str]
