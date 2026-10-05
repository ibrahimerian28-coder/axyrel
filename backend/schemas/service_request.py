"""Pydantic schemas for the Axyrel Service Request domain."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

REQUEST_PRIORITIES = ("Low", "Normal", "High", "Urgent")
REQUEST_STATUSES = ("Open", "In Progress", "Resolved", "Closed", "Cancelled")


def request_choice(value, field):
    choices = REQUEST_PRIORITIES if field == "priority" else REQUEST_STATUSES
    if value not in choices:
        raise ValueError(f'{field.capitalize()} must be one of: {", ".join(choices)}.')
    return value


def request_title(value):
    if value is None or not value.strip():
        raise ValueError("Title is required.")
    return value


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
    @field_validator("priority", "status")
    @classmethod
    def canonical_choice(cls, value, info):
        return request_choice(value, info.field_name)

    @field_validator("title")
    @classmethod
    def required_title(cls, value):
        return request_title(value)


class ServiceRequestUpdate(BaseModel):
    customer_id: UUID | None = None
    asset_id: UUID | None = None
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    source: str | None = None
    notes: str | None = None

    # Validators run only for fields actually supplied; omitted legacy values
    # remain unchanged and never invalidate an unrelated PATCH.
    @field_validator("priority", "status")
    @classmethod
    def canonical_choice(cls, value, info):
        return request_choice(value, info.field_name)

    @field_validator("title")
    @classmethod
    def required_title(cls, value):
        return request_title(value)

    @field_validator("customer_id")
    @classmethod
    def required_customer(cls, value):
        if value is None:
            raise ValueError("Customer is required.")
        return value


class ServiceRequestRead(ServiceRequestBase):
    id: UUID
    company_id: UUID
    display_id: int | None = None
    requested_at: datetime
    model_config = ConfigDict(from_attributes=True)
