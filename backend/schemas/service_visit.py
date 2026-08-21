"""Pydantic schemas for the Axyrel Service Visit domain."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class ServiceVisitBase(BaseModel):
    work_order_id: UUID
    schedule_id: UUID | None = None
    customer_id: UUID
    asset_id: UUID | None = None
    technician_id: UUID | None = None
    status: str = "Planned"
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_actual_time_range(self):
        if self.actual_start_at and self.actual_end_at and self.actual_end_at < self.actual_start_at:
            raise ValueError("actual_end_at must be later than or equal to actual_start_at")
        return self


class ServiceVisitCreate(ServiceVisitBase):
    pass


class ServiceVisitUpdate(BaseModel):
    work_order_id: UUID | None = None
    schedule_id: UUID | None = None
    customer_id: UUID | None = None
    asset_id: UUID | None = None
    technician_id: UUID | None = None
    status: str | None = None
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_actual_time_range(self):
        if self.actual_start_at and self.actual_end_at and self.actual_end_at < self.actual_start_at:
            raise ValueError("actual_end_at must be later than or equal to actual_start_at")
        return self


class ServiceVisitRead(ServiceVisitBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
