"""Task 46 Service Visit integration tests."""
import os
import tempfile
import unittest
from uuid import uuid4

DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
DB_FILE.close()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_FILE.name}"
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes-123456"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import get_db
from backend.core.security import hash_password
from backend.main import app
from backend.models.base import Base
import backend.models  # noqa: F401  # register ORM tables
from backend.models.company import Company
from backend.models.customer import Customer
from backend.models.user import User


class Task46ServiceVisitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            f"sqlite:///{DB_FILE.name}",
            connect_args={"check_same_thread": False},
        )
        cls.Session = sessionmaker(bind=cls.engine, autoflush=False, autocommit=False)
        Base.metadata.create_all(cls.engine)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()
        try:
            os.unlink(DB_FILE.name)
        except OSError:
            pass

    def setUp(self):
        with self.Session() as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            company = Company(id=uuid4(), name="Company A", status="active")
            admin = User(
                id=uuid4(),
                company=company,
                email="admin@example.com",
                full_name="Admin",
                password_hash=hash_password("Password123!"),
                role="admin",
            )
            technician = User(
                id=uuid4(),
                company=company,
                email="tech@example.com",
                full_name="Tech",
                password_hash=hash_password("Password123!"),
                role="technician",
            )
            customer = Customer(id=uuid4(), company_id=company.id, name="Field Customer")
            db.add_all([company, admin, technician, customer])
            db.commit()
            self.company_id = company.id
            self.technician_id = technician.id
            self.customer_id = customer.id

        def override_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

    def _auth(self) -> dict[str, str]:
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "admin@example.com", "password": "Password123!"},
        )
        self.assertEqual(response.status_code, 200)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def _create_work_order(self, headers, status="Open", technician=True):
        payload = {
            "customer_id": str(self.customer_id),
            "title": "Replace filter",
            "status": status,
        }
        if technician:
            payload["assigned_technician_id"] = str(self.technician_id)
        response = self.client.post("/api/v1/work-orders", json=payload, headers=headers)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _create_visit(self, headers, work_order_id, status="Planned"):
        response = self.client.post(
            "/api/v1/service-visits",
            json={
                "work_order_id": work_order_id,
                "customer_id": str(self.customer_id),
                "status": status,
            },
            headers=headers,
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_cancelling_work_order_cancels_in_progress_visit(self):
        headers = self._auth()
        work_order = self._create_work_order(headers)
        visit = self._create_visit(headers, work_order["id"], status="In Progress")

        response = self.client.patch(
            f"/api/v1/work-orders/{work_order['id']}",
            json={"status": "Cancelled"},
            headers=headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "Cancelled")

        response = self.client.get(f"/api/v1/service-visits/{visit['id']}", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "Cancelled")

    def test_completed_visit_can_move_to_cancelled_and_syncs_work_order(self):
        headers = self._auth()
        work_order = self._create_work_order(headers)
        visit = self._create_visit(headers, work_order["id"], status="Completed")

        response = self.client.get(f"/api/v1/work-orders/{work_order['id']}", headers=headers)
        self.assertEqual(response.json()["status"], "Completed")

        response = self.client.patch(
            f"/api/v1/service-visits/{visit['id']}",
            json={"status": "Cancelled"},
            headers=headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "Cancelled")

        response = self.client.get(f"/api/v1/work-orders/{work_order['id']}", headers=headers)
        self.assertEqual(response.json()["status"], "Cancelled")

    def test_installing_part_deducts_technician_stock_and_restores_on_cancel(self):
        headers = self._auth()
        item = self.client.post(
            "/api/v1/inventory",
            json={"item_name": "Filter cartridge", "quantity": 10, "cost_price": 5},
            headers=headers,
        )
        self.assertEqual(item.status_code, 201, item.text)
        item_id = item.json()["id"]

        stock = self.client.post(
            "/api/v1/technician-stock",
            json={
                "technician_id": str(self.technician_id),
                "inventory_item_id": item_id,
                "quantity": 4,
            },
            headers=headers,
        )
        self.assertEqual(stock.status_code, 201, stock.text)

        work_order = self._create_work_order(headers)
        visit = self._create_visit(headers, work_order["id"], status="In Progress")

        response = self.client.post(
            f"/api/v1/service-visits/{visit['id']}/parts",
            json={"inventory_item_id": item_id, "quantity": 2},
            headers=headers,
        )
        self.assertEqual(response.status_code, 200, response.text)

        remaining = self.client.get(
            "/api/v1/technician-stock",
            params={
                "technician_id": str(self.technician_id),
                "inventory_item_id": item_id,
            },
            headers=headers,
        )
        self.assertEqual(remaining.status_code, 200)
        self.assertEqual(remaining.json()[0]["quantity"], 2)

        response = self.client.patch(
            f"/api/v1/service-visits/{visit['id']}",
            json={"status": "Cancelled"},
            headers=headers,
        )
        self.assertEqual(response.status_code, 200, response.text)

        restored = self.client.get(
            "/api/v1/technician-stock",
            params={
                "technician_id": str(self.technician_id),
                "inventory_item_id": item_id,
            },
            headers=headers,
        )
        self.assertEqual(restored.json()[0]["quantity"], 4)


if __name__ == "__main__":
    unittest.main()
