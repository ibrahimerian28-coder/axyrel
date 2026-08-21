"""Task 44 API endpoints for expenses."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.expense import ExpenseService
from backend.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission

router = APIRouter(prefix="/expenses", tags=["expenses"])
service = ExpenseService()

@router.get("", response_model=list[ExpenseRead], dependencies=[Depends(require_permission(Permission.EXPENSE_READ))])
def list_records(db: DBSession, company_id: CompanyID, ):
    kwargs = {}
    return service.list_expenses(db, company_id, **kwargs)

@router.get("/{expense_id}", response_model=ExpenseRead, dependencies=[Depends(require_permission(Permission.EXPENSE_READ))])
def get_record(expense_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.get_expense(db, company_id, expense_id)
    if record is None:
        raise HTTPException(status_code=404, detail="expenses record not found")
    return record

@router.post("", response_model=ExpenseRead, status_code=201, dependencies=[Depends(require_permission(Permission.EXPENSE_MANAGE))])
def create_record(payload: ExpenseCreate, db: DBSession, company_id: CompanyID):
    record = service.create_expense(db, company_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(record)
    return record

@router.patch("/{expense_id}", response_model=ExpenseRead, dependencies=[Depends(require_permission(Permission.EXPENSE_MANAGE))])
def update_record(expense_id: UUID, payload: ExpenseUpdate, db: DBSession, company_id: CompanyID):
    record = service.update_expense(db, company_id, expense_id, payload.model_dump(exclude_unset=True))
    if record is None:
        raise HTTPException(status_code=404, detail="expenses record not found")
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{expense_id}", status_code=204, dependencies=[Depends(require_permission(Permission.EXPENSE_MANAGE))])
def delete_record(expense_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.delete_expense(db, company_id, expense_id)
    if record is None:
        raise HTTPException(status_code=404, detail="expenses record not found")
    db.commit()
    return None
