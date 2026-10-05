"""Pydantic schemas for the Axyrel Asset domain."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AssetBase(BaseModel):
    customer_id: UUID
    asset_type: str
    serial_number: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    country: str | None = Field(default=None, max_length=2)
    state: str | None = Field(default=None, max_length=150)
    area: str | None = Field(default=None, max_length=150)
    address: str | None = Field(default=None, max_length=500)
    location_url: str | None = Field(default=None, max_length=1000)
    maintenance_cycle: int | None = Field(default=None, ge=1, le=1200, strict=True)
    warranty_years: int | None = Field(default=None, ge=0, le=100, strict=True)
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
    country: str | None = Field(default=None, max_length=2)
    state: str | None = Field(default=None, max_length=150)
    area: str | None = Field(default=None, max_length=150)
    address: str | None = Field(default=None, max_length=500)
    location_url: str | None = Field(default=None, max_length=1000)
    maintenance_cycle: int | None = Field(default=None, ge=1, le=1200, strict=True)
    warranty_years: int | None = Field(default=None, ge=0, le=100, strict=True)
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
