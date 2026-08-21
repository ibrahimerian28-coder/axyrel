"""Axyrel FastAPI application entry point for Task 44."""
from fastapi import FastAPI
from backend.api.v1 import router as api_v1_router

app=FastAPI(title="Axyrel API", version="1.0.0")
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/health", tags=["system"])
def health() -> dict[str,str]:
    return {"status":"ok"}
