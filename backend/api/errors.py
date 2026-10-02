"""Narrow database-conflict classification and safe internal-error responses."""
import logging

from fastapi import Request
from psycopg import Error as PostgreSQLError
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

UNIQUE_CONFLICT_DETAILS = {
    "uq_inventory_items_company_item_name": "An inventory item with this name already exists.",
    "uq_technician_stock_company_technician_item": "Stock for this technician and inventory item already exists.",
    "uq_invoices_company_number": "An invoice with this number already exists.",
    "uq_service_contracts_company_number": "A service contract with this number already exists.",
}


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    original = exc.orig
    if isinstance(original, PostgreSQLError) and original.sqlstate == "23505":
        detail = UNIQUE_CONFLICT_DETAILS.get(original.diag.constraint_name)
        if detail is not None:
            return JSONResponse(status_code=409, content={"detail": detail})
    logger.error(
        "Unhandled database integrity error",
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled application error",
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
