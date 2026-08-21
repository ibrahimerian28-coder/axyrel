"""Scheduling model for the Axyrel service domain."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class Schedule(Base):
    """A scheduled time slot for a work order."""

    __tablename__ = "schedules"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    work_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("work_orders.id"), nullable=False, index=True
    )
    technician_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Scheduled", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
