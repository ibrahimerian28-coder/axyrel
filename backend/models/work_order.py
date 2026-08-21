"""Work Order ORM model for the Axyrel service domain."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class WorkOrder(Base):
    """An executable service job created from a service request or directly."""

    __tablename__ = "work_orders"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assets.id"), nullable=True, index=True
    )
    service_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("service_requests.id"), nullable=True, index=True
    )
    display_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(30), default="Normal", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Open", nullable=False)
    assigned_technician_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    scheduled_start: Mapped[datetime | None] = mapped_column(DateTime)
    scheduled_end: Mapped[datetime | None] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
