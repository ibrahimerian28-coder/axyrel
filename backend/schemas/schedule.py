"""Pydantic schemas for the Axyrel Scheduling domain."""

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from backend.core.event_time import normalize_event_time


class ScheduleBase(BaseModel):
    work_order_id: UUID
    technician_id: UUID | None = None
    start_at: datetime
    end_at: datetime
    status: str = "Scheduled"
    notes: str | None = None

    @field_validator("start_at", "end_at")
    @classmethod
    def normalize_times(cls, value: datetime) -> datetime:
        return normalize_event_time(value)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be later than start_at")
        return self


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    work_order_id: UUID | None = None
    technician_id: UUID | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    status: str | None = None
    notes: str | None = None

    @field_validator("start_at", "end_at")
    @classmethod
    def normalize_times(cls, value: datetime | None) -> datetime | None:
        return normalize_event_time(value) if value is not None else None


class ScheduleRead(ScheduleBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_validator("start_at", "end_at")
    @classmethod
    def normalize_times(cls, value: datetime) -> datetime:
        # Database output is an instant, including naive UTC from SQLite tests.
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
