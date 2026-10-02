"""OD-17 Invoice links and monetary compatibility on disposable SQLite."""
import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import UUID, uuid4

DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
DB_FILE.close()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_FILE.name}"
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes-123456"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker
import backend.models
from backend.api.v1 import router
from backend.core.database import get_db
from backend.core.security import create_access_token, hash_password
from backend.main import app as application
from backend.models.base import Base
from backend.models.company import Company
from backend.models.customer import Customer
from backend.models.user import User
from backend.models.work_order import WorkOrder
from backend.models.invoice import Invoice
from backend.services.invoice import InvoiceService, WorkOrderReferenceError


class Task56OrderBillingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(f"sqlite:///{DB_FILE.name}", connect_args={"check_same_thread": False})

        @event.listens_for(cls.engine, "connect")
        def enforce_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        cls.Session = sessionmaker(bind=cls.engine, autoflush=False)
        Base.metadata.create_all(cls.engine)
        cls.password_hash = hash_password("Password123!")

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        os.unlink(DB_FILE.name)

    def setUp(self):
        self.company, self.foreign_company, self.customer, self.other_customer, self.foreign_customer = [uuid4() for _ in range(5)]
        self.order, self.other_order, self.foreign_order, self.deleted_order, self.cancelled_order = [uuid4() for _ in range(5)]
        self.invoice, self.foreign_invoice, self.deleted_invoice, self.admin = [uuid4() for _ in range(4)]
        with self.Session() as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            db.add_all([Company(id=self.company, name="A", status="active"),
                        Company(id=self.foreign_company, name="B", status="active")])
            db.flush()
            db.add_all([Customer(id=self.customer, company_id=self.company, name="A1"),
                        Customer(id=self.other_customer, company_id=self.company, name="A2"),
                        Customer(id=self.foreign_customer, company_id=self.foreign_company, name="B1"),
                        User(id=self.admin, company_id=self.company, email="admin@example.com", full_name="Admin",
                             role="admin", password_hash=self.password_hash)])
            db.flush()
            for order_id, company, customer, status in (
                (self.order, self.company, self.customer, "Open"),
                (self.other_order, self.company, self.customer, "Completed"),
                (self.foreign_order, self.foreign_company, self.foreign_customer, "Open"),
                (self.deleted_order, self.company, self.customer, "Deleted"),
                (self.cancelled_order, self.company, self.customer, "Cancelled"),
            ):
                db.add(WorkOrder(id=order_id, company_id=company, customer_id=customer, title="Order", status=status))
            db.flush()
            for invoice_id, company, customer, order_id, status in (
                (self.invoice, self.company, self.other_customer, self.order, "Draft"),
                (self.foreign_invoice, self.foreign_company, self.foreign_customer, self.foreign_order, "Draft"),
                (self.deleted_invoice, self.company, self.customer, self.order, "Deleted"),
            ):
                db.add(Invoice(id=invoice_id, company_id=company, customer_id=customer, work_order_id=order_id,
                               invoice_number=str(invoice_id), issue_date=date(2026, 10, 2), total=Decimal("12.34"), status=status))
            db.commit()
        app = FastAPI()
        app.exception_handlers.update(application.exception_handlers)
        app.include_router(router, prefix="/api/v1")

        def disposable_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = disposable_db
        self.client = TestClient(app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)
        self.headers = {"Authorization": f"Bearer {create_access_token(str(self.admin))}"}

    def _create(self, **data):
        return self.client.post("/api/v1/invoices", headers=self.headers,
                                json={"customer_id": str(self.other_customer), "invoice_number": str(uuid4()),
                                      "issue_date": "2026-10-02", **data})

    def _patch(self, data, invoice_id=None):
        return self.client.patch(f"/api/v1/invoices/{invoice_id or self.invoice}", headers=self.headers, json=data)

    def _read(self):
        with self.Session() as db:
            row = db.get(Invoice, self.invoice)
            return row.work_order_id, row.total, row.subtotal, row.notes, row.status

    def test_api_order_creation_to_invoice_read_and_filter(self):
        order = self.client.post("/api/v1/work-orders", headers=self.headers,
                                 json={"customer_id": str(self.customer), "title": "API order"})
        self.assertEqual(order.status_code, 201, order.text)
        created = self._create(work_order_id=order.json()["id"])
        self.assertEqual(created.status_code, 201, created.text)
        fetched = self.client.get(f'/api/v1/invoices/{created.json()["id"]}', headers=self.headers)
        self.assertEqual(fetched.json(), created.json())
        listed = self.client.get("/api/v1/invoices", headers=self.headers, params={"work_order_id": order.json()["id"]})
        self.assertEqual([row["id"] for row in listed.json()], [created.json()["id"]])

    def test_missing_foreign_deleted_parent_rejected_before_create(self):
        for order in (uuid4(), self.foreign_order, self.deleted_order):
            with self.Session() as db:
                before = db.scalar(select(func.count()).select_from(Invoice))
            response = self._create(work_order_id=str(order), subtotal="15")
            self.assertEqual(response.status_code, 400, response.text)
            self.assertEqual(response.json(), {"detail": "Work order not found."})
            with self.Session() as db:
                self.assertEqual(db.scalar(select(func.count()).select_from(Invoice)), before)

    def test_invalid_patch_rejects_entire_mutation(self):
        before = self._read()
        for order in (uuid4(), self.foreign_order, self.deleted_order):
            response = self._patch({"work_order_id": str(order), "notes": "No", "total": "99", "status": "Deleted"})
            self.assertEqual(response.status_code, 400, response.text)
            self.assertEqual(self._read(), before)

    def test_direct_service_validation_and_missing_target(self):
        with self.Session() as db:
            service = InvoiceService()
            with self.assertRaises(WorkOrderReferenceError):
                service.create_invoice(db, self.company, {"work_order_id": self.foreign_order})
            with self.assertRaises(WorkOrderReferenceError):
                service.update_invoice(db, self.company, self.invoice, {"work_order_id": self.deleted_order, "notes": "No"})
            self.assertIsNone(db.get(Invoice, self.invoice).notes)
            self.assertIsNone(service.update_invoice(db, self.company, self.foreign_invoice, {"work_order_id": self.foreign_order}))

    def test_customer_mismatch_and_explicit_fields_remain_authoritative(self):
        response = self._create(work_order_id=str(self.order), total="7.89", status="Paid", notes="Explicit")
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["customer_id"], str(self.other_customer))
        self.assertEqual(Decimal(response.json()["total"]), Decimal("7.89"))
        self.assertEqual(response.json()["status"], "Paid")
        self.assertEqual(response.json()["notes"], "Explicit")

    def test_optional_create_link_and_no_inheritance(self):
        for data in ({}, {"work_order_id": None}, {"work_order_id": str(self.order)}):
            response = self._create(**data)
            self.assertEqual(response.status_code, 201, response.text)
            self.assertEqual(response.json()["customer_id"], str(self.other_customer))
            self.assertEqual(response.json()["work_order_id"], data.get("work_order_id"))
            self.assertIsNone(response.json()["notes"])

    def test_patch_preservation_null_and_reassignment(self):
        for data, expected in (({"notes": "Keep"}, self.order), ({"work_order_id": None}, None),
                               ({"work_order_id": str(self.other_order)}, self.other_order)):
            response = self._patch(data)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["work_order_id"], str(expected) if expected else None)
            self.assertEqual(Decimal(response.json()["total"]), Decimal("12.34"))

    def test_visible_order_statuses_do_not_gain_billing_restrictions(self):
        for order in (self.order, self.other_order, self.cancelled_order):
            response = self._create(work_order_id=str(order))
            self.assertEqual(response.status_code, 201, response.text)

    def test_missing_foreign_deleted_invoice_preserves_404_precedence(self):
        for invoice in (uuid4(), self.foreign_invoice, self.deleted_invoice):
            response = self._patch({"work_order_id": str(uuid4())}, invoice)
            self.assertEqual(response.status_code, 404, response.text)

    def test_decimal_create_calculation_explicit_zero_and_clamp_preserved(self):
        for values, expected in (({"subtotal": "10.25", "discount": "1.10", "tax": "0.35"}, "9.50"),
                                  ({"subtotal": "2", "discount": "3"}, "0"),
                                  ({"subtotal": "15", "total": "0"}, "0"),
                                  ({"subtotal": "15", "total": "7.89"}, "7.89")):
            response = self._create(work_order_id=str(self.order), **values)
            self.assertEqual(response.status_code, 201, response.text)
            self.assertEqual(Decimal(response.json()["total"]), Decimal(expected))

    def test_patch_does_not_recalculate_total(self):
        response = self._patch({"work_order_id": str(self.other_order), "subtotal": "100", "discount": "5"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(Decimal(response.json()["total"]), Decimal("12.34"))

    def test_list_get_delete_isolation_and_no_order_side_effects(self):
        listed = self.client.get("/api/v1/invoices", headers=self.headers)
        self.assertEqual([row["id"] for row in listed.json()], [str(self.invoice)])
        for method in (self.client.get, self.client.delete):
            response = method(f"/api/v1/invoices/{self.foreign_invoice}", headers=self.headers)
            self.assertEqual(response.status_code, 404, response.text)
        response = self.client.delete(f"/api/v1/invoices/{self.invoice}", headers=self.headers)
        self.assertEqual(response.status_code, 204, response.text)
        with self.Session() as db:
            self.assertEqual(db.get(WorkOrder, self.order).status, "Open")

    def test_auth_schema_and_billing_permission_contracts(self):
        self.assertEqual(self.client.post("/api/v1/invoices", json={}).status_code, 401)
        self.assertEqual(self._create(work_order_id="invalid").status_code, 422)
        self.assertEqual(self._patch({"invoice_number": "  "}).status_code, 422)
        with self.Session() as db:
            db.get(User, self.admin).role = "technician"
            db.commit()
        self.assertEqual(self._create(work_order_id=str(self.order)).status_code, 403)

    def test_unexpected_service_value_errors_remain_safe_500(self):
        for action in ("create_invoice", "update_invoice"):
            with patch(f"backend.api.v1.invoices.service.{action}", side_effect=ValueError("private failure")):
                with self.assertLogs("backend.api.errors", level="ERROR"):
                    response = self._create() if action == "create_invoice" else self._patch({"notes": "No"})
                self.assertEqual(response.status_code, 500, response.text)
                self.assertEqual(response.json(), {"detail": "Internal Server Error"})


if __name__ == "__main__":
    unittest.main()
