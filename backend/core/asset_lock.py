"""Tenant transaction serialization shared by Asset CRUD and CSV import."""
import hashlib
from sqlalchemy import text

def lock_assets(db, company_id):
    """All API Asset writers share one tenant transaction lock on PostgreSQL."""
    if db.get_bind().dialect.name == "postgresql":
        key = int.from_bytes(hashlib.sha256(f"axyrel:assets:{company_id}".encode()).digest()[:8], "big", signed=True)
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})


