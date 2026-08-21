"""Tenant-scoped expense ORM model for the Axyrel finance domain."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class Expense(Base):
    """A company-owned expense record ready for later profitability reporting."""

    __tablename__ = "expenses"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payment_method: Mapped[str | None] = mapped_column(String(50))
    vendor: Mapped[str | None] = mapped_column(String(200))
    reference: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

