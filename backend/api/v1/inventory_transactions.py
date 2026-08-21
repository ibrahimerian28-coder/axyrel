"""Task 44 inventory transaction endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.services.inventory_transactions import InventoryTransactionService
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission
router=APIRouter(prefix="/inventory-transactions", tags=["inventory transactions"])
service=InventoryTransactionService()
class TransactionCreate(BaseModel):
    inventory_item_id: UUID
    transaction_type: str
    quantity: int
    reference_type: str|None=None
    reference_id: UUID|None=None
    notes: str|None=None
@router.get("", dependencies=[Depends(require_permission(Permission.INVENTORY_READ))])
def list_transactions(db: DBSession, company_id: CompanyID, inventory_item_id: UUID|None=None, transaction_type: str|None=None):
    return service.list_transactions(db, company_id, inventory_item_id, transaction_type)
@router.get("/{transaction_id}", dependencies=[Depends(require_permission(Permission.INVENTORY_READ))])
def get_transaction(transaction_id: UUID, db: DBSession, company_id: CompanyID):
    r=service.get_transaction(db, company_id, transaction_id)
    if r is None: raise HTTPException(404,"inventory transaction not found")
    return r
@router.post("", status_code=201, dependencies=[Depends(require_permission(Permission.INVENTORY_MANAGE))])
def create_transaction(payload: TransactionCreate, db: DBSession, company_id: CompanyID):
    r=service.create_transaction(db, company_id, payload.model_dump()); db.commit(); db.refresh(r); return r
