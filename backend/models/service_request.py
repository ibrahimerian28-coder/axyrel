"""Service Request ORM model for the Axyrel service domain."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class ServiceRequest(Base):
    """A customer service request that may later become a work order."""

    __tablename__ = "service_requests"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assets.id"), nullable=True, index=True
    )
    display_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(30), default="Normal")
    status: Mapped[str] = mapped_column(String(30), default="Open")
    source: Mapped[str | None] = mapped_column(String(50))
    requested_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
