"""Invoice ORM model for the Axyrel billing domain."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.base import Base

class Invoice(Base):
    """Tenant-scoped invoice linked to a customer and optionally a work order."""
    __tablename__ = "invoices"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    work_order_id: Mapped[UUID | None] = mapped_column(ForeignKey("work_orders.id"), nullable=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Draft", nullable=False, index=True)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
