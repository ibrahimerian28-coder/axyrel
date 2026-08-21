"""Task 44 technician-stock endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.services.technician_stock import TechnicianStockService
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission
router=APIRouter(prefix="/technician-stock", tags=["technician stock"])
service=TechnicianStockService()
class StockCreate(BaseModel):
    technician_id: UUID
    inventory_item_id: UUID
    quantity: int = 0
class StockSetQuantity(BaseModel):
    quantity: int
@router.get("", dependencies=[Depends(require_permission(Permission.INVENTORY_READ))])
def list_stock(db: DBSession, company_id: CompanyID, technician_id: UUID|None=None, inventory_item_id: UUID|None=None):
    return service.list_stock(db, company_id, technician_id, inventory_item_id)
@router.get("/{stock_id}", dependencies=[Depends(require_permission(Permission.INVENTORY_READ))])
def get_stock(stock_id: UUID, db: DBSession, company_id: CompanyID):
    r=service.get_stock(db, company_id, stock_id)
    if r is None: raise HTTPException(404,"technician stock not found")
    return r
@router.post("", status_code=201, dependencies=[Depends(require_permission(Permission.INVENTORY_MANAGE))])
def create_stock(payload: StockCreate, db: DBSession, company_id: CompanyID):
    r=service.create_stock(db, company_id, payload.model_dump()); db.commit(); db.refresh(r); return r
@router.patch("/{stock_id}", dependencies=[Depends(require_permission(Permission.INVENTORY_MANAGE))])
def set_quantity(stock_id: UUID, payload: StockSetQuantity, db: DBSession, company_id: CompanyID):
    r=service.set_quantity(db, company_id, stock_id, payload.quantity)
    if r is None: raise HTTPException(404,"technician stock not found")
    db.commit(); db.refresh(r); return r
