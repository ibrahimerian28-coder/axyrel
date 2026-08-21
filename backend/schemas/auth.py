"""Authentication API schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: UUID
    company_id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login_at: datetime | None = None
    permissions: list[str] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
