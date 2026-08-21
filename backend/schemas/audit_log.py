"""Pydantic schemas for activity/audit log operations."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogCreate(BaseModel):
    actor_user_id: UUID | None = None
    action: str = Field(min_length=1, max_length=80)
    entity_type: str | None = Field(default=None, max_length=80)
    entity_id: UUID | None = None
    description: str | None = None
    event_metadata: dict | None = None
    ip_address: str | None = Field(default=None, max_length=64)
    user_agent: str | None = Field(default=None, max_length=500)


class AuditLogRead(AuditLogCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    created_at: datetime
