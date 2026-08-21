"""Service Contract ORM model for the Axyrel contract domain."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class ServiceContract(Base):
    """Tenant-scoped service contract linked to a customer."""

    __tablename__ = "service_contracts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    contract_number: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="Draft", nullable=False, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    contract_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    billing_frequency: Mapped[str] = mapped_column(
        String(30), default="Monthly", nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
