"""Task 44 API endpoints for work orders."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.work_order import WorkOrderService
from backend.schemas.work_order import WorkOrderCreate, WorkOrderUpdate, WorkOrderRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission

router = APIRouter(prefix="/work-orders", tags=["work orders"])
service = WorkOrderService()

@router.get("", response_model=list[WorkOrderRead], dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def list_records(db: DBSession, company_id: CompanyID, customer_id: UUID | None = None, asset_id: UUID | None = None, service_request_id: UUID | None = None, status: str | None = None, assigned_technician_id: UUID | None = None, search: str | None = None):
    kwargs = {}
    kwargs["customer_id"] = customer_id
    kwargs["asset_id"] = asset_id
    kwargs["service_request_id"] = service_request_id
    kwargs["status"] = status
    kwargs["assigned_technician_id"] = assigned_technician_id
    kwargs["search"] = search
    return service.list_work_orders(db, company_id, **kwargs)

@router.get("/{work_order_id}", response_model=WorkOrderRead, dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def get_record(work_order_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.get_work_order(db, company_id, work_order_id)
    if record is None:
        raise HTTPException(status_code=404, detail="work_orders record not found")
    return record

@router.post("", response_model=WorkOrderRead, status_code=201, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def create_record(payload: WorkOrderCreate, db: DBSession, company_id: CompanyID):
    record = service.create_work_order(db, company_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(record)
    return record

@router.patch("/{work_order_id}", response_model=WorkOrderRead, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def update_record(work_order_id: UUID, payload: WorkOrderUpdate, db: DBSession, company_id: CompanyID):
    record = service.update_work_order(db, company_id, work_order_id, payload.model_dump(exclude_unset=True))
    if record is None:
        raise HTTPException(status_code=404, detail="work_orders record not found")
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{work_order_id}", status_code=204, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def delete_record(work_order_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.delete_work_order(db, company_id, work_order_id)
    if record is None:
        raise HTTPException(status_code=404, detail="work_orders record not found")
    db.commit()
    return None
