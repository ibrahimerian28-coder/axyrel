"""Task 44 API endpoints for service visits."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from backend.services.service_visit import ServiceVisitService
from backend.schemas.service_visit import ServiceVisitCreate, ServiceVisitUpdate, ServiceVisitRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission
from backend.schemas.service_desk import Reason

router = APIRouter(prefix="/service-visits", tags=["service visits"])
service = ServiceVisitService()


class ServiceVisitPartInstall(BaseModel):
    inventory_item_id: UUID
    quantity: int = Field(gt=0)


def _bad_request(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[ServiceVisitRead], dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def list_records(
    db: DBSession,
    company_id: CompanyID,
    work_order_id: UUID | None = None,
    schedule_id: UUID | None = None,
    technician_id: UUID | None = None,
    status: str | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
):
    try:
        return service.list_visits(
            db,
            company_id,
            work_order_id=work_order_id,
            schedule_id=schedule_id,
            technician_id=technician_id,
            status=status,
            start_from=start_from,
            start_to=start_to,
        )
    except ValueError as exc:
        raise _bad_request(exc) from exc

@router.get("/{visit_id}", response_model=ServiceVisitRead, dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def get_record(visit_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.get_visit(db, company_id, visit_id)
    if record is None:
        raise HTTPException(status_code=404, detail="service_visits record not found")
    return record

@router.post("", response_model=ServiceVisitRead, status_code=201, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def create_record(payload: ServiceVisitCreate, db: DBSession, company_id: CompanyID):
    try:
        record = service.create_visit(db, company_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise _bad_request(exc) from exc
    db.commit()
    db.refresh(record)
    return record

@router.patch("/{visit_id}", response_model=ServiceVisitRead, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def update_record(visit_id: UUID, payload: ServiceVisitUpdate, db: DBSession, company_id: CompanyID):
    try:
        record = service.update_visit(db, company_id, visit_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise _bad_request(exc) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="service_visits record not found")
    db.commit()
    db.refresh(record)
    return record


@router.post(
    "/{visit_id}/parts",
    response_model=ServiceVisitRead,
    dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))],
)
def install_part(
    visit_id: UUID,
    payload: ServiceVisitPartInstall,
    db: DBSession,
    company_id: CompanyID,
):
    try:
        record = service.install_part(
            db, company_id, visit_id, payload.inventory_item_id, payload.quantity
        )
    except ValueError as exc:
        raise _bad_request(exc) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="service_visits record not found")
    db.commit()
    db.refresh(record)
    return record


@router.post("/{visit_id}/parts/reverse", response_model=ServiceVisitRead,
             dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def reverse_parts(visit_id: UUID, payload: Reason, db: DBSession, company_id: CompanyID):
    try:
        record = service.reverse_parts(db, company_id, visit_id, payload.reason)
    except ValueError as exc:
        raise _bad_request(exc) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="Visit not found")
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{visit_id}", status_code=204, dependencies=[Depends(require_permission(Permission.SERVICE_MANAGE))])
def delete_record(visit_id: UUID, db: DBSession, company_id: CompanyID):
    try:
        record = service.delete_visit(db, company_id, visit_id)
    except ValueError as exc:
        raise _bad_request(exc) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="service_visits record not found")
    db.commit()
    return None
