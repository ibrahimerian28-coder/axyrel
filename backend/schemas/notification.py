"""Pydantic schemas for tenant-scoped notifications."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    recipient_user_id: UUID | None = None
    notification_type: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1)
    priority: str = Field(default="normal", min_length=1, max_length=20)
    entity_type: str | None = Field(default=None, max_length=50)
    entity_id: UUID | None = None
    action_url: str | None = Field(default=None, max_length=500)
    expires_at: datetime | None = None


class NotificationUpdate(BaseModel):
    status: str | None = Field(default=None, min_length=1, max_length=20)
    read_at: datetime | None = None


class NotificationRead(NotificationCreate):
    id: UUID
    company_id: UUID
    status: str
    read_at: datetime | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
