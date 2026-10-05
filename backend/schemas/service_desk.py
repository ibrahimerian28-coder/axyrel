"""Operational commands reuse existing domain contracts and time validation."""
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field
from backend.schemas.service_request import ServiceRequestCreate


class Appointment(BaseModel):
    technician_id: UUID
    start_at: datetime
    end_at: datetime
    notes: str | None = None


class QuickService(ServiceRequestCreate):
    command_id: UUID
    title: str = Field(min_length=1, max_length=200)
    appointment: Appointment | None = None


class VisitOutcome(BaseModel):
    outcome: Literal["complete-job", "follow-up", "unavailable", "cancel-visit"]
    notes: str = Field(min_length=1)
    appointment: Appointment | None = None


class Reason(BaseModel):
    reason: str = Field(min_length=1)
