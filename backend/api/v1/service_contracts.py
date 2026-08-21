"""Task 44 API endpoints for service contracts."""
from __future__ import annotations
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.services.service_contract import ServiceContractService
from backend.schemas.service_contract import ServiceContractCreate, ServiceContractUpdate, ServiceContractRead
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission

router = APIRouter(prefix="/service-contracts", tags=["service contracts"])
service = ServiceContractService()

@router.get("", response_model=list[ServiceContractRead], dependencies=[Depends(require_permission(Permission.BILLING_READ))])
def list_records(db: DBSession, company_id: CompanyID, ):
    kwargs = {}
    return service.list_contracts(db, company_id, **kwargs)

@router.get("/{contract_id}", response_model=ServiceContractRead, dependencies=[Depends(require_permission(Permission.BILLING_READ))])
def get_record(contract_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.get_contract(db, company_id, contract_id)
    if record is None:
        raise HTTPException(status_code=404, detail="service_contracts record not found")
    return record

@router.post("", response_model=ServiceContractRead, status_code=201, dependencies=[Depends(require_permission(Permission.BILLING_MANAGE))])
def create_record(payload: ServiceContractCreate, db: DBSession, company_id: CompanyID):
    record = service.create_contract(db, company_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(record)
    return record

@router.patch("/{contract_id}", response_model=ServiceContractRead, dependencies=[Depends(require_permission(Permission.BILLING_MANAGE))])
def update_record(contract_id: UUID, payload: ServiceContractUpdate, db: DBSession, company_id: CompanyID):
    record = service.update_contract(db, company_id, contract_id, payload.model_dump(exclude_unset=True))
    if record is None:
        raise HTTPException(status_code=404, detail="service_contracts record not found")
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{contract_id}", status_code=204, dependencies=[Depends(require_permission(Permission.BILLING_MANAGE))])
def delete_record(contract_id: UUID, db: DBSession, company_id: CompanyID):
    record = service.delete_contract(db, company_id, contract_id)
    if record is None:
        raise HTTPException(status_code=404, detail="service_contracts record not found")
    db.commit()
    return None
