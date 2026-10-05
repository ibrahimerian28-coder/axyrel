"""Synthetic real FastAPI on a generated local PostgreSQL database only."""
import os
import sys
import tempfile
import json
import re
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
os.environ["AXYREL_ENV"] = "test"
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from backend.core.config import Settings, get_settings

# Read only the local connection configuration, never connect to its app DB.
url = make_url(Settings(_env_file=root / ".env").database_url)
if url.get_backend_name() != "postgresql" or url.host not in {"localhost", "127.0.0.1", "::1"}:
    raise RuntimeError("Phase 3 review requires local PostgreSQL, never a remote target.")
database_name = "axyrel_phase3_test_" + uuid4().hex
admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
test_port = int(os.environ.get("AXYREL_PHASE3_TEST_PORT", "8130"))
if not 1024 <= test_port <= 65535: raise RuntimeError("Invalid disposable API test port.")
marker = root / ("frontend/test-results/phase3-database.json" if test_port == 8130 else f"frontend/test-results/phase3-database-{test_port}.json")


def cleanup_database(name: str):
    if not re.fullmatch(r"axyrel_phase3_test_[0-9a-f]{32}", name):
        raise RuntimeError("Refusing unexpected disposable database cleanup.")
    if os.environ.get("AXYREL_RETAIN_TEST_DATABASES") == "1":
        print("Retained generated disposable test database; no DROP executed.", flush=True)
        return
    with admin.connect() as db:
        db.exec_driver_sql(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    marker.unlink(missing_ok=True)


@contextmanager
def working_directory(folder):
    previous = Path.cwd()
    os.chdir(folder)
    try:
        yield
    finally:
        os.chdir(previous)


@contextmanager
def synthetic_application():
    if marker.exists():
        raise RuntimeError("Clean the previous disposable Phase 3 test database before starting another run.")
    with admin.connect() as db:
        db.exec_driver_sql(f'CREATE DATABASE "{database_name}"')
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"database": database_name}), encoding="utf-8")
    engine = None
    try:
        with tempfile.TemporaryDirectory(prefix="axyrel-phase3-") as folder, working_directory(folder):
            os.environ.update(DATABASE_URL=url.set(database=database_name).render_as_string(hide_password=False),
                              SECRET_KEY="synthetic-phase3-only-secret-at-least-32-bytes", AXYREL_ENV="test")
            get_settings.cache_clear()
            import backend.core.config as configuration
            configuration.settings = get_settings()
            from backend.core.database import engine as synthetic_engine, SessionLocal
            engine = synthetic_engine
            from backend.core.security import hash_password
            from backend.models.base import Base
            import backend.models
            from backend.models.company import Company
            from backend.models.user import User
            from backend.models.customer import Customer
            from backend.models.asset import Asset
            from backend.models.service_request import ServiceRequest
            from backend.models.work_order import WorkOrder
            from backend.models.schedule import Schedule
            from backend.models.service_visit import ServiceVisit
            from backend.models.service_history import ServiceHistory
            from backend.models.inventory_item import InventoryItem
            from backend.models.technician_stock import TechnicianStock
            Base.metadata.create_all(engine)
            with SessionLocal() as db:
                company = Company(id=uuid4(), name="Synthetic Phase 3", status="active")
                other = Company(id=uuid4(), name="Synthetic Other", status="active")
                db.add_all([company, other]); db.flush()
                technician = None
                for email, role, tenant in [("admin", "admin", company), ("technician", "technician", company), ("foreign", "admin", other)]:
                    user = User(id=uuid4(), company=tenant, email=f"{email}@example.test", full_name=f"Synthetic {email.title()}", role=role, password_hash=hash_password("synthetic-password"))
                    db.add(user)
                    if role == "technician": technician = user
                customer = Customer(id=uuid4(), company_id=company.id, display_id=1001, name="Synthetic Customer", phone="+201000000001", status="Active")
                db.add(customer); db.flush()
                asset = Asset(id=uuid4(), company_id=company.id, customer_id=customer.id, display_id=2001, asset_type="HVAC", serial_number="SYN-001", model="Synthetic Model", status="Active")
                db.add(asset); db.flush()
                request = ServiceRequest(id=uuid4(), company_id=company.id, customer_id=customer.id, asset_id=asset.id, display_id=1, title="Synthetic Request", status="Open")
                db.add(request); db.flush()
                order = WorkOrder(id=uuid4(), company_id=company.id, customer_id=customer.id, asset_id=asset.id, service_request_id=request.id, assigned_technician_id=technician.id, display_id=1, title="Synthetic Order", status="Open")
                db.add(order); db.flush()
                start = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0)
                schedule = Schedule(id=uuid4(), company_id=company.id, work_order_id=order.id, technician_id=technician.id, start_at=start, end_at=start + timedelta(hours=2), status="Scheduled")
                db.add(schedule); db.flush()
                visit = ServiceVisit(id=uuid4(), company_id=company.id, work_order_id=order.id, schedule_id=schedule.id, customer_id=customer.id, asset_id=asset.id, technician_id=technician.id, status="Planned")
                db.add(visit); db.flush()
                db.add(ServiceHistory(id=uuid4(), company_id=company.id, customer_id=customer.id, asset_id=asset.id, work_order_id=order.id, service_visit_id=visit.id, technician_id=technician.id, service_type="Inspection", service_date=start.replace(tzinfo=None), summary="Explicit synthetic service history", status="Active"))
                item = InventoryItem(id=uuid4(), company_id=company.id, item_name="Synthetic Filter", quantity=20, cost_price=5, status="Active")
                db.add(item); db.flush()
                db.add(TechnicianStock(id=uuid4(), company_id=company.id, technician_id=technician.id, inventory_item_id=item.id, quantity=8))
                db.commit()
            from backend.main import app
            try:
                yield app
            finally:
                engine.dispose(); engine = None
    finally:
        if engine is not None: engine.dispose()
        cleanup_database(database_name)
        admin.dispose()


if __name__ == "__main__":
    if "--cleanup" in sys.argv:
        if marker.exists():
            cleanup_database(json.loads(marker.read_text(encoding="utf-8"))["database"])
        admin.dispose()
        print("Disposable Phase 3 database cleanup complete.")
    else:
        import uvicorn
        with synthetic_application() as app:
            uvicorn.run(app, host="127.0.0.1", port=test_port, log_level="warning", access_log=False)
