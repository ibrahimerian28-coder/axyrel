"""FastAPI dependencies for authenticated tenant-scoped API endpoints."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.core.authentication import CurrentUser
from backend.core.authorization import Permission, require_permission
from backend.core.database import get_db
from backend.core.tenant import set_company_context


DBSession = Annotated[Session, Depends(get_db)]


def get_company_id(current_user: CurrentUser) -> UUID:
    """Resolve tenant context exclusively from the authenticated user."""
    set_company_context(current_user.company_id)
    return current_user.company_id


def require_api_permission(permission: Permission):
    return require_permission(permission)


CompanyID = Annotated[UUID, Depends(get_company_id)]
