import time
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.workflow import workflow
from app.services.audit_service import AuditService
from app.utils.citations import build_citations_from_chunks
from app.utils import cost_tracker

logger = logging.getLogger(__name__)


class ComplianceService:

    def __init__(self, db: AsyncSession):
        self._db = db
        self._audit_service = AuditService(db)

    async def analyze(
        self,
        query: str,
        session_id: uuid.UUID,
        organization_context: str | None = None,
    ) -> dict:
        initial_state = {
            "query": query,
            "session_id": str(session_id),
            "organization_context": organization_context,
            "iteration_count": 0,
            "max_iterations": 2,
            "agent_trace": [],
        }

        start_ms = int(time.time() * 1000)
        logger.info("[COMPLIANCE] Starting workflow for session %s", session_id)

        cost_tracker.reset()
        final_state = await workflow.ainvoke(initial_state)
        usage = cost_tracker.get()
        duration_ms = int(time.time() * 1000) - start_ms

        logger.info(
            "[COMPLIANCE] Workflow complete in %dms, iterations=%d, tokens=%d, cost=$%.6f",
            duration_ms,
            final_state.get("iteration_count", 0),
            usage.total_tokens if usage else 0,
            usage.cost_usd if usage else 0.0,
        )

        reasoning_result = final_state.get("reasoning_result") or {}
        audit_result = final_state.get("audit_result") or {}
        citation_result = final_state.get("citation_result") or {}
        chunks = final_state.get("retrieved_chunks") or []
        citations = build_citations_from_chunks(chunks)

        # Derive applicable regulator list from jurisdiction output
        jurisdiction_result = final_state.get("jurisdiction_result") or {}
        applicable_regulators = [
            r.get("regulator")
            for r in jurisdiction_result.get("applicable_regulators", [])
            if r.get("regulator")
        ]
        if not applicable_regulators:
            applicable_regulators = final_state.get("target_regulators") or []

        final_report = {
            "query": query,
            "executive_summary": reasoning_result.get("reasoning_summary", ""),
            "applicable_regulators": applicable_regulators,
            "obligations": reasoning_result.get("obligations", []),
            "prohibitions": reasoning_result.get("prohibitions", []),
            "permissions": reasoning_result.get("permissions", []),
            "conflicts": reasoning_result.get("conflicts", []),
            "compliance_gaps": audit_result.get("compliance_gaps", []),
            "compliance_checklist": audit_result.get("compliance_checklist", []),
            "licensing_requirements": audit_result.get("licensing_requirements", []),
            "recommendations": audit_result.get("recommendations", []),
            "risk_score": audit_result.get("risk_score"),
            "risk_level": audit_result.get("risk_level"),
            "citations": citations,
        }

        final_state["final_report"] = final_report

        record = await self._audit_service.create_record(
            workflow_state=final_state,
            session_id=session_id,
            duration_ms=duration_ms,
        )

        return {
            "audit_id": str(record.id),
            "session_id": str(session_id),
            "query": query,
            "final_report": final_report,
            "overall_risk_level": audit_result.get("risk_level"),
            "hallucination_risk": citation_result.get("hallucination_risk"),
            "grounding_score": citation_result.get("overall_grounding_score"),
            "agent_trace": final_state.get("agent_trace", []),
            "iteration_count": final_state.get("iteration_count", 0),
            "duration_ms": duration_ms,
            "llm_metrics": {
                "llm_calls": usage.llm_calls if usage else 0,
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
                "cost_usd": round(usage.cost_usd, 6) if usage else 0.0,
                "model": "gpt-4o-mini",
            },
        }

    async def analyze_gap(
        self,
        business_description: str,
        session_id: uuid.UUID,
        target_regulators: list[str] | None = None,
    ) -> dict:
        """
        Builds a gap-focused query and runs the full compliance workflow.
        All gap analysis logic lives here, not in the route.
        """
        gap_query = (
            f"Perform a compliance gap analysis for the following business: "
            f"{business_description}. "
            f"Identify missing controls, unmet obligations, and regulatory gaps."
        )

        if target_regulators:
            gap_query += f" Focus specifically on: {', '.join(target_regulators)}."

        return await self.analyze(
            query=gap_query,
            session_id=session_id,
        )