"""Persistent authentication tested against disposable storage only."""
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

import test_task46_auth as fixture
from backend.main import app
from backend.models.auth_session import AuthSession
from backend.models.company import Company
from backend.models.user import User
from backend.services.auth_sessions import credential_hash
from backend.services.auth_sessions import issue_session
from uuid import uuid4


class PersistentSessionTests(fixture.Task46AuthTests):
    def setUp(self):
        with self.Session() as db:
            db.query(AuthSession).delete()
            db.commit()
        super().setUp()

    def session(self, email="admin@example.com"):
        response = self.client.post("/api/v1/auth/sessions", data={"username": email, "password": "Password123!"})
        self.assertEqual(response.status_code, 200)
        return response.json()["access_token"]

    def headers(self, credential):
        return {"Authorization": f"Bearer {credential}"}

    def test_hash_only_and_no_time_expiry_after_connection_restart(self):
        credential = self.session()
        with self.Session() as db:
            stored = db.query(AuthSession).one()
            self.assertEqual(stored.secret_hash, credential_hash(credential))
            self.assertNotIn(credential, repr(stored.__dict__))
            stored.created_at = datetime(1990, 1, 1, tzinfo=timezone.utc)
            db.commit()
        self.engine.dispose()
        with TestClient(app) as restarted:
            response = restarted.get("/api/v1/auth/me", headers=self.headers(credential))
        self.assertEqual(response.status_code, 200)

    def test_logout_revocation_reuse_and_idempotence(self):
        credential = self.session()
        headers = self.headers(credential)
        self.assertEqual(self.client.post("/api/v1/auth/sessions/logout", headers=headers).status_code, 204)
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=headers).status_code, 401)
        self.assertEqual(self.client.post("/api/v1/auth/sessions/logout", headers=headers).status_code, 204)
        with self.Session() as db:
            self.assertIsNotNone(db.query(AuthSession).one().revoked_at)

    def test_disabled_deleted_and_company_inactive(self):
        for change in ("disabled", "deleted", "company"):
            with self.subTest(change=change):
                self.setUp()
                credential = self.session()
                with self.Session() as db:
                    user = db.query(User).filter_by(email="admin@example.com").one()
                    if change == "disabled": user.is_active = False
                    elif change == "deleted": db.delete(user)
                    else: db.get(Company, self.company_a).status = "inactive"
                    db.commit()
                self.assertEqual(self.client.get("/api/v1/auth/me", headers=self.headers(credential)).status_code, 401)

    def test_current_permissions_tenant_isolation_and_security_revocation(self):
        credential = self.session()
        headers = {**self.headers(credential), "X-Company-ID": str(self.company_b)}
        self.assertEqual([row["name"] for row in self.client.get("/api/v1/customers", headers=headers).json()], ["A Customer"])
        with self.Session() as db:
            session = db.query(AuthSession).one()
            session_id = session.id
            user = db.query(User).filter_by(email="admin@example.com").one()
            user.role = "technician"
            db.commit()
        self.assertEqual(self.client.get("/api/v1/expenses", headers=headers).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/auth/sessions/{session_id}", headers=headers).status_code, 403)
        with self.Session() as db:
            db.query(User).filter_by(email="admin@example.com").one().role = "admin"
            db.query(AuthSession).one().company_id = self.company_b
            db.commit()
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=headers).status_code, 401)
        with self.Session() as db:
            db.query(AuthSession).one().company_id = self.company_a
            db.commit()
        self.assertEqual(self.client.delete(f"/api/v1/auth/sessions/{session_id}", headers=headers).status_code, 204)
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=headers).status_code, 401)

    def test_session_store_failure_fails_closed_without_invalidating_session(self):
        credential = self.session()
        with patch("backend.core.authentication.resolve_session", side_effect=OperationalError("unavailable", {}, Exception())):
            with TestClient(app, raise_server_exceptions=False) as client:
                self.assertEqual(client.get("/api/v1/auth/me", headers=self.headers(credential)).status_code, 500)
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=self.headers(credential)).status_code, 200)

    def test_independent_sessions_and_jwt_contract(self):
        first, second = self.session(), self.session()
        self.assertNotEqual(first, second)
        self.client.post("/api/v1/auth/sessions/logout", headers=self.headers(first))
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=self.headers(second)).status_code, 200)
        jwt = self._login("admin@example.com")
        self.assertEqual(len(jwt.split(".")), 3)
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=self.headers(jwt)).status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=self.headers("axs_invalid")).status_code, 401)

    def test_admin_cannot_revoke_another_company_session(self):
        credential = self.session()
        with self.Session() as db:
            foreign = User(id=uuid4(), company_id=self.company_b, email="foreign@example.test", full_name="Foreign", role="admin", password_hash="unused")
            db.add(foreign); db.flush()
            foreign_credential = issue_session(db, foreign)
            db.commit()
            foreign_id = db.query(AuthSession).filter_by(secret_hash=credential_hash(foreign_credential)).one().id
        self.assertEqual(self.client.delete(f"/api/v1/auth/sessions/{foreign_id}", headers=self.headers(credential)).status_code, 204)
        self.assertEqual(self.client.get("/api/v1/auth/me", headers=self.headers(foreign_credential)).status_code, 200)
