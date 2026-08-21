"""Task 44 API endpoints for inventory."""
from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.inventory import InventoryService
from backend.schemas.inventory import InventoryItemCreate, InventoryItemUpdate, InventoryItemRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission
router=APIRouter(prefix="/inventory", tags=["inventory"])
service=InventoryService()

@router.get("", response_model=list[InventoryItemRead], dependencies=[Depends(require_permission(Permission.INVENTORY_READ))])
def list_items(db: DBSession, company_id: CompanyID, search: str|None=None, status: str|None=None):
    return service.list_items(db, company_id, search=search, status=status)

@router.get("/{item_id}", response_model=InventoryItemRead, dependencies=[Depends(require_permission(Permission.INVENTORY_READ))])
def get_item(item_id: UUID, db: DBSession, company_id: CompanyID):
    item=service.get_item(db, company_id, item_id)
    if item is None: raise HTTPException(404, "inventory item not found")
    return item

@router.post("", response_model=InventoryItemRead, status_code=201, dependencies=[Depends(require_permission(Permission.INVENTORY_MANAGE))])
def create_item(payload: InventoryItemCreate, db: DBSession, company_id: CompanyID):
    item=service.create_item(db, company_id, payload.model_dump(exclude_unset=True)); db.commit(); db.refresh(item); return item

@router.patch("/{item_id}", response_model=InventoryItemRead, dependencies=[Depends(require_permission(Permission.INVENTORY_MANAGE))])
def update_item(item_id: UUID, payload: InventoryItemUpdate, db: DBSession, company_id: CompanyID):
    item=service.update_item(db, company_id, item_id, payload.model_dump(exclude_unset=True))
    if item is None: raise HTTPException(404, "inventory item not found")
    db.commit(); db.refresh(item); return item

@router.delete("/{item_id}", status_code=204, dependencies=[Depends(require_permission(Permission.INVENTORY_MANAGE))])
def delete_item(item_id: UUID, db: DBSession, company_id: CompanyID):
    item=service.delete_item(db, company_id, item_id)
    if item is None: raise HTTPException(404, "inventory item not found")
    db.commit(); return None
