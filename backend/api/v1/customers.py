"""Task 44 API endpoints for customers."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.customer import CustomerService
from backend.schemas.customer import CustomerCreate, CustomerUpdate, CustomerRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission

router = APIRouter(prefix="/customers", tags=["customers"])
service = CustomerService()

@router.get("", response_model=list[CustomerRead], dependencies=[Depends(require_permission(Permission.CUSTOMER_READ))])
def list_records(db: DBSession, company_id: CompanyID, search: str | None = None):
    kwargs = {}
    kwargs["search"] = search
    return service.list_customers(db, company_id, **kwargs)

@router.get("/{customer_id}", response_model=CustomerRead, dependencies=[Depends(require_permission(Permission.CUSTOMER_READ))])
def get_record(customer_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.get_customer(db, company_id, customer_id)
    if record is None:
        raise HTTPException(status_code=404, detail="customers record not found")
    return record

@router.post("", response_model=CustomerRead, status_code=201, dependencies=[Depends(require_permission(Permission.CUSTOMER_MANAGE))])
def create_record(payload: CustomerCreate, db: DBSession, company_id: CompanyID):
    record = service.create_customer(db, company_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(record)
    return record

@router.patch("/{customer_id}", response_model=CustomerRead, dependencies=[Depends(require_permission(Permission.CUSTOMER_MANAGE))])
def update_record(customer_id: UUID, payload: CustomerUpdate, db: DBSession, company_id: CompanyID):
    record = service.update_customer(db, company_id, customer_id, payload.model_dump(exclude_unset=True))
    if record is None:
        raise HTTPException(status_code=404, detail="customers record not found")
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{customer_id}", status_code=204, dependencies=[Depends(require_permission(Permission.CUSTOMER_MANAGE))])
def delete_record(customer_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.delete_customer(db, company_id, customer_id)
    if record is None:
        raise HTTPException(status_code=404, detail="customers record not found")
    db.commit()
    return None
