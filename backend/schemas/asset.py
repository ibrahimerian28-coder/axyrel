"""Pydantic schemas for the Axyrel Asset domain."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AssetBase(BaseModel):
    customer_id: UUID
    asset_type: str
    serial_number: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    installation_date: date | None = None
    warranty_start: date | None = None
    warranty_end: date | None = None
    status: str = "Active"
    notes: str | None = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    customer_id: UUID | None = None
    asset_type: str | None = None
    serial_number: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    installation_date: date | None = None
    warranty_start: date | None = None
    warranty_end: date | None = None
    status: str | None = None
    notes: str | None = None


class AssetRead(AssetBase):
    id: UUID
    company_id: UUID
    display_id: int | None = None
    model_config = ConfigDict(from_attributes=True)
