import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.audit_repository import AuditRepository
from app.models.database_models import AuditRecord

logger = logging.getLogger(__name__)


class AuditService:

    def __init__(self, session: AsyncSession):
        self._repo = AuditRepository(session)

    async def create_record(
        self,
        workflow_state: dict,
        session_id: uuid.UUID,
        duration_ms: int | None = None,
    ) -> AuditRecord:
        """
        Builds and persists an AuditRecord from a completed LangGraph workflow state.
        Extracts grounding score and risk level from nested agent results.
        """
        citation_result = workflow_state.get("citation_result") or {}
        audit_result = workflow_state.get("audit_result") or {}
        critic_result = workflow_state.get("critic_result") or {}

        grounding_score_raw = citation_result.get("overall_grounding_score", None)
        try:
            grounding_score = int(grounding_score_raw) if grounding_score_raw is not None else None
        except (TypeError, ValueError):
            grounding_score = None

        data = {
            "session_id": session_id,
            "query": workflow_state.get("query", ""),
            "organization_context": workflow_state.get("organization_context"),
            "target_regulators": workflow_state.get("target_regulators") or [],
            "agent_trace": workflow_state.get("agent_trace") or [],
            "jurisdiction_result": workflow_state.get("jurisdiction_result") or {},
            "reasoning_result": workflow_state.get("reasoning_result") or {},
            "audit_result": audit_result,
            "citation_result": citation_result,
            "critic_result": critic_result,
            "final_report": workflow_state.get("final_report") or {},
            "overall_risk_level": audit_result.get("risk_level"),
            "hallucination_risk": citation_result.get("hallucination_risk"),
            "grounding_score": grounding_score,
            "iteration_count": workflow_state.get("iteration_count", 0),
            "status": "COMPLETED",
            "duration_ms": duration_ms,
        }

        record = await self._repo.save(data)
        logger.info("[AUDIT] Saved audit record %s for session %s", record.id, session_id)
        return record

    async def get_record(self, audit_id: str) -> AuditRecord | None:
        try:
            uid = uuid.UUID(audit_id)
        except ValueError:
            return None
        return await self._repo.get_by_id(uid)

    async def list_session_records(
        self,
        session_id: str,
        limit: int = 20,
    ) -> list[AuditRecord]:
        try:
            uid = uuid.UUID(session_id)
        except ValueError:
            return []
        return await self._repo.list_by_session(uid, limit=limit)
