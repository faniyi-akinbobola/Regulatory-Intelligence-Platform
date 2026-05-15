from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel


# Health
class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, str]

# Regulation Upload

class RegulationUploadResponse(BaseModel):
    document_id: UUID
    title: str
    regulator: str
    status: str
    message: str

class DocumentStatusResponse(BaseModel):
    document_id: UUID
    title: str
    regulator: str
    status: str
    total_chunks: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class DocumentListResponse(BaseModel):
    documents: list[DocumentStatusResponse]
    total: int


# Business Analysis /  Compliance Report

class CitationResponse(BaseModel):
    document_id: UUID
    document_title: str
    regulator: str
    section_number: str | None
    section_title: str | None
    page_number: int | None
    excerpt: str
    relevance_score: float | None = None

class ReasoningStepResponse(BaseModel):
    agent_name: str
    step_index: int
    summary: str
    citations_used: list[CitationResponse] = []
    duration_ms: int | None = None

class RiskItem(BaseModel):
    category: str
    description: str
    severity: str
    regulation_reference: str | None = None
    mitigation: str | None = None
    
class LicenseRequirement(BaseModel):
    license_name: str
    issuing_body: str
    description: str
    mandatory: bool
    citation: CitationResponse | None = None

class ComplianceObligation(BaseModel):
    obligation: str
    regulator: str
    deadline: str | None = None
    priority: str
    citation: CitationResponse | None = None

class ComplianceReportResponse(BaseModel):
    report_id: UUID
    workflow_status: str
    business_description: str
    applicable_regulators: list[str]
    risk_level: str | None
    risk_score: float | None
    required_licenses: list[LicenseRequirement]
    compliance_obligations: list[ComplianceObligation]
    regulatory_gaps: list[RiskItem]
    recommendations: list[dict[str, Any]]
    citations: list[CitationResponse]
    reasoning_trace: list[ReasoningStepResponse]
    created_at: datetime
    completed_at: datetime | None

class AnalysisInitiatedResponse(BaseModel):
    report_id: UUID
    workflow_status: str
    message: str


# Audit Trace
class AgentStepResponse(BaseModel):
    id: UUID
    agent_name: str
    step_index: int
    reasoning: str | None
    citations_used: list[CitationResponse]
    duration_ms: int | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

class AuditTraceResponse(BaseModel):
    report_id: UUID
    workflow_status: str
    total_steps: int
    agent_steps: list[AgentStepResponse]
    created_at: datetime
    completed_at: datetime | None
    




