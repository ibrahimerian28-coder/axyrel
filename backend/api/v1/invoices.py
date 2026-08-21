"""Task 44 API endpoints for invoices."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.invoice import InvoiceService
from backend.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission

router = APIRouter(prefix="/invoices", tags=["invoices"])
service = InvoiceService()

@router.get("", response_model=list[InvoiceRead], dependencies=[Depends(require_permission(Permission.BILLING_READ))])
def list_records(db: DBSession, company_id: CompanyID, customer_id: UUID | None = None, work_order_id: UUID | None = None, status: str | None = None):
    kwargs = {}
    kwargs["customer_id"] = customer_id
    kwargs["work_order_id"] = work_order_id
    kwargs["status"] = status
    return service.list_invoices(db, company_id, **kwargs)

@router.get("/{invoice_id}", response_model=InvoiceRead, dependencies=[Depends(require_permission(Permission.BILLING_READ))])
def get_record(invoice_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.get_invoice(db, company_id, invoice_id)
    if record is None:
        raise HTTPException(status_code=404, detail="invoices record not found")
    return record

@router.post("", response_model=InvoiceRead, status_code=201, dependencies=[Depends(require_permission(Permission.BILLING_MANAGE))])
def create_record(payload: InvoiceCreate, db: DBSession, company_id: CompanyID):
    record = service.create_invoice(db, company_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(record)
    return record

@router.patch("/{invoice_id}", response_model=InvoiceRead, dependencies=[Depends(require_permission(Permission.BILLING_MANAGE))])
def update_record(invoice_id: UUID, payload: InvoiceUpdate, db: DBSession, company_id: CompanyID):
    record = service.update_invoice(db, company_id, invoice_id, payload.model_dump(exclude_unset=True))
    if record is None:
        raise HTTPException(status_code=404, detail="invoices record not found")
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{invoice_id}", status_code=204, dependencies=[Depends(require_permission(Permission.BILLING_MANAGE))])
def delete_record(invoice_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.delete_invoice(db, company_id, invoice_id)
    if record is None:
        raise HTTPException(status_code=404, detail="invoices record not found")
    db.commit()
    return None
