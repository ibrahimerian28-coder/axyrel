"""Task 44 reporting endpoints for profitability."""
from datetime import date
from fastapi import APIRouter, Depends
from backend.services.profitability import ProfitabilityService
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission
router=APIRouter(prefix="/profitability", tags=["profitability"])
service=ProfitabilityService()
@router.get("/summary", dependencies=[Depends(require_permission(Permission.REPORT_READ))])
def summary(db: DBSession, company_id: CompanyID, start_date: date|None=None, end_date: date|None=None):
    return service.summary(db, company_id, start_date, end_date)
@router.get("/expenses", dependencies=[Depends(require_permission(Permission.REPORT_READ))])
def expense_breakdown(db: DBSession, company_id: CompanyID, start_date: date|None=None, end_date: date|None=None):
    return service.expense_breakdown(db, company_id, start_date, end_date)
