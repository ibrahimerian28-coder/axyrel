"""Pydantic schemas for the Axyrel Scheduling domain."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class ScheduleBase(BaseModel):
    work_order_id: UUID
    technician_id: UUID | None = None
    start_at: datetime
    end_at: datetime
    status: str = "Scheduled"
    notes: str | None = None

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


class ScheduleRead(ScheduleBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
