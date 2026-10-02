"""Minimal read-only directory for existing technician User identities."""
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from backend.api.dependencies import CompanyID, DBSession
from backend.core.authorization import Permission, require_permission
from backend.models.user import User

router = APIRouter(prefix="/technician-directory", tags=["technician directory"])


class TechnicianDirectoryEntry(BaseModel):
    id: UUID
    display_name: str


@router.get("", response_model=list[TechnicianDirectoryEntry],
            dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def list_technicians(db: DBSession, company_id: CompanyID):
    rows = db.execute(select(User.id, User.full_name).where(
        User.company_id == company_id, User.role == "technician", User.is_active.is_(True)
    ).order_by(User.full_name, User.id)).all()
    return [TechnicianDirectoryEntry(id=row.id, display_name=row.full_name) for row in rows]
