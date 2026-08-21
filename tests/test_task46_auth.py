"""Task 46 authentication and tenant-isolation tests."""
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
from backend.core.security import create_access_token, hash_password
from backend.main import app
from backend.models.base import Base
from backend.models.company import Company
from backend.models.customer import Customer
from backend.models.user import User


class Task46AuthTests(unittest.TestCase):
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
            db.query(Customer).delete()
            db.query(User).delete()
            db.query(Company).delete()
            company_a = Company(id=uuid4(), name="Company A", status="active")
            company_b = Company(id=uuid4(), name="Company B", status="active")
            inactive_company = Company(id=uuid4(), name="Inactive Company", status="inactive")
            admin = User(
                id=uuid4(), company=company_a, email="admin@example.com", full_name="Admin",
                password_hash=hash_password("Password123!"), role="admin",
            )
            manager = User(
                id=uuid4(), company=company_a, email="manager@example.com", full_name="Manager",
                password_hash=hash_password("Password123!"), role="manager",
            )
            technician = User(
                id=uuid4(), company=company_a, email="technician@example.com", full_name="Technician",
                password_hash=hash_password("Password123!"), role="technician",
            )
            inactive_user_active_company = User(
                id=uuid4(), company=company_a, email="inactive-user@example.com", full_name="Inactive User",
                password_hash=hash_password("Password123!"), role="admin", is_active=False,
            )
            inactive_company_user = User(
                id=uuid4(), company=inactive_company, email="inactive-company@example.com", full_name="Inactive Company User",
                password_hash=hash_password("Password123!"), role="admin",
            )
            db.add_all(
                [
                    company_a,
                    company_b,
                    inactive_company,
                    admin,
                    manager,
                    technician,
                    admin,
                    manager,
                    technician,
                    inactive_user_active_company,
                    inactive_company_user,
                    Customer(id=uuid4(), company_id=company_a.id, name="A Customer"),
                    Customer(id=uuid4(), company_id=company_b.id, name="B Customer"),
                ]
            )
            db.commit()
            self.company_a = company_a.id
            self.company_b = company_b.id

        def override_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

    def test_login_and_me(self):
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "ADMIN@example.com", "password": "Password123!"},
        )
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]

        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["company_id"], str(self.company_a))
        self.assertEqual(response.json()["role"], "admin")
        self.assertIn("expense:manage", response.json()["permissions"])
        self.assertIn("report:read", response.json()["permissions"])

    def test_company_header_cannot_switch_tenant(self):
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "admin@example.com", "password": "Password123!"},
        )
        token = response.json()["access_token"]

        response = self.client.get(
            "/api/v1/customers",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Company-ID": str(self.company_b),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["name"] for row in response.json()], ["A Customer"])


    def _login(self, email: str) -> str:
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "Password123!"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["access_token"]

    def test_inactive_company_blocks_login(self):
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "inactive-company@example.com", "password": "Password123!"},
        )
        self.assertEqual(response.status_code, 401)

    def test_inactive_company_revokes_existing_token(self):
        token = self._login("admin@example.com")
        with self.Session() as db:
            company = db.get(Company, self.company_a)
            company.status = "inactive"
            db.commit()

        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 401)

    def test_inactive_user_blocks_login_when_company_is_active(self):
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "inactive-user@example.com", "password": "Password123!"},
        )
        self.assertEqual(response.status_code, 401)

    def test_expired_jwt_is_rejected(self):
        token = create_access_token(self._user_id("admin@example.com"), expires_minutes=-1)
        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 401)

    def test_invalid_and_malformed_tokens_are_rejected(self):
        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer definitely-not-a-jwt"},
        )
        self.assertEqual(response.status_code, 401)

        token = create_access_token("not-a-uuid")
        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 401)

    def test_role_permissions_are_enforced(self):
        manager_token = self._login("manager@example.com")
        technician_token = self._login("technician@example.com")

        response = self.client.get(
            "/api/v1/expenses",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            "/api/v1/expenses",
            headers={"Authorization": f"Bearer {technician_token}"},
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            "/api/v1/audit-logs",
            headers={"Authorization": f"Bearer {technician_token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_jwt_permissions_cannot_elevate_database_role(self):
        token = create_access_token(
            self._user_id("technician@example.com"),
            role="admin",
            permissions=["expense:manage", "report:read"],
        )
        response = self.client.get(
            "/api/v1/expenses",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def _user_id(self, email: str):
        with self.Session() as db:
            user = db.query(User).filter(User.email == email).one()
            return str(user.id)

    def test_invalid_password_is_rejected(self):
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "admin@example.com", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
