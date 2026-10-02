"""Real accepted FastAPI with synthetic isolated SQLite, never configured app DB."""
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
with tempfile.TemporaryDirectory(prefix="axyrel-phase2-") as folder:
    os.chdir(folder)  # No workspace .env is read.
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(folder) / 'synthetic.db'}"
    os.environ["SECRET_KEY"] = "synthetic-phase2-local-test-only"
    os.environ["AXYREL_ENV"] = "test"
    from backend.core.database import engine, SessionLocal
    from backend.core.security import hash_password
    from backend.models.base import Base
    import backend.models
    from backend.models.company import Company
    from backend.models.user import User
    from backend.models.customer import Customer
    from backend.models.asset import Asset
    from backend.models.work_order import WorkOrder
    from backend.models.service_history import ServiceHistory
    from datetime import datetime
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        company = Company(id=uuid4(), name="Synthetic Review", status="active")
        db.add(company)
        for role in ("admin", "technician"):
            db.add(User(id=uuid4(), company=company, email=f"{role}@example.test", full_name=f"Synthetic {role.title()}", role=role, password_hash=hash_password("synthetic-password")))
        customer = Customer(id=uuid4(), company_id=company.id, display_id=1001, name="Synthetic Customer", phone="+201000000001", area="Synthetic Area", status="Active")
        db.add(customer); db.flush()
        asset = Asset(id=uuid4(), company_id=company.id, customer_id=customer.id, display_id=2001, asset_type="HVAC", model="Synthetic Model", serial_number="SYN-001", status="Active")
        db.add(asset); db.flush()
        db.add(WorkOrder(id=uuid4(), company_id=company.id, customer_id=customer.id, asset_id=asset.id, title="Synthetic inspection", status="Open"))
        db.add(ServiceHistory(id=uuid4(), company_id=company.id, customer_id=customer.id, asset_id=asset.id, service_type="Inspection", summary="Synthetic completed inspection", service_date=datetime(2026, 1, 15), status="Active"))
        db.commit()
    from backend.main import app
    import uvicorn
    try:
        uvicorn.run(app, host="127.0.0.1", port=8110, log_level="warning", access_log=False)
    finally:
        engine.dispose()
