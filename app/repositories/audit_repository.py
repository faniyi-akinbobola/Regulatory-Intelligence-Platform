import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database_models import AuditRecord


class AuditRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, data: dict) -> AuditRecord:
        """Persist a new audit record. Returns the saved record with its generated ID."""
        record = AuditRecord(**data)
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_id(self, audit_id: uuid.UUID) -> AuditRecord | None:
        result = await self._session.execute(
            select(AuditRecord).where(AuditRecord.id == audit_id)
        )
        return result.scalar_one_or_none()

    async def list_by_session(
        self,
        session_id: uuid.UUID,
        limit: int = 20,
    ) -> list[AuditRecord]:
        result = await self._session.execute(
            select(AuditRecord)
            .where(AuditRecord.session_id == session_id)
            .order_by(AuditRecord.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
