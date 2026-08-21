"""Pydantic schemas for the Axyrel Service Contract domain."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ServiceContractBase(BaseModel):
    customer_id: UUID
    contract_number: str = Field(min_length=1, max_length=50)
    status: str = "Draft"
    start_date: date
    end_date: date | None = None
    contract_value: Decimal = Field(default=Decimal("0"), ge=0)
    billing_frequency: str = "Monthly"
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ServiceContractCreate(ServiceContractBase):
    pass


class ServiceContractUpdate(BaseModel):
    customer_id: UUID | None = None
    contract_number: str | None = Field(default=None, min_length=1, max_length=50)
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    contract_value: Decimal | None = Field(default=None, ge=0)
    billing_frequency: str | None = None
    notes: str | None = None


class ServiceContractRead(ServiceContractBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
