"""Pydantic schemas for the PostgreSQL inventory model."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class InventoryItemBase(BaseModel):
    item_name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(default=0, ge=0)
    min_limit: int = Field(default=0, ge=0)
    cost_price: Decimal = Field(default=Decimal("0"), ge=0)
    ideal_stock: int = Field(default=0, ge=0)
    status: str = "Active"


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    item_name: str | None = Field(default=None, min_length=1, max_length=200)
    quantity: int | None = Field(default=None, ge=0)
    min_limit: int | None = Field(default=None, ge=0)
    cost_price: Decimal | None = Field(default=None, ge=0)
    ideal_stock: int | None = Field(default=None, ge=0)
    status: str | None = None


class InventoryItemRead(InventoryItemBase):
    id: UUID
    company_id: UUID
    model_config = ConfigDict(from_attributes=True)
