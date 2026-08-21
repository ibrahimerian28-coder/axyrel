"""Task 44 API endpoints for service requests."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.service_request import ServiceRequestService
from backend.schemas.service_request import ServiceRequestCreate, ServiceRequestUpdate, ServiceRequestRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission

router = APIRouter(prefix="/service-requests", tags=["service requests"])
service = ServiceRequestService()

@router.get("", response_model=list[ServiceRequestRead], dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def list_records(db: DBSession, company_id: CompanyID, customer_id: UUID | None = None, asset_id: UUID | None = None, status: str | None = None, search: str | None = None):
    kwargs = {}
    kwargs["customer_id"] = customer_id
    kwargs["asset_id"] = asset_id
    kwargs["status"] = status
    kwargs["search"] = search
    return service.list_requests(db, company_id, **kwargs)

@router.get("/{request_id}", response_model=ServiceRequestRead, dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def get_record(request_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.get_request(db, company_id, request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="service_requests record not found")
    return record

@router.post("", response_model=ServiceRequestRead, status_code=201, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def create_record(payload: ServiceRequestCreate, db: DBSession, company_id: CompanyID):
    record = service.create_request(db, company_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(record)
    return record

@router.patch("/{request_id}", response_model=ServiceRequestRead, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def update_record(request_id: UUID, payload: ServiceRequestUpdate, db: DBSession, company_id: CompanyID):
    record = service.update_request(db, company_id, request_id, payload.model_dump(exclude_unset=True))
    if record is None:
        raise HTTPException(status_code=404, detail="service_requests record not found")
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{request_id}", status_code=204, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def delete_record(request_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.delete_request(db, company_id, request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="service_requests record not found")
    db.commit()
    return None
