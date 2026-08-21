"""Pydantic schemas for Axyrel invoices."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator

class InvoiceBase(BaseModel):
    customer_id: UUID
    work_order_id: UUID | None = None
    invoice_number: str
    status: str = "Draft"
    issue_date: date
    due_date: date | None = None
    subtotal: Decimal = Decimal("0.00")
    discount: Decimal = Decimal("0.00")
    tax: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")
    paid_amount: Decimal = Decimal("0.00")
    notes: str | None = None

    @field_validator("invoice_number")
    @classmethod
    def validate_invoice_number(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("invoice_number must not be empty")
        return value

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    customer_id: UUID | None = None
    work_order_id: UUID | None = None
    invoice_number: str | None = None
    status: str | None = None
    issue_date: date | None = None
    due_date: date | None = None
    subtotal: Decimal | None = None
    discount: Decimal | None = None
    tax: Decimal | None = None
    total: Decimal | None = None
    paid_amount: Decimal | None = None
    notes: str | None = None

class InvoiceRead(InvoiceBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
