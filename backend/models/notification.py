"""Tenant-scoped notification ORM model for Axyrel."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class Notification(Base):
    """A notification delivered to an optional user within a company."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_company_recipient_status", "company_id", "recipient_user_id", "status"),
        Index("ix_notifications_company_created_at", "company_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    recipient_user_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal", index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unread", index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[UUID | None] = mapped_column(nullable=True)
    action_url: Mapped[str | None] = mapped_column(String(500))
    read_at: Mapped[datetime | None] = mapped_column(DateTime)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
