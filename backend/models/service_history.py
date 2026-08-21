"""Service History ORM model for the Axyrel field-service domain."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class ServiceHistory(Base):
    """Historical record of a completed or recorded service activity."""

    __tablename__ = "service_history"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    asset_id: Mapped[UUID | None] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    service_visit_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("service_visits.id"), nullable=True, index=True
    )
    work_order_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("work_orders.id"), nullable=True, index=True
    )
    service_type: Mapped[str] = mapped_column(String(100), nullable=False)
    service_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    technician_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="Active", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
