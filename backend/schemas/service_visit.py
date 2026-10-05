"""Pydantic schemas for the Axyrel Service Visit domain."""

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from backend.core.event_time import normalize_event_time


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

    @field_validator("actual_start_at", "actual_end_at")
    @classmethod
    def normalize_times(cls, value: datetime | None) -> datetime | None:
        return normalize_event_time(value) if value is not None else None

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

    @field_validator("actual_start_at", "actual_end_at")
    @classmethod
    def normalize_times(cls, value: datetime | None) -> datetime | None:
        return normalize_event_time(value) if value is not None else None

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

    @field_validator("actual_start_at", "actual_end_at")
    @classmethod
    def normalize_times(cls, value: datetime | None) -> datetime | None:
        return value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value.astimezone(timezone.utc) if value is not None else None
