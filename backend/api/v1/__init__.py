"""Task 46 API v1 router registry."""
from fastapi import APIRouter

from backend.api.v1.assets import router as assets_router
from backend.api.v1.audit_logs import router as audit_logs_router
from backend.api.v1.auth import router as auth_router
from backend.api.v1.customers import router as customers_router
from backend.api.v1.expenses import router as expenses_router
from backend.api.v1.inventory import router as inventory_router
from backend.api.v1.inventory_transactions import router as inventory_transactions_router
from backend.api.v1.invoices import router as invoices_router
from backend.api.v1.notifications import router as notifications_router
from backend.api.v1.profitability import router as profitability_router
from backend.api.v1.schedules import router as schedules_router
from backend.api.v1.service_contracts import router as service_contracts_router
from backend.api.v1.service_history import router as service_history_router
from backend.api.v1.service_requests import router as service_requests_router
from backend.api.v1.service_visits import router as service_visits_router
from backend.api.v1.technician_stock import router as technician_stock_router
from backend.api.v1.work_orders import router as work_orders_router

router = APIRouter()
for _router in (
    auth_router,
    customers_router,
    assets_router,
    service_requests_router,
    work_orders_router,
    schedules_router,
    service_visits_router,
    service_history_router,
    service_contracts_router,
    invoices_router,
    expenses_router,
    inventory_router,
    inventory_transactions_router,
    technician_stock_router,
    notifications_router,
    audit_logs_router,
    profitability_router,
):
    router.include_router(_router)
