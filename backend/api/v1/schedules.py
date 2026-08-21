"""Task 44 API endpoints for schedules."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.schedule import ScheduleService
from backend.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission

router = APIRouter(prefix="/schedules", tags=["schedules"])
service = ScheduleService()

@router.get("", response_model=list[ScheduleRead], dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def list_records(db: DBSession, company_id: CompanyID, work_order_id: UUID | None = None, technician_id: UUID | None = None, status: str | None = None, start_from: datetime | None = None, start_to: datetime | None = None):
    kwargs = {}
    kwargs["work_order_id"] = work_order_id
    kwargs["technician_id"] = technician_id
    kwargs["status"] = status
    kwargs["start_from"] = start_from
    kwargs["start_to"] = start_to
    return service.list_schedules(db, company_id, **kwargs)

@router.get("/{schedule_id}", response_model=ScheduleRead, dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def get_record(schedule_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.get_schedule(db, company_id, schedule_id)
    if record is None:
        raise HTTPException(status_code=404, detail="schedules record not found")
    return record

@router.post("", response_model=ScheduleRead, status_code=201, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def create_record(payload: ScheduleCreate, db: DBSession, company_id: CompanyID):
    record = service.create_schedule(db, company_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(record)
    return record

@router.patch("/{schedule_id}", response_model=ScheduleRead, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def update_record(schedule_id: UUID, payload: ScheduleUpdate, db: DBSession, company_id: CompanyID):
    record = service.update_schedule(db, company_id, schedule_id, payload.model_dump(exclude_unset=True))
    if record is None:
        raise HTTPException(status_code=404, detail="schedules record not found")
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{schedule_id}", status_code=204, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def delete_record(schedule_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.delete_schedule(db, company_id, schedule_id)
    if record is None:
        raise HTTPException(status_code=404, detail="schedules record not found")
    db.commit()
    return None
