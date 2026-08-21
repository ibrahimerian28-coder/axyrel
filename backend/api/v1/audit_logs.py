"""Task 44 audit-log endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from backend.services.audit_log import AuditLogService
from backend.schemas.audit_log import AuditLogCreate, AuditLogRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission
router=APIRouter(prefix="/audit-logs", tags=["audit"])
service=AuditLogService()
@router.get("", response_model=list[AuditLogRead], dependencies=[Depends(require_permission(Permission.AUDIT_READ))])
def list_audit_logs(db: DBSession, company_id: CompanyID):
    return service.list_audit_logs(db, company_id)
@router.get("/{audit_log_id}", response_model=AuditLogRead, dependencies=[Depends(require_permission(Permission.AUDIT_READ))])
def get_audit_log(audit_log_id: UUID, db: DBSession, company_id: CompanyID):
    r=service.get_audit_log(db, company_id, audit_log_id)
    if r is None: raise HTTPException(404,"audit log not found")
    return r
@router.post("", response_model=AuditLogRead, status_code=201, dependencies=[Depends(require_permission(Permission.AUDIT_READ))])
def create_audit_log(payload: AuditLogCreate, db: DBSession, company_id: CompanyID):
    r=service.create_audit_log(db, company_id, payload.model_dump(exclude_unset=True)); db.commit(); db.refresh(r); return r
