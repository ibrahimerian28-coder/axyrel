"""Axyrel FastAPI application entry point for Task 44."""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.core.config import get_settings
from sqlalchemy.exc import IntegrityError
from backend.api.errors import integrity_error_handler, unexpected_error_handler
from backend.api.v1 import router as api_v1_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings().validate_production_security()
    yield


app=FastAPI(title="Axyrel API", version="1.0.0", lifespan=lifespan)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, unexpected_error_handler)
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/health", tags=["system"])
def health() -> dict[str,str]:
    return {"status":"ok"}
