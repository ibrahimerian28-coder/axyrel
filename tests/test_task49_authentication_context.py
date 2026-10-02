"""Task 49 context compatibility using an isolated app and disposable database."""
import os
import tempfile
import unittest
from typing import Annotated
from unittest.mock import patch
from uuid import uuid4

DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
DB_FILE.close()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_FILE.name}"
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes-123456"

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.models  # noqa: F401  # register disposable ORM tables
from backend.api.dependencies import CompanyID, DBSession, get_company_id
from backend.api.v1 import router as api_v1_router
from backend.core import authentication
from backend.core.authentication import AuthContext, CurrentAuthContext, CurrentUser
from backend.core.config import settings
from backend.core.authorization import Permission, permissions_for_role, require_permission
from backend.core.tenant import get_company_context, set_company_context
from backend.core.database import get_db
from backend.core.security import ALGORITHM, create_access_token, hash_password
from backend.main import app as application
from backend.models.base import Base
from backend.models.company import Company
from backend.models.user import User


class Task49AuthenticationContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(f"sqlite:///{DB_FILE.name}", connect_args={"check_same_thread": False})
        cls.Session = sessionmaker(bind=cls.engine, autoflush=False)
        Base.metadata.create_all(cls.engine)
        cls.password_hash = hash_password("Password123!")

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        os.unlink(DB_FILE.name)

    def setUp(self):
        with self.Session() as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            company = Company(id=uuid4(), name="Context Company", status="active")
            other_company = Company(id=uuid4(), name="Other Context Company", status="active")
            user = User(id=uuid4(), company=company, email="admin@example.com", full_name="Admin",
                        password_hash=self.password_hash, role="admin")
            other_user = User(id=uuid4(), company=other_company, email="tech@example.com", full_name="Tech",
                              password_hash=self.password_hash, role="technician")
            db.add_all([company, other_company, user, other_user])
            db.commit()
            self.user_id, self.company_id = user.id, company.id
            self.other_user_id, self.other_company_id = other_user.id, other_company.id
        self.token = create_access_token(str(self.user_id))
        self.app = FastAPI()
        self.app.exception_handlers.update(application.exception_handlers)
        self.app.include_router(api_v1_router, prefix="/api/v1")

        def override_db():
            with self.Session() as db:
                yield db

        self.app.dependency_overrides[get_db] = override_db

        @self.app.get("/context")
        def context_probe(context: CurrentAuthContext, user: CurrentUser, db: DBSession):
            return {
                "context_type": isinstance(context, AuthContext),
                "orm_user": isinstance(user, User),
                "same_user": context.user is user,
                "session_identity": db.get(User, user.id) is context.user,
                "user_id": str(user.id),
                "company_id": str(context.company_id),
                "role": user.role,
            }

        @self.app.get("/projections")
        def projection_probe(context: CurrentAuthContext, company_id: CompanyID,
                             allowed_user: Annotated[User, Depends(require_permission(Permission.CUSTOMER_READ))],
                             user: CurrentUser):
            return {
                "company_id": str(company_id),
                "user_id": str(context.user.id),
                "permission_user_same": allowed_user is context.user,
                "current_user_same": user is context.user,
                "orm_guard_user": isinstance(allowed_user, User),
            }

        self.client = TestClient(self.app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)

    def _context(self, token=None, **kwargs):
        headers = {"Authorization": f"Bearer {self.token if token is None else token}"}
        headers.update(kwargs.pop("headers", {}))
        return self.client.get("/context", headers=headers, **kwargs)

    def _assert_401(self, response, detail):
        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(response.json(), {"detail": detail})
        self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def _assert_inactive(self, response):
        self._assert_401(response, "User is inactive, company is inactive, or user no longer exists")

    def _set_role(self, role):
        with self.Session() as db:
            db.get(User, self.user_id).role = role
            db.commit()

    def test_valid_token_constructs_auth_context(self):
        response = self._context()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["context_type"])
        self.assertEqual(response.json()["user_id"], str(self.user_id))

    def test_context_and_current_user_share_database_identity(self):
        response = self._context()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["same_user"])
        self.assertTrue(response.json()["session_identity"])

    def test_company_comes_from_database_user(self):
        self.assertEqual(self._context().json()["company_id"], str(self.company_id))

    def test_company_header_cannot_select_context_tenant(self):
        response = self._context(headers={"X-Company-ID": str(self.other_company_id)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["company_id"], str(self.company_id))

    def test_company_query_cannot_select_context_tenant(self):
        response = self._context(params={"company_id": str(self.other_company_id)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["company_id"], str(self.company_id))

    def test_forged_role_claim_does_not_override_database_role(self):
        token = create_access_token(str(self.other_user_id), role="admin")
        response = self._context(token)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["role"], "technician")

    def test_forged_permissions_do_not_override_context_or_authorization(self):
        token = create_access_token(str(self.other_user_id), permissions=["expense:manage", "report:read"])
        response = self._context(token)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["user_id"], str(self.other_user_id))
        self.assertEqual(response.json()["company_id"], str(self.other_company_id))
        denied = self.client.get("/api/v1/expenses", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(denied.status_code, 403, denied.text)
        self.assertEqual(denied.json(), {"detail": "Insufficient permissions"})

    def test_deactivated_user_rejects_existing_token(self):
        with self.Session() as db:
            db.get(User, self.user_id).is_active = False
            db.commit()
        self._assert_inactive(self._context())

    def test_deactivated_company_rejects_existing_token(self):
        with self.Session() as db:
            db.get(Company, self.company_id).status = "inactive"
            db.commit()
        self._assert_inactive(self._context())

    def test_deleted_user_rejects_existing_token(self):
        with self.Session() as db:
            db.delete(db.get(User, self.user_id))
            db.commit()
        self._assert_inactive(self._context())

    def test_unknown_user_rejected(self):
        self._assert_inactive(self._context(create_access_token(str(uuid4()))))

    def test_missing_authorization_preserves_401_and_bearer(self):
        self._assert_401(self.client.get("/context"), "Not authenticated")

    def test_non_bearer_scheme_preserves_401_and_bearer(self):
        self._assert_401(self.client.get("/context", headers={"Authorization": "Basic ignored"}), "Not authenticated")

    def test_invalid_token_preserves_401_and_bearer(self):
        self._assert_401(self._context("not-a-jwt"), "Invalid or expired access token")

    def test_expired_token_preserves_401_and_bearer(self):
        token = create_access_token(str(self.user_id), expires_minutes=-1)
        self._assert_401(self._context(token), "Invalid or expired access token")

    def test_missing_subject_preserves_error(self):
        token = jwt.encode({}, settings.secret_key, algorithm=ALGORITHM)
        self._assert_401(self._context(token), "Access token has no subject")

    def test_empty_subject_preserves_error(self):
        self._assert_401(self._context(create_access_token("")), "Access token has no subject")

    def test_invalid_uuid_subject_preserves_error(self):
        self._assert_401(self._context(create_access_token("not-a-uuid")), "Access token has an invalid subject")

    def test_signed_token_without_exp_preserves_current_compatibility(self):
        token = jwt.encode({"sub": str(self.user_id)}, settings.secret_key, algorithm=ALGORITHM)
        response = self._context(token)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["user_id"], str(self.user_id))

    def test_context_is_request_scoped_without_identity_leak(self):
        first = self._context()
        second = self._context(create_access_token(str(self.other_user_id)))
        self.assertEqual(first.json()["user_id"], str(self.user_id))
        self.assertEqual(second.json()["user_id"], str(self.other_user_id))
        self.assertEqual(second.json()["company_id"], str(self.other_company_id))
        self._assert_401(self.client.get("/context"), "Not authenticated")
        self._set_role("manager")
        self.assertEqual(self._context().json()["role"], "manager")

    def test_current_user_adapter_returns_orm_user(self):
        response = self._context()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["orm_user"])

    def test_context_and_user_dependencies_resolve_authentication_once(self):
        with patch.object(authentication._authentication_service, "get_active_user",
                          wraps=authentication._authentication_service.get_active_user) as lookup:
            with patch.object(authentication, "decode_access_token", wraps=authentication.decode_access_token) as decode:
                response = self._context()
                self.assertEqual(response.status_code, 200, response.text)
                lookup.assert_called_once()
                decode.assert_called_once()

    def test_context_does_not_eagerly_validate_invalid_role(self):
        self._set_role("invalid-role")
        response = self._context()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["role"], "invalid-role")

    def test_invalid_role_login_preserves_explicit_500(self):
        self._set_role("invalid-role")
        response = self.client.post("/api/v1/auth/login",
                                    data={"username": "admin@example.com", "password": "Password123!"})
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json(), {"detail": "User has an invalid application role"})

    def test_invalid_role_me_preserves_safe_unexpected_500(self):
        self._set_role("invalid-role")
        with self.assertLogs("backend.api.errors", level="ERROR"):
            response = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json(), {"detail": "Internal Server Error"})

    def test_invalid_role_permission_guard_preserves_403(self):
        self._set_role("invalid-role")
        response = self.client.get("/api/v1/customers", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(response.json(), {"detail": "User has an invalid application role"})

    def _get_authenticated(self, path, token=None, **kwargs):
        headers = {"Authorization": f"Bearer {self.token if token is None else token}"}
        headers.update(kwargs.pop("headers", {}))
        return self.client.get(path, headers=headers, **kwargs)

    def test_company_projection_uses_canonical_context(self):
        response = self._get_authenticated("/projections")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["company_id"], str(self.company_id))

    def test_company_projection_ignores_header_tampering(self):
        response = self._get_authenticated("/projections", headers={"X-Company-ID": str(self.other_company_id)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["company_id"], str(self.company_id))

    def test_company_projection_ignores_query_tampering(self):
        response = self._get_authenticated("/projections", params={"company_id": str(self.other_company_id)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["company_id"], str(self.company_id))

    def test_company_projection_ignores_jwt_company_claim(self):
        token = jwt.encode({"sub": str(self.user_id), "company_id": str(self.other_company_id)},
                           settings.secret_key, algorithm=ALGORITHM)
        response = self._get_authenticated("/projections", token)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["company_id"], str(self.company_id))

    def test_company_projection_preserves_contextvar_assignment(self):
        previous = get_company_context()
        try:
            with self.Session() as db:
                context = AuthContext(db.get(User, self.user_id))
                self.assertEqual(get_company_id(context), self.company_id)
                self.assertEqual(get_company_context(), self.company_id)
        finally:
            set_company_context(previous)

    def test_permission_projection_returns_same_orm_user(self):
        response = self._get_authenticated("/projections")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["permission_user_same"])
        self.assertTrue(response.json()["orm_guard_user"])
        self.assertTrue(response.json()["current_user_same"])

    def test_allowed_database_role_succeeds(self):
        response = self._get_authenticated("/api/v1/expenses")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), [])

    def test_forged_privileges_cannot_pass_guard(self):
        token = create_access_token(str(self.other_user_id), role="admin", permissions=["expense:read"])
        response = self._get_authenticated("/api/v1/expenses", token)
        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(response.json(), {"detail": "Insufficient permissions"})
        self.assertNotIn("www-authenticate", response.headers)

    def test_permission_guard_reflects_database_role_change(self):
        token = create_access_token(str(self.user_id), role="admin", permissions=["expense:read"])
        self._set_role("technician")
        response = self._get_authenticated("/api/v1/expenses", token)
        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(response.json(), {"detail": "Insufficient permissions"})
        self.assertNotIn("www-authenticate", response.headers)

    def test_invalid_role_guard_has_no_bearer_challenge(self):
        self._set_role("invalid-role")
        response = self._get_authenticated("/api/v1/customers")
        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(response.json(), {"detail": "User has an invalid application role"})
        self.assertNotIn("www-authenticate", response.headers)

    def test_me_uses_canonical_identity_and_existing_response_shape(self):
        with self.Session() as db:
            context = AuthContext(db.get(User, self.other_user_id))
            self.app.dependency_overrides[authentication.get_auth_context] = lambda: context
            response = self._get_authenticated("/api/v1/auth/me")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["id"], str(self.other_user_id))
        self.assertEqual(response.json()["company_id"], str(self.other_company_id))
        self.assertEqual(set(response.json()), {"id", "company_id", "email", "full_name", "role",
                                              "is_active", "last_login_at", "permissions"})

    def test_me_reports_database_effective_permissions(self):
        response = self._get_authenticated("/api/v1/auth/me")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(set(response.json()["permissions"]), {p.value for p in permissions_for_role("admin")})

    def test_me_reflects_database_role_changed_after_token_issuance(self):
        token = create_access_token(str(self.user_id), role="admin", permissions=["expense:read"])
        self._set_role("technician")
        response = self._get_authenticated("/api/v1/auth/me", token)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["role"], "technician")
        self.assertEqual(set(response.json()["permissions"]), {p.value for p in permissions_for_role("technician")})

    def test_me_ignores_forged_privilege_claims(self):
        token = create_access_token(str(self.other_user_id), role="admin", permissions=["expense:manage"])
        response = self._get_authenticated("/api/v1/auth/me", token)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["role"], "technician")
        self.assertEqual(set(response.json()["permissions"]), {p.value for p in permissions_for_role("technician")})

    def test_domain_company_and_permission_dependencies_authenticate_once(self):
        with patch.object(authentication._authentication_service, "get_active_user",
                          wraps=authentication._authentication_service.get_active_user) as lookup:
            with patch.object(authentication, "decode_access_token", wraps=authentication.decode_access_token) as decode:
                response = self._get_authenticated("/api/v1/customers")
                self.assertEqual(response.status_code, 200, response.text)
                lookup.assert_called_once()
                decode.assert_called_once()

    def test_projections_share_one_context_with_current_user_adapter(self):
        with patch.object(authentication._authentication_service, "get_active_user",
                          wraps=authentication._authentication_service.get_active_user) as lookup:
            with patch.object(authentication, "decode_access_token", wraps=authentication.decode_access_token) as decode:
                response = self._get_authenticated("/projections")
                self.assertEqual(response.status_code, 200, response.text)
                self.assertTrue(response.json()["permission_user_same"])
                self.assertTrue(response.json()["current_user_same"])
                lookup.assert_called_once()
                decode.assert_called_once()

    def test_me_does_not_reuse_identity_across_requests(self):
        with patch.object(authentication._authentication_service, "get_active_user",
                          wraps=authentication._authentication_service.get_active_user) as lookup:
            first = self._get_authenticated("/api/v1/auth/me")
            second = self._get_authenticated("/api/v1/auth/me", create_access_token(str(self.other_user_id)))
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(second.status_code, 200, second.text)
            self.assertEqual(first.json()["id"], str(self.user_id))
            self.assertEqual(second.json()["id"], str(self.other_user_id))
            self.assertEqual(lookup.call_count, 2)
