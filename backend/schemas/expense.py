"""Pydantic schemas for Axyrel expenses."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class ExpenseBase(BaseModel):
    category: str
    description: str | None = None
    amount: Decimal
    expense_date: date
    payment_method: str | None = None
    vendor: str | None = None
    reference: str | None = None
    notes: str | None = None
    status: str = "Active"

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("category must not be empty")
        return value

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("amount must be non-negative")
        return value


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    category: str | None = None
    description: str | None = None
    amount: Decimal | None = None
    expense_date: date | None = None
    payment_method: str | None = None
    vendor: str | None = None
    reference: str | None = None
    notes: str | None = None
    status: str | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("amount must be non-negative")
        return value


class ExpenseRead(ExpenseBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
