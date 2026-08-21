"""Task 44 API endpoints for service visits."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.service_visit import ServiceVisitService
from backend.schemas.service_visit import ServiceVisitCreate, ServiceVisitUpdate, ServiceVisitRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission

router = APIRouter(prefix="/service-visits", tags=["service visits"])
service = ServiceVisitService()

@router.get("", response_model=list[ServiceVisitRead], dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def list_records(db: DBSession, company_id: CompanyID, ):
    kwargs = {}
    return service.list_visits(db, company_id, **kwargs)

@router.get("/{visit_id}", response_model=ServiceVisitRead, dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def get_record(visit_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.get_visit(db, company_id, visit_id)
    if record is None:
        raise HTTPException(status_code=404, detail="service_visits record not found")
    return record

@router.post("", response_model=ServiceVisitRead, status_code=201, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def create_record(payload: ServiceVisitCreate, db: DBSession, company_id: CompanyID):
    record = service.create_visit(db, company_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(record)
    return record

@router.patch("/{visit_id}", response_model=ServiceVisitRead, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def update_record(visit_id: UUID, payload: ServiceVisitUpdate, db: DBSession, company_id: CompanyID):
    record = service.update_visit(db, company_id, visit_id, payload.model_dump(exclude_unset=True))
    if record is None:
        raise HTTPException(status_code=404, detail="service_visits record not found")
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{visit_id}", status_code=204, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def delete_record(visit_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.delete_visit(db, company_id, visit_id)
    if record is None:
        raise HTTPException(status_code=404, detail="service_visits record not found")
    db.commit()
    return None
