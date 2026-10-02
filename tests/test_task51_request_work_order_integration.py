"""Owner-approved optional Service Request link, using disposable API data."""
import os
import tempfile
import unittest
from uuid import uuid4

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
from backend.models.service_request import ServiceRequest
from backend.models.work_order import WorkOrder
from backend.services.work_order import WorkOrderService


class Task51RequestWorkOrderTests(unittest.TestCase):
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
        self.company, self.other_company, self.customer, self.other_customer, self.foreign_customer = [uuid4() for _ in range(5)]
        self.asset, self.other_asset, self.request, self.foreign_request, self.deleted_request = [uuid4() for _ in range(5)]
        self.order, self.foreign_order, self.admin = [uuid4() for _ in range(3)]
        with self.Session() as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            db.add_all([Company(id=self.company, name="A", status="active"),
                        Company(id=self.other_company, name="B", status="active")])
            db.flush()
            db.add_all([Customer(id=self.customer, company_id=self.company, name="A1"),
                        Customer(id=self.other_customer, company_id=self.company, name="A2"),
                        Customer(id=self.foreign_customer, company_id=self.other_company, name="B1"),
                        User(id=self.admin, company_id=self.company, email="admin@example.com", full_name="Admin",
                             role="admin", password_hash=self.password_hash)])
            db.flush()
            db.add_all([Asset(id=self.asset, company_id=self.company, customer_id=self.customer, asset_type="A1"),
                        Asset(id=self.other_asset, company_id=self.company, customer_id=self.other_customer, asset_type="A2")])
            db.flush()
            db.add_all([ServiceRequest(id=self.request, company_id=self.company, customer_id=self.customer,
                                       asset_id=self.asset, title="Request"),
                        ServiceRequest(id=self.foreign_request, company_id=self.other_company,
                                       customer_id=self.foreign_customer, title="Foreign"),
                        ServiceRequest(id=self.deleted_request, company_id=self.company,
                                       customer_id=self.customer, title="Deleted", status="Deleted")])
            db.flush()
            db.add_all([WorkOrder(id=self.order, company_id=self.company, customer_id=self.other_customer,
                                  asset_id=self.other_asset, service_request_id=self.request, title="Order"),
                        WorkOrder(id=self.foreign_order, company_id=self.other_company,
                                  customer_id=self.foreign_customer, title="Foreign")])
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

    def _create(self, **extra):
        return self.client.post("/api/v1/work-orders", headers=self.headers,
                                json={"customer_id": str(self.other_customer), "title": "New order", **extra})

    def _patch(self, data, order_id=None):
        return self.client.patch(f"/api/v1/work-orders/{order_id or self.order}", headers=self.headers, json=data)

    def _count(self):
        with self.Session() as db:
            return db.scalar(select(func.count()).select_from(WorkOrder))

    def test_api_request_creation_to_work_order_read_and_filter(self):
        request = self.client.post("/api/v1/service-requests", headers=self.headers,
                                   json={"customer_id": str(self.customer), "asset_id": str(self.asset), "title": "New request"})
        self.assertEqual(request.status_code, 201, request.text)
        created = self._create(service_request_id=request.json()["id"], asset_id=str(self.other_asset))
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(created.json()["customer_id"], str(self.other_customer))
        self.assertEqual(created.json()["asset_id"], str(self.other_asset))
        self.assertEqual(created.json()["service_request_id"], request.json()["id"])
        fetched = self.client.get(f'/api/v1/work-orders/{created.json()["id"]}', headers=self.headers)
        self.assertEqual(fetched.status_code, 200, fetched.text)
        self.assertEqual(fetched.json(), created.json())
        listed = self.client.get("/api/v1/work-orders", headers=self.headers,
                                  params={"service_request_id": request.json()["id"]})
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual([order["id"] for order in listed.json()], [created.json()["id"]])

    def test_create_omitted_request_preserves_direct_work_order(self):
        response = self._create()
        self.assertEqual(response.status_code, 201, response.text)
        self.assertIsNone(response.json()["service_request_id"])

    def test_create_explicit_null_request_preserves_direct_work_order(self):
        response = self._create(service_request_id=None)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertIsNone(response.json()["service_request_id"])

    def test_link_does_not_inherit_asset_or_technician(self):
        response = self._create(service_request_id=str(self.request))
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["customer_id"], str(self.other_customer))
        self.assertIsNone(response.json()["asset_id"])
        self.assertIsNone(response.json()["assigned_technician_id"])

    def test_unknown_foreign_and_deleted_links_rejected_without_creation(self):
        for request_id in [uuid4(), self.foreign_request, self.deleted_request]:
            with self.subTest(request_id=request_id):
                before = self._count()
                response = self._create(service_request_id=str(request_id))
                self.assertEqual(response.status_code, 400, response.text)
                self.assertEqual(response.json(), {"detail": "Service request not found."})
                self.assertEqual(self._count(), before)

    def test_invalid_patch_link_prevents_entire_mutation(self):
        for request_id in [uuid4(), self.foreign_request, self.deleted_request]:
            with self.subTest(request_id=request_id):
                response = self._patch({"service_request_id": str(request_id), "title": "Changed", "status": "Cancelled"})
                self.assertEqual(response.status_code, 400, response.text)
                with self.Session() as db:
                    order = db.get(WorkOrder, self.order)
                    self.assertEqual(order.title, "Order")
                    self.assertEqual(order.status, "Open")
                    self.assertEqual(order.service_request_id, self.request)

    def test_valid_patch_link_preserves_explicit_mismatching_fields(self):
        response = self._patch({"service_request_id": str(self.request), "customer_id": str(self.other_customer),
                               "asset_id": str(self.other_asset)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["customer_id"], str(self.other_customer))
        self.assertEqual(response.json()["asset_id"], str(self.other_asset))

    def test_patch_explicit_null_detaches_optional_request(self):
        response = self._patch({"service_request_id": None})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["service_request_id"])
        self.assertEqual(response.json()["customer_id"], str(self.other_customer))

    def test_patch_omitted_request_preserves_existing_link(self):
        response = self._patch({"notes": "Note"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["service_request_id"], str(self.request))

    def test_missing_and_hidden_targets_keep_404_precedence(self):
        for order_id in [uuid4(), self.foreign_order]:
            with self.subTest(order_id=order_id):
                response = self._patch({"service_request_id": str(uuid4())}, order_id)
                self.assertEqual(response.status_code, 404, response.text)
                self.assertEqual(response.json(), {"detail": "work_orders record not found"})

    def test_other_tenant_request_filter_cannot_expose_work_orders(self):
        response = self.client.get("/api/v1/work-orders", headers=self.headers,
                                   params={"service_request_id": str(self.foreign_request)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), [])

    def test_direct_service_rejects_foreign_request_before_create(self):
        before = self._count()
        with self.Session() as db:
            with self.assertRaisesRegex(ValueError, "Service request not found"):
                WorkOrderService().create_work_order(db, self.company,
                                                     {"customer_id": self.customer, "title": "New",
                                                      "service_request_id": self.foreign_request})
        self.assertEqual(self._count(), before)

    def test_direct_service_rejects_invalid_request_before_update(self):
        with self.Session() as db:
            with self.assertRaisesRegex(ValueError, "Service request not found"):
                WorkOrderService().update_work_order(db, self.company, self.order,
                                                     {"service_request_id": self.deleted_request, "title": "Changed"})
            self.assertEqual(db.get(WorkOrder, self.order).title, "Order")

    def test_missing_authentication_preserves_bearer_challenge(self):
        response = self.client.post("/api/v1/work-orders", json={"customer_id": str(self.customer), "title": "New"})
        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(response.headers["www-authenticate"], "Bearer")
