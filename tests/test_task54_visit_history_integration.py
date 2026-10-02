"""OD-16 Service Visit links, tested with disposable SQLite and real foreign keys."""
import os
import tempfile
import unittest
from datetime import datetime
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
from backend.models.asset import Asset
from backend.models.user import User
from backend.models.work_order import WorkOrder
from backend.models.service_visit import ServiceVisit
from backend.models.service_history import ServiceHistory
from backend.services.service_history import ServiceHistoryService, ServiceVisitReferenceError


class Task54VisitHistoryTests(unittest.TestCase):
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
        self.asset, self.other_asset, self.order, self.other_order, self.foreign_order = [uuid4() for _ in range(5)]
        self.visit, self.other_visit, self.foreign_visit, self.deleted_visit, self.cancelled_visit = [uuid4() for _ in range(5)]
        self.history, self.foreign_history, self.deleted_history, self.admin, self.technician = [uuid4() for _ in range(5)]
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
            db.add_all([Asset(id=self.asset, company_id=self.company, customer_id=self.customer, asset_type="A1"),
                        Asset(id=self.other_asset, company_id=self.company, customer_id=self.other_customer, asset_type="A2")])
            db.flush()
            db.add_all([WorkOrder(id=self.order, company_id=self.company, customer_id=self.customer,
                                  asset_id=self.asset, title="A1"),
                        WorkOrder(id=self.other_order, company_id=self.company, customer_id=self.other_customer,
                                  asset_id=self.other_asset, title="A2"),
                        WorkOrder(id=self.foreign_order, company_id=self.foreign_company,
                                  customer_id=self.foreign_customer, title="B1")])
            db.flush()
            for visit_id, company, order, customer, status in (
                (self.visit, self.company, self.order, self.customer, "Completed"),
                (self.other_visit, self.company, self.order, self.customer, "Planned"),
                (self.foreign_visit, self.foreign_company, self.foreign_order, self.foreign_customer, "Completed"),
                (self.deleted_visit, self.company, self.order, self.customer, "Deleted"),
                (self.cancelled_visit, self.company, self.order, self.customer, "Cancelled"),
            ):
                db.add(ServiceVisit(id=visit_id, company_id=company, work_order_id=order, customer_id=customer,
                                    technician_id=self.technician, asset_id=self.asset if company == self.company else None,
                                    status=status, notes="Visit notes"))
            db.flush()
            for history_id, company, customer, visit_id, status in (
                (self.history, self.company, self.other_customer, self.visit, "Active"),
                (self.foreign_history, self.foreign_company, self.foreign_customer, self.foreign_visit, "Active"),
                (self.deleted_history, self.company, self.customer, self.visit, "Deleted"),
            ):
                db.add(ServiceHistory(id=history_id, company_id=company, customer_id=customer,
                                      service_visit_id=visit_id, service_type="Repair", summary="Original",
                                      service_date=datetime(2026, 10, 2, 12), status=status))
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
        return self.client.post("/api/v1/service-history", headers=self.headers,
                                json={"customer_id": str(self.other_customer), "service_type": "Repair",
                                      "service_date": "2026-10-02T12:00:00", "summary": "Recorded", **data})

    def _patch(self, data, history_id=None):
        return self.client.patch(f"/api/v1/service-history/{history_id or self.history}",
                                 headers=self.headers, json=data)

    def _count(self):
        with self.Session() as db:
            return db.scalar(select(func.count()).select_from(ServiceHistory))

    def _read(self):
        with self.Session() as db:
            record = db.get(ServiceHistory, self.history)
            return record.service_visit_id, record.summary, record.notes, record.status

    def test_api_visit_creation_to_linked_history_read_and_repository_filter(self):
        visit = self.client.post("/api/v1/service-visits", headers=self.headers,
                                 json={"work_order_id": str(self.other_order), "customer_id": str(self.other_customer)})
        self.assertEqual(visit.status_code, 201, visit.text)
        history = self._create(service_visit_id=visit.json()["id"])
        self.assertEqual(history.status_code, 201, history.text)
        read = self.client.get(f'/api/v1/service-history/{history.json()["id"]}', headers=self.headers)
        self.assertEqual(read.json(), history.json())
        with self.Session() as db:
            linked = ServiceHistoryService().list_history(db, self.company, service_visit_id=UUID(visit.json()["id"]))
            self.assertEqual([str(row.id) for row in linked], [history.json()["id"]])

    def test_missing_foreign_deleted_visit_rejected_before_create(self):
        for visit in (uuid4(), self.foreign_visit, self.deleted_visit):
            with self.subTest(visit=visit):
                before = self._count()
                response = self._create(service_visit_id=str(visit))
                self.assertEqual(response.status_code, 400, response.text)
                self.assertEqual(response.json(), {"detail": "Service visit not found."})
                self.assertEqual(self._count(), before)

    def test_invalid_patch_rejects_entire_mutation(self):
        before = self._read()
        for visit in (uuid4(), self.foreign_visit, self.deleted_visit):
            response = self._patch({"service_visit_id": str(visit), "summary": "Changed", "notes": "No", "status": "Deleted"})
            self.assertEqual(response.status_code, 400, response.text)
            self.assertEqual(self._read(), before)

    def test_direct_service_validates_before_create_and_update(self):
        with self.Session() as db:
            service = ServiceHistoryService()
            before = db.scalar(select(func.count()).select_from(ServiceHistory))
            with self.assertRaises(ServiceVisitReferenceError):
                service.create_history(db, self.company, {"service_visit_id": self.foreign_visit})
            self.assertEqual(db.scalar(select(func.count()).select_from(ServiceHistory)), before)
            with self.assertRaises(ServiceVisitReferenceError):
                service.update_history(db, self.company, self.history,
                                       {"service_visit_id": self.deleted_visit, "summary": "No"})
            self.assertEqual(db.get(ServiceHistory, self.history).summary, "Original")

    def test_explicit_mismatching_relationships_and_other_fields_remain_authoritative(self):
        technician = str(uuid4())
        response = self._create(service_visit_id=str(self.visit), asset_id=str(self.other_asset),
                                work_order_id=str(self.other_order), technician_id=technician,
                                notes="History notes", service_type="  Inspection  ", summary="  Explicit  ")
        self.assertEqual(response.status_code, 201, response.text)
        for field, expected in (("customer_id", str(self.other_customer)), ("asset_id", str(self.other_asset)),
                                ("work_order_id", str(self.other_order)), ("technician_id", technician),
                                ("notes", "History notes"), ("service_type", "Inspection"), ("summary", "Explicit")):
            self.assertEqual(response.json()[field], expected)
        response = self._patch({"service_visit_id": str(self.other_visit), "customer_id": str(self.other_customer),
                                "asset_id": str(self.other_asset), "work_order_id": str(self.other_order)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["customer_id"], str(self.other_customer))
        self.assertEqual(response.json()["asset_id"], str(self.other_asset))
        self.assertEqual(response.json()["work_order_id"], str(self.other_order))

    def test_link_does_not_inherit_optional_fields(self):
        response = self._create(service_visit_id=str(self.visit))
        self.assertEqual(response.status_code, 201, response.text)
        for field in ("asset_id", "work_order_id", "technician_id", "notes"):
            self.assertIsNone(response.json()[field])

    def test_optional_create_link_omission_and_null(self):
        for data in ({}, {"service_visit_id": None}):
            response = self._create(**data)
            self.assertEqual(response.status_code, 201, response.text)
            self.assertIsNone(response.json()["service_visit_id"])

    def test_patch_omission_detachment_and_valid_reassignment(self):
        response = self._patch({"notes": "Updated"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["service_visit_id"], str(self.visit))
        response = self._patch({"service_visit_id": None})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["service_visit_id"])
        response = self._patch({"service_visit_id": str(self.other_visit)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["service_visit_id"], str(self.other_visit))

    def test_visible_planned_cancelled_visits_do_not_gain_status_restrictions(self):
        for visit in (self.other_visit, self.cancelled_visit):
            response = self._create(service_visit_id=str(visit))
            self.assertEqual(response.status_code, 201, response.text)

    def test_missing_foreign_deleted_target_preserves_404_precedence(self):
        for history in (uuid4(), self.foreign_history, self.deleted_history):
            response = self._patch({"service_visit_id": str(uuid4())}, history)
            self.assertEqual(response.status_code, 404, response.text)
        with self.Session() as db:
            self.assertIsNone(ServiceHistoryService().update_history(db, self.company, self.foreign_history,
                                                                    {"service_visit_id": self.foreign_visit}))

    def test_get_list_delete_tenant_isolation_and_soft_delete(self):
        listed = self.client.get("/api/v1/service-history", headers=self.headers)
        self.assertEqual([row["id"] for row in listed.json()], [str(self.history)])
        for method in (self.client.get, self.client.delete):
            response = method(f"/api/v1/service-history/{self.foreign_history}", headers=self.headers)
            self.assertEqual(response.status_code, 404, response.text)
        response = self.client.delete(f"/api/v1/service-history/{self.history}", headers=self.headers)
        self.assertEqual(response.status_code, 204, response.text)
        with self.Session() as db:
            self.assertEqual(db.get(ServiceHistory, self.history).status, "Deleted")
            self.assertEqual(db.get(ServiceVisit, self.visit).status, "Completed")

    def test_authentication_and_schema_validation_still_precede_service(self):
        response = self.client.post("/api/v1/service-history", json={})
        self.assertEqual(response.status_code, 401, response.text)
        response = self._create(service_visit_id="bad-uuid")
        self.assertEqual(response.status_code, 422, response.text)
        response = self._patch({"summary": "  ", "service_visit_id": str(uuid4())})
        self.assertEqual(response.status_code, 422, response.text)

    def test_unexpected_value_error_remains_safe_500(self):
        for action in ("create_history", "update_history"):
            with patch(f"backend.api.v1.service_history.service.{action}", side_effect=ValueError("private internal failure")):
                with self.assertLogs("backend.api.errors", level="ERROR"):
                    response = self._create() if action == "create_history" else self._patch({"notes": "No"})
                self.assertEqual(response.status_code, 500, response.text)
                self.assertEqual(response.json(), {"detail": "Internal Server Error"})


if __name__ == "__main__":
    unittest.main()
