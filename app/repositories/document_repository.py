from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database_models import DocumentRecord


class DocumentRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def exists_by_hash(self, file_hash: str) -> bool:
        result = await self._session.execute(
            select(DocumentRecord).where(DocumentRecord.file_hash == file_hash)
        )
        return result.scalar_one_or_none() is not None

    async def save(self, data: dict) -> DocumentRecord:
        record = DocumentRecord(**data)
        self._session.add(record)
        await self._session.flush()  # get the ID without closing session
        return record

    async def get_all(self) -> list[DocumentRecord]:
        result = await self._session.execute(select(DocumentRecord))
        return list(result.scalars().all())
    
    async def get_by_id(self, doc_id: int) -> DocumentRecord | None:
        result = await self._session.execute(
            select(DocumentRecord).where(DocumentRecord.id == doc_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, doc_id: int) -> None:
        record = await self.get_by_id(doc_id)
        if record:
            await self._session.delete(record)