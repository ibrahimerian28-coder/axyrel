"""Task 44 API endpoints for service history."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.service_history import ServiceHistoryService
from backend.schemas.service_history import ServiceHistoryCreate, ServiceHistoryUpdate, ServiceHistoryRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission

router = APIRouter(prefix="/service-history", tags=["service history"])
service = ServiceHistoryService()

@router.get("", response_model=list[ServiceHistoryRead], dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def list_records(db: DBSession, company_id: CompanyID, ):
    kwargs = {}
    return service.list_history(db, company_id, **kwargs)

@router.get("/{history_id}", response_model=ServiceHistoryRead, dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def get_record(history_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.get_history(db, company_id, history_id)
    if record is None:
        raise HTTPException(status_code=404, detail="service_history record not found")
    return record

@router.post("", response_model=ServiceHistoryRead, status_code=201, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def create_record(payload: ServiceHistoryCreate, db: DBSession, company_id: CompanyID):
    record = service.create_history(db, company_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(record)
    return record

@router.patch("/{history_id}", response_model=ServiceHistoryRead, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def update_record(history_id: UUID, payload: ServiceHistoryUpdate, db: DBSession, company_id: CompanyID):
    record = service.update_history(db, company_id, history_id, payload.model_dump(exclude_unset=True))
    if record is None:
        raise HTTPException(status_code=404, detail="service_history record not found")
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{history_id}", status_code=204, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def delete_record(history_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.delete_history(db, company_id, history_id)
    if record is None:
        raise HTTPException(status_code=404, detail="service_history record not found")
    db.commit()
    return None
