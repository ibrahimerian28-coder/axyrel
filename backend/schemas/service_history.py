"""Pydantic schemas for the Axyrel Service History domain."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator


class ServiceHistoryBase(BaseModel):
    customer_id: UUID
    asset_id: UUID | None = None
    service_visit_id: UUID | None = None
    work_order_id: UUID | None = None
    service_type: str
    service_date: datetime
    summary: str
    technician_id: UUID | None = None
    notes: str | None = None
    status: str = "Active"

    @field_validator("service_type", "summary")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value: raise ValueError("value must not be empty")
        return value


class ServiceHistoryCreate(ServiceHistoryBase): pass


class ServiceHistoryUpdate(BaseModel):
    customer_id: UUID | None = None
    asset_id: UUID | None = None
    service_visit_id: UUID | None = None
    work_order_id: UUID | None = None
    service_type: str | None = None
    service_date: datetime | None = None
    summary: str | None = None
    technician_id: UUID | None = None
    notes: str | None = None
    status: str | None = None


class ServiceHistoryRead(ServiceHistoryBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
