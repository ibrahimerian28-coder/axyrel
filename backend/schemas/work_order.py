"""Pydantic schemas for the Axyrel Work Order domain."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkOrderBase(BaseModel):
    customer_id: UUID
    asset_id: UUID | None = None
    service_request_id: UUID | None = None
    title: str
    description: str | None = None
    priority: str = "Normal"
    status: str = "Open"
    assigned_technician_id: UUID | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    notes: str | None = None


class WorkOrderCreate(WorkOrderBase):
    pass


class WorkOrderUpdate(BaseModel):
    customer_id: UUID | None = None
    asset_id: UUID | None = None
    service_request_id: UUID | None = None
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    assigned_technician_id: UUID | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    notes: str | None = None


class WorkOrderRead(WorkOrderBase):
    id: UUID
    company_id: UUID
    display_id: int | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
