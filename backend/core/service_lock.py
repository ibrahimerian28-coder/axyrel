"""Serialize service mutations per tenant, including retries across workers."""
import hashlib
from sqlalchemy import text
from backend.core.tenant_isolation import require_company_id


def lock_service(db, company_id):
    company_id = require_company_id(company_id)
    if db.get_bind().dialect.name == "postgresql":
        key = int.from_bytes(hashlib.sha256(f"axyrel:service:{company_id}".encode()).digest()[:8], "big", signed=True)
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
