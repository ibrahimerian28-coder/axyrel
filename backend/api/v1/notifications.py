"""Task 44 notification endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from backend.services.notification import NotificationService
from backend.schemas.notification import NotificationCreate, NotificationUpdate, NotificationRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission
router=APIRouter(prefix="/notifications", tags=["notifications"])
service=NotificationService()
@router.get("", response_model=list[NotificationRead], dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def list_notifications(db: DBSession, company_id: CompanyID):
    return service.list_notifications(db, company_id)
@router.get("/{notification_id}", response_model=NotificationRead, dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def get_notification(notification_id: UUID, db: DBSession, company_id: CompanyID):
    r=service.get_notification(db, company_id, notification_id)
    if r is None: raise HTTPException(404,"notification not found")
    return r
@router.post("", response_model=NotificationRead, status_code=201, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def create_notification(payload: NotificationCreate, db: DBSession, company_id: CompanyID):
    r=service.create_notification(db, company_id, payload.model_dump(exclude_unset=True)); db.commit(); db.refresh(r); return r
@router.patch("/{notification_id}", response_model=NotificationRead, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def update_notification(notification_id: UUID, payload: NotificationUpdate, db: DBSession, company_id: CompanyID):
    r=service.update_notification(db, company_id, notification_id, payload.model_dump(exclude_unset=True))
    if r is None: raise HTTPException(404,"notification not found")
    db.commit(); db.refresh(r); return r
@router.post("/{notification_id}/read", response_model=NotificationRead, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def mark_read(notification_id: UUID, db: DBSession, company_id: CompanyID):
    r=service.mark_read(db, company_id, notification_id)
    if r is None: raise HTTPException(404,"notification not found")
    db.commit(); db.refresh(r); return r
