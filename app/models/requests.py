from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BusinessAnalysisRequest(BaseModel):
    business_description: str = Field(
        min_length=20,
        max_length=5000,
        description="Describe the business model or product to analyze for regulatory compliance.",
    )
    business_sector: str | None = Field(
        default=None,
        description="e.g. fintech, payments, lending, investment, insurance",
    )
    target_regulators: list[str] | None = Field(
        default=None,
        description="Optionally restrict analysis to specific regulators e.g. CBN, SEC",
    )
    organization_context: dict[str, Any] | None = Field(
        default=None,
        description="Additional org context: existing licenses, jurisdiction, etc.",
    )


class ComplianceGapRequest(BaseModel):
    business_description: str = Field(min_length=20, max_length=5000)
    target_regulators: list[str] | None = None


class AuditTraceQueryRequest(BaseModel):
    report_id: UUID
    include_agent_details: bool = True