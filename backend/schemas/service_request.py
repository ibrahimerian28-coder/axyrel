"""Pydantic schemas for the Axyrel Service Request domain."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ServiceRequestBase(BaseModel):
    customer_id: UUID
    asset_id: UUID | None = None
    title: str
    description: str | None = None
    priority: str = "Normal"
    status: str = "Open"
    source: str | None = None
    notes: str | None = None


class ServiceRequestCreate(ServiceRequestBase):
    pass


class ServiceRequestUpdate(BaseModel):
    customer_id: UUID | None = None
    asset_id: UUID | None = None
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    source: str | None = None
    notes: str | None = None


class ServiceRequestRead(ServiceRequestBase):
    id: UUID
    company_id: UUID
    display_id: int | None = None
    requested_at: datetime
    model_config = ConfigDict(from_attributes=True)
