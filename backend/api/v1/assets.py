"""Task 44 API endpoints for assets."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.asset import AssetService
from backend.schemas.asset import AssetCreate, AssetUpdate, AssetRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission

router = APIRouter(prefix="/assets", tags=["assets"])
service = AssetService()

@router.get("", response_model=list[AssetRead], dependencies=[Depends(require_permission(Permission.ASSET_READ))])
def list_records(db: DBSession, company_id: CompanyID, customer_id: UUID | None = None, search: str | None = None):
    kwargs = {}
    kwargs["customer_id"] = customer_id
    kwargs["search"] = search
    return service.list_assets(db, company_id, **kwargs)

@router.get("/{asset_id}", response_model=AssetRead, dependencies=[Depends(require_permission(Permission.ASSET_READ))])
def get_record(asset_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.get_asset(db, company_id, asset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="assets record not found")
    return record

@router.post("", response_model=AssetRead, status_code=201, dependencies=[Depends(require_permission(Permission.ASSET_MANAGE))])
def create_record(payload: AssetCreate, db: DBSession, company_id: CompanyID):
    record = service.create_asset(db, company_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(record)
    return record

@router.patch("/{asset_id}", response_model=AssetRead, dependencies=[Depends(require_permission(Permission.ASSET_MANAGE))])
def update_record(asset_id: UUID, payload: AssetUpdate, db: DBSession, company_id: CompanyID):
    record = service.update_asset(db, company_id, asset_id, payload.model_dump(exclude_unset=True))
    if record is None:
        raise HTTPException(status_code=404, detail="assets record not found")
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{asset_id}", status_code=204, dependencies=[Depends(require_permission(Permission.ASSET_MANAGE))])
def delete_record(asset_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.delete_asset(db, company_id, asset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="assets record not found")
    db.commit()
    return None
