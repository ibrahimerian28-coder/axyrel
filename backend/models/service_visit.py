"""Service Visit ORM model for the Axyrel field-service domain."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class ServiceVisit(Base):
    """An actual field visit performed for a work order."""

    __tablename__ = "service_visits"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    work_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("work_orders.id"), nullable=False, index=True
    )
    schedule_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("schedules.id"), nullable=True, index=True
    )
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assets.id"), nullable=True, index=True
    )
    technician_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="Planned", nullable=False, index=True)
    actual_start_at: Mapped[datetime | None] = mapped_column(DateTime)
    actual_end_at: Mapped[datetime | None] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
