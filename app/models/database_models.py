from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.postgres import Base
import uuid


class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    regulator: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_pages: Mapped[int] = mapped_column(Integer, nullable=False)
    chunks_ingested: Mapped[int] = mapped_column(Integer, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditRecord(Base):
    __tablename__ = "audit_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(index=True)
    query: Mapped[str] = mapped_column(Text)
    organization_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_regulators: Mapped[dict] = mapped_column(JSON)
    agent_trace: Mapped[list] = mapped_column(JSON)
    jurisdiction_result: Mapped[dict] = mapped_column(JSON)
    reasoning_result: Mapped[dict] = mapped_column(JSON)
    audit_result: Mapped[dict] = mapped_column(JSON)
    citation_result: Mapped[dict] = mapped_column(JSON)
    critic_result: Mapped[dict] = mapped_column(JSON)
    final_report: Mapped[dict] = mapped_column(JSON)
    overall_risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hallucination_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    grounding_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    iteration_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED")
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())