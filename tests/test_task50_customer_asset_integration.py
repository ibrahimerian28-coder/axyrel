"""Customer-to-Asset workflow on an isolated application/disposable database."""
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
from backend.core.tenant_isolation import TenantScopeRequiredError
from backend.main import app as application
from backend.models.base import Base
from backend.models.company import Company
from backend.models.customer import Customer
from backend.models.asset import Asset
from backend.models.user import User
from backend.services.asset import AssetService


class Task50CustomerAssetTests(unittest.TestCase):
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
        self.company, self.other_company = uuid4(), uuid4()
        self.customer, self.second_customer, self.foreign_customer, self.deleted_customer = [uuid4() for _ in range(4)]
        self.asset, self.foreign_asset, self.admin, self.tech = [uuid4() for _ in range(4)]
        with self.Session() as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            db.add_all([Company(id=self.company, name="A", status="active"),
                        Company(id=self.other_company, name="B", status="active")])
            db.flush()
            db.add_all([Customer(id=self.customer, company_id=self.company, name="A1"),
                        Customer(id=self.second_customer, company_id=self.company, name="A2"),
                        Customer(id=self.foreign_customer, company_id=self.other_company, name="B1"),
                        Customer(id=self.deleted_customer, company_id=self.company, name="Deleted", status="Deleted"),
                        User(id=self.admin, company_id=self.company, email="admin@example.com", full_name="Admin",
                             role="admin", password_hash=self.password_hash),
                        User(id=self.tech, company_id=self.company, email="tech@example.com", full_name="Tech",
                             role="technician", password_hash=self.password_hash)])
            db.flush()
            db.add_all([Asset(id=self.asset, company_id=self.company, customer_id=self.customer, asset_type="Pump"),
                        Asset(id=self.foreign_asset, company_id=self.other_company,
                              customer_id=self.foreign_customer, asset_type="Foreign")])
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

    def _create(self, customer_id):
        return self.client.post("/api/v1/assets", headers=self.headers,
                                json={"customer_id": str(customer_id), "asset_type": "Boiler"})

    def _patch(self, data, asset_id=None):
        return self.client.patch(f"/api/v1/assets/{asset_id or self.asset}", headers=self.headers, json=data)

    def _count(self):
        with self.Session() as db:
            return db.scalar(select(func.count()).select_from(Asset))

    def _assert_parent_unchanged(self):
        with self.Session() as db:
            asset = db.get(Asset, self.asset)
            self.assertEqual(asset.customer_id, self.customer)
            self.assertEqual(asset.asset_type, "Pump")

    def test_customer_create_to_asset_create_read_and_filter(self):
        parent = self.client.post("/api/v1/customers", headers=self.headers, json={"name": "New customer"})
        self.assertEqual(parent.status_code, 201, parent.text)
        response = self._create(parent.json()["id"])
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["customer_id"], parent.json()["id"])
        self.assertEqual(response.json()["company_id"], str(self.company))
        fetched = self.client.get(f'/api/v1/assets/{response.json()["id"]}', headers=self.headers)
        self.assertEqual(fetched.status_code, 200, fetched.text)
        self.assertEqual(fetched.json(), response.json())
        listed = self.client.get("/api/v1/assets", headers=self.headers, params={"customer_id": parent.json()["id"]})
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual([a["id"] for a in listed.json()], [response.json()["id"]])

    def test_multiple_assets_remain_customer_scoped(self):
        created = self._create(self.customer)
        self.assertEqual(created.status_code, 201, created.text)
        listed = self.client.get("/api/v1/assets", headers=self.headers, params={"customer_id": str(self.customer)})
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual({a["id"] for a in listed.json()}, {str(self.asset), created.json()["id"]})

    def test_other_tenant_customer_filter_cannot_expose_assets(self):
        response = self.client.get("/api/v1/assets", headers=self.headers,
                                   params={"customer_id": str(self.foreign_customer)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), [])

    def test_create_unknown_customer_rejected_without_persistence(self):
        before = self._count()
        response = self._create(uuid4())
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json(), {"detail": "Customer not found."})
        self.assertEqual(self._count(), before)

    def test_create_foreign_customer_rejected_without_persistence(self):
        before = self._count()
        response = self._create(self.foreign_customer)
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json(), {"detail": "Customer not found."})
        self.assertEqual(self._count(), before)

    def test_create_deleted_customer_rejected_without_persistence(self):
        before = self._count()
        self.assertEqual(self._create(self.deleted_customer).status_code, 400)
        self.assertEqual(self._count(), before)

    def test_valid_customer_reassignment_preserved(self):
        response = self._patch({"customer_id": str(self.second_customer)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["customer_id"], str(self.second_customer))

    def test_foreign_customer_patch_rejects_entire_mutation(self):
        response = self._patch({"customer_id": str(self.foreign_customer), "asset_type": "Changed"})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json(), {"detail": "Customer not found."})
        self._assert_parent_unchanged()

    def test_unknown_customer_patch_rejects_entire_mutation(self):
        self.assertEqual(self._patch({"customer_id": str(uuid4()), "asset_type": "Changed"}).status_code, 400)
        self._assert_parent_unchanged()

    def test_null_customer_patch_cannot_remove_required_owner(self):
        response = self._patch({"customer_id": None, "asset_type": "Changed"})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json(), {"detail": "Customer is required."})
        self._assert_parent_unchanged()

    def test_patch_without_customer_preserves_relationship(self):
        response = self._patch({"notes": "Updated"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["customer_id"], str(self.customer))
        self.assertEqual(response.json()["notes"], "Updated")

    def test_hidden_asset_404_precedes_parent_validation(self):
        response = self._patch({"customer_id": None}, self.foreign_asset)
        self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(response.json(), {"detail": "assets record not found"})

    def test_missing_asset_404_precedes_parent_validation(self):
        self.assertEqual(self._patch({"customer_id": None}, uuid4()).status_code, 404)

    def test_asset_create_requires_authentication(self):
        response = self.client.post("/api/v1/assets", json={"customer_id": str(self.customer), "asset_type": "Pump"})
        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_technician_cannot_create_assets(self):
        response = self.client.post("/api/v1/assets",
                                    headers={"Authorization": f"Bearer {create_access_token(str(self.tech))}"},
                                    json={"customer_id": str(self.customer), "asset_type": "Pump"})
        self.assertEqual(response.status_code, 403, response.text)
        self.assertNotIn("www-authenticate", response.headers)

    def test_direct_service_create_enforces_parent_tenant(self):
        before = self._count()
        with self.Session() as db:
            with self.assertRaisesRegex(ValueError, "Customer not found"):
                AssetService().create_asset(db, self.company, {"customer_id": self.foreign_customer, "asset_type": "Pump"})
        self.assertEqual(self._count(), before)

    def test_direct_service_update_enforces_parent_before_mutation(self):
        with self.Session() as db:
            with self.assertRaisesRegex(ValueError, "Customer not found"):
                AssetService().update_asset(db, self.company, self.asset,
                                            {"customer_id": self.deleted_customer, "asset_type": "Changed"})
            self.assertEqual(db.get(Asset, self.asset).asset_type, "Pump")
            self.assertEqual(db.get(Asset, self.asset).customer_id, self.customer)
        self._assert_parent_unchanged()

    def test_direct_service_requires_explicit_company_scope(self):
        with self.Session() as db:
            with self.assertRaises(TenantScopeRequiredError):
                AssetService().create_asset(db, None, {"customer_id": self.customer, "asset_type": "Pump"})

    def test_customer_soft_delete_does_not_cascade_or_block_unrelated_patch(self):
        response = self.client.delete(f"/api/v1/customers/{self.customer}", headers=self.headers)
        self.assertEqual(response.status_code, 204, response.text)
        patched = self._patch({"notes": "Historical asset"})
        self.assertEqual(patched.status_code, 200, patched.text)
        self.assertEqual(patched.json()["customer_id"], str(self.customer))
