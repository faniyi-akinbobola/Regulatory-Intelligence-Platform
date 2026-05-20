from uuid import UUID
from pydantic import BaseModel


class AnalysisInitiatedResponse(BaseModel):
    report_id: UUID
    workflow_status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, str]
