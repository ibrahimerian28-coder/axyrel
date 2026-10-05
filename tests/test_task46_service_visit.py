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

    def test_active_visit_cannot_be_reassigned_to_cancelled_work_order(self):
        headers = self._auth()
        source = self._create_work_order(headers)
        visit = self._create_visit(headers, source["id"], status="In Progress")
        target = self._create_work_order(headers, status="Cancelled")

        response = self.client.patch(
            f"/api/v1/service-visits/{visit['id']}",
            json={"work_order_id": target["id"]},
            headers=headers,
        )
        visit_response = self.client.get(
            f"/api/v1/service-visits/{visit['id']}", headers=headers
        )
        self.assertEqual(visit_response.status_code, 200, visit_response.text)
        target_response = self.client.get(
            f"/api/v1/work-orders/{target['id']}", headers=headers
        )
        self.assertEqual(target_response.status_code, 200, target_response.text)
        resulting_visit = visit_response.json()
        resulting_target = target_response.json()
        self.assertFalse(
            resulting_visit["work_order_id"] == resulting_target["id"]
            and resulting_visit["status"] in {"Planned", "In Progress"}
            and resulting_target["status"] == "Cancelled",
            f"D46-01: PATCH status={response.status_code}; "
            f"visit status={resulting_visit['status']}, "
            f"work_order_id={resulting_visit['work_order_id']}; "
            f"target id={resulting_target['id']}, status={resulting_target['status']}",
        )

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

    def test_completed_visit_can_move_to_cancelled_without_terminating_job(self):
        headers = self._auth()
        work_order = self._create_work_order(headers)
        visit = self._create_visit(headers, work_order["id"], status="Completed")

        response = self.client.get(f"/api/v1/work-orders/{work_order['id']}", headers=headers)
        self.assertEqual(response.json()["status"], "Open")

        response = self.client.patch(
            f"/api/v1/service-visits/{visit['id']}",
            json={"status": "Cancelled"},
            headers=headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "Cancelled")

        response = self.client.get(f"/api/v1/work-orders/{work_order['id']}", headers=headers)
        self.assertEqual(response.json()["status"], "Open")

    def test_cancelled_visit_restores_stock_to_original_technician_after_reassignment(self):
        headers = self._auth()
        technician_b_id = uuid4()
        with self.Session() as db:
            db.add(User(
                id=technician_b_id, company_id=self.company_id,
                email="tech-b@example.com", full_name="Technician B",
                password_hash=hash_password("Password123!"), role="technician",
            ))
            db.commit()

        item = self.client.post(
            "/api/v1/inventory",
            json={"item_name": "Filter cartridge", "quantity": 10, "cost_price": 5},
            headers=headers,
        )
        self.assertEqual(item.status_code, 201, item.text)
        item_id = item.json()["id"]
        for technician_id, quantity in ((self.technician_id, 2), (technician_b_id, 0)):
            stock = self.client.post(
                "/api/v1/technician-stock",
                json={"technician_id": str(technician_id),
                      "inventory_item_id": item_id, "quantity": quantity},
                headers=headers,
            )
            self.assertEqual(stock.status_code, 201, stock.text)

        def stock_quantity(technician_id):
            response = self.client.get(
                "/api/v1/technician-stock",
                params={"technician_id": str(technician_id), "inventory_item_id": item_id},
                headers=headers,
            )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(len(response.json()), 1, response.text)
            return response.json()[0]["quantity"]

        a_before = stock_quantity(self.technician_id)
        work_order = self._create_work_order(headers)
        visit = self._create_visit(headers, work_order["id"], status="In Progress")
        self.assertEqual(visit["technician_id"], str(self.technician_id))
        install = self.client.post(
            f"/api/v1/service-visits/{visit['id']}/parts",
            json={"inventory_item_id": item_id, "quantity": 1}, headers=headers,
        )
        self.assertEqual(install.status_code, 200, install.text)
        a_after = stock_quantity(self.technician_id)
        self.assertEqual(a_after, a_before - 1)
        change = self.client.patch(
            f"/api/v1/service-visits/{visit['id']}",
            json={"technician_id": str(technician_b_id)}, headers=headers,
        )
        self.assertEqual(change.status_code, 200, change.text)
        self.assertEqual(change.json()["technician_id"], str(technician_b_id))
        b_before = stock_quantity(technician_b_id)
        cancel = self.client.patch(
            f"/api/v1/service-visits/{visit['id']}",
            json={"status": "Cancelled"}, headers=headers,
        )
        self.assertEqual(cancel.status_code, 200, cancel.text)
        self.assertEqual(cancel.json()["status"], "Cancelled")
        a_final = stock_quantity(self.technician_id)
        b_final = stock_quantity(technician_b_id)
        self.assertEqual(
            (a_final, b_final), (a_before, b_before),
            f"D46-02: install HTTP {install.status_code}; A before={a_before}, "
            f"after install={a_after}; technician change HTTP {change.status_code}, "
            f"technician_id={change.json()['technician_id']}; "
            f"cancel HTTP {cancel.status_code}, status={cancel.json()['status']}; "
            f"A final={a_final}; B before reversal={b_before}, final={b_final}",
        )

    def test_generic_install_reference_cannot_create_stock_on_visit_cancellation(self):
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
            json={"technician_id": str(self.technician_id),
                  "inventory_item_id": item_id, "quantity": 0},
            headers=headers,
        )
        self.assertEqual(stock.status_code, 201, stock.text)
        work_order = self._create_work_order(headers)
        visit = self._create_visit(headers, work_order["id"], status="In Progress")
        self.assertEqual(visit["technician_id"], str(self.technician_id))

        def stock_quantity():
            response = self.client.get(
                "/api/v1/technician-stock",
                params={"technician_id": str(self.technician_id), "inventory_item_id": item_id},
                headers=headers,
            )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(len(response.json()), 1, response.text)
            return response.json()[0]["quantity"]

        before = stock_quantity()
        self.assertEqual(before, 0)
        with TestClient(app, raise_server_exceptions=False) as client:
            transaction = client.post(
                "/api/v1/inventory-transactions",
                json={"inventory_item_id": item_id, "transaction_type": "OUT",
                      "quantity": 1, "reference_type": "SERVICE_VISIT_INSTALL",
                      "reference_id": visit["id"],
                      "notes": f"Installed on service visit {visit['id']}; technician_id={self.technician_id}"},
                headers=headers,
            )
        before_cancel = stock_quantity()
        self.assertEqual(before_cancel, 0)
        cancel = self.client.patch(
            f"/api/v1/service-visits/{visit['id']}",
            json={"status": "Cancelled"}, headers=headers,
        )
        self.assertEqual(cancel.status_code, 200, cancel.text)
        self.assertEqual(cancel.json()["status"], "Cancelled")
        final = stock_quantity()
        result = (
            f"generic transaction HTTP {transaction.status_code}, body={transaction.text}; "
            f"stock before={before}, before cancellation={before_cancel}; "
            f"cancellation HTTP {cancel.status_code}; final stock={final}"
        )
        print(result)
        self.assertEqual(final, before, result)

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
