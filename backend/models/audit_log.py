"""Immutable tenant-scoped activity/audit log model for Axyrel."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class AuditLog(Base):
    """Records an auditable action performed within a company."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_company_created_at", "company_id", "created_at"),
        Index("ix_audit_logs_company_actor", "company_id", "actor_user_id"),
        Index("ix_audit_logs_company_entity", "company_id", "entity_type", "entity_id"),
        Index("ix_audit_logs_company_action", "company_id", "action"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    entity_id: Mapped[UUID | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
