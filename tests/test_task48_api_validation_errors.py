"""Task 48 Phase 1–4 API errors using a disposable database."""
import os
import tempfile
import unittest
import sqlite3
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import date

DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
DB_FILE.close()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_FILE.name}"
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes-123456"

from fastapi.testclient import TestClient
from fastapi import HTTPException
from psycopg import errors as pg_errors
from psycopg.pq import DiagnosticField
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.core.database import get_db
from backend.core.security import create_access_token, hash_password
from backend.main import app
from backend.models.base import Base
import backend.models  # noqa: F401  # register ORM tables
from backend.models.company import Company
from backend.models.inventory_item import InventoryItem
from backend.models.technician_stock import TechnicianStock
from backend.models.user import User
from backend.models.customer import Customer
from backend.models.expense import Expense
from backend.models.invoice import Invoice
from backend.models.service_history import ServiceHistory
from backend.schemas.expense import ExpenseUpdate
from backend.schemas.invoice import InvoiceUpdate
from backend.schemas.service_history import ServiceHistoryUpdate
from backend.models.service_contract import ServiceContract
from backend.services.service_contract import ServiceContractService


class Task48TechnicianStockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            f"sqlite:///{DB_FILE.name}",
            connect_args={"check_same_thread": False},
        )
        cls.Session = sessionmaker(bind=cls.engine, autoflush=False, autocommit=False)
        Base.metadata.create_all(cls.engine)
        cls.password_hash = hash_password("Password123!")
        cls.previous_overrides = app.dependency_overrides.copy()

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(cls.previous_overrides)
        cls.engine.dispose()
        os.unlink(DB_FILE.name)

    def setUp(self):
        with self.Session() as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            company = Company(id=uuid4(), name="Task 48 Company", status="active")
            admin = User(
                id=uuid4(), company=company, email="admin@example.com",
                full_name="Admin", password_hash=self.password_hash, role="admin",
            )
            technician = User(
                id=uuid4(), company=company, email="technician@example.com",
                full_name="Technician", password_hash=self.password_hash, role="technician",
            )
            item = InventoryItem(id=uuid4(), company_id=company.id, item_name="Test Part")
            db.add_all([company, admin, technician, item])
            db.commit()
            self.company_id = company.id
            self.technician_id = technician.id
            self.item_id = item.id
            self.admin_headers = {"Authorization": f"Bearer {create_access_token(str(admin.id))}"}
            self.technician_headers = {"Authorization": f"Bearer {create_access_token(str(technician.id))}"}

        def override_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def _payload(self, quantity):
        return {
            "technician_id": str(self.technician_id),
            "inventory_item_id": str(self.item_id),
            "quantity": quantity,
        }

    def _create_stock(self, quantity):
        response = self.client.post(
            "/api/v1/technician-stock", json=self._payload(quantity), headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["quantity"], quantity)
        stock_id = UUID(response.json()["id"])
        with self.Session() as db:
            stock = db.get(TechnicianStock, stock_id)
            self.assertEqual(stock.quantity, quantity)
            self.assertEqual(stock.company_id, self.company_id)
            self.assertEqual(stock.technician_id, self.technician_id)
            self.assertEqual(stock.inventory_item_id, self.item_id)
        return stock_id

    def _assert_quantity(self, stock_id, quantity):
        with self.Session() as db:
            self.assertEqual(db.query(TechnicianStock).count(), 1)
            self.assertEqual(db.get(TechnicianStock, stock_id).quantity, quantity)

    def test_negative_create_returns_400_without_persistence(self):
        response = self.client.post(
            "/api/v1/technician-stock", json=self._payload(-1), headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json(), {"detail": "quantity must be non-negative"})
        with self.Session() as db:
            self.assertEqual(db.query(TechnicianStock).count(), 0)

    def test_negative_patch_returns_400_without_mutation(self):
        stock_id = self._create_stock(3)
        response = self.client.patch(
            f"/api/v1/technician-stock/{stock_id}", json={"quantity": -1}, headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json(), {"detail": "quantity must be non-negative"})
        self._assert_quantity(stock_id, 3)

    def test_zero_create_remains_valid(self):
        self._create_stock(0)

    def test_zero_patch_remains_valid(self):
        stock_id = self._create_stock(3)
        response = self.client.patch(
            f"/api/v1/technician-stock/{stock_id}", json={"quantity": 0}, headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["quantity"], 0)
        self._assert_quantity(stock_id, 0)

    def test_positive_create_remains_valid(self):
        self._create_stock(3)

    def test_positive_patch_remains_valid(self):
        stock_id = self._create_stock(3)
        response = self.client.patch(
            f"/api/v1/technician-stock/{stock_id}", json={"quantity": 5}, headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["quantity"], 5)
        self._assert_quantity(stock_id, 5)

    def test_missing_patch_target_preserves_404(self):
        response = self.client.patch(
            f"/api/v1/technician-stock/{uuid4()}", json={"quantity": 1}, headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(response.json(), {"detail": "technician stock not found"})
        with self.Session() as db:
            self.assertEqual(db.query(TechnicianStock).count(), 0)

    def test_create_and_patch_require_authentication(self):
        stock_id = self._create_stock(3)
        for method, path, payload in (
            ("POST", "/api/v1/technician-stock", self._payload(-1)),
            ("PATCH", f"/api/v1/technician-stock/{stock_id}", {"quantity": -1}),
        ):
            with self.subTest(method=method):
                response = self.client.request(method, path, json=payload)
                self.assertEqual(response.status_code, 401, response.text)
                self.assertEqual(response.json(), {"detail": "Not authenticated"})
                self.assertEqual(response.headers["www-authenticate"], "Bearer")
                self._assert_quantity(stock_id, 3)

    def test_create_and_patch_require_inventory_manage_permission(self):
        stock_id = self._create_stock(3)
        for method, path, payload in (
            ("POST", "/api/v1/technician-stock", self._payload(-1)),
            ("PATCH", f"/api/v1/technician-stock/{stock_id}", {"quantity": -1}),
        ):
            with self.subTest(method=method):
                response = self.client.request(method, path, json=payload, headers=self.technician_headers)
                self.assertEqual(response.status_code, 403, response.text)
                self.assertEqual(response.json(), {"detail": "Insufficient permissions"})
                self._assert_quantity(stock_id, 3)

    def _integrity_error(self, sqlstate="23505", constraint="uq_technician_stock_company_technician_item"):
        info = {DiagnosticField.SQLSTATE: sqlstate.encode()}
        if constraint is not None:
            info[DiagnosticField.CONSTRAINT_NAME] = constraint.encode()
        original = pg_errors.lookup(sqlstate)("private driver message", info=info)
        return IntegrityError("INSERT INTO private_table", {"secret": "private parameter"}, original)

    def _post_error(self, error, *, route="technician-stock", function="create_stock", payload=None):
        module = route.replace("-", "_")
        with patch(f"backend.api.v1.{module}.service.{function}", side_effect=error):
            with TestClient(app, raise_server_exceptions=False) as client:
                return client.post(
                    f"/api/v1/{route}", json=self._payload(1) if payload is None else payload,
                    headers=self.admin_headers,
                )

    def _assert_integrity_500(self, error):
        with self.assertLogs("backend.api.errors", level="ERROR") as logs:
            response = self._post_error(error)
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json(), {"detail": "Internal Server Error"})
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertIs(logs.records[0].exc_info[1], error)
        self.assertIsNotNone(logs.records[0].exc_info[2])

    def test_inventory_unique_conflict_returns_safe_409(self):
        response = self._post_error(
            self._integrity_error(constraint="uq_inventory_items_company_item_name"),
            route="inventory", function="create_item", payload={"item_name": "Part"},
        )
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json(), {"detail": "An inventory item with this name already exists."})

    def test_technician_stock_unique_conflict_returns_safe_409(self):
        response = self._post_error(self._integrity_error())
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json(), {"detail": "Stock for this technician and inventory item already exists."})

    def test_invoice_unique_conflict_returns_safe_409(self):
        response = self._post_error(
            self._integrity_error(constraint="uq_invoices_company_number"),
            route="invoices", function="create_invoice",
            payload={"customer_id": str(uuid4()), "invoice_number": "INV-1", "issue_date": "2026-10-02"},
        )
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json(), {"detail": "An invoice with this number already exists."})

    def test_service_contract_unique_conflict_returns_safe_409(self):
        response = self._post_error(
            self._integrity_error(constraint="uq_service_contracts_company_number"),
            route="service-contracts", function="create_contract",
            payload={"customer_id": str(uuid4()), "contract_number": "SC-1", "start_date": "2026-10-02"},
        )
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json(), {"detail": "A service contract with this number already exists."})

    def test_unknown_unique_constraint_returns_safe_500(self):
        self._assert_integrity_500(self._integrity_error(constraint="unknown_unique"))

    def test_primary_key_conflict_returns_safe_500(self):
        self._assert_integrity_500(self._integrity_error(constraint="technician_stock_pkey"))

    def test_foreign_key_violation_returns_safe_500(self):
        self._assert_integrity_500(self._integrity_error(sqlstate="23503"))

    def test_check_violation_returns_safe_500(self):
        self._assert_integrity_500(self._integrity_error(sqlstate="23514"))

    def test_not_null_violation_returns_safe_500(self):
        self._assert_integrity_500(self._integrity_error(sqlstate="23502"))

    def test_missing_constraint_diagnostics_returns_safe_500(self):
        self._assert_integrity_500(self._integrity_error(constraint=None))

    def test_constraint_match_requires_exact_name(self):
        name = "uq_technician_stock_company_technician_item"
        for constraint in (name.upper(), " " + name, name + " "):
            with self.subTest(constraint=constraint):
                self._assert_integrity_500(self._integrity_error(constraint=constraint))

    def test_unsupported_driver_is_not_classified_by_message(self):
        original = sqlite3.IntegrityError("23505 uq_technician_stock_company_technician_item")
        self._assert_integrity_500(IntegrityError("private SQL", {}, original))

    def test_unsupported_driver_is_not_classified_by_lookalike_attributes(self):
        original = RuntimeError("private driver message")
        original.sqlstate = "23505"
        original.diag = SimpleNamespace(constraint_name="uq_technician_stock_company_technician_item")
        self._assert_integrity_500(IntegrityError("private SQL", {}, original))

    def test_unexpected_exception_returns_safe_500_and_logs_traceback(self):
        error = RuntimeError("private internal details")
        with self.assertLogs("backend.api.errors", level="ERROR") as logs:
            response = self._post_error(error)
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json(), {"detail": "Internal Server Error"})
        self.assertIs(logs.records[0].exc_info[1], error)
        self.assertIsNotNone(logs.records[0].exc_info[2])

    def test_no_global_value_error_conversion(self):
        with self.assertLogs("backend.api.errors", level="ERROR"):
            response = self._post_error(
                ValueError("private internal details"), route="invoices", function="create_invoice",
                payload={"customer_id": str(uuid4()), "invoice_number": "INV-1", "issue_date": "2026-10-02"},
            )
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json(), {"detail": "Internal Server Error"})

    def test_explicit_http_exception_preserves_detail_and_headers(self):
        response = self._post_error(HTTPException(500, "Explicit application failure", {"X-Test": "preserved"}))
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json(), {"detail": "Explicit application failure"})
        self.assertEqual(response.headers["x-test"], "preserved")

    def test_request_validation_preserves_structured_422(self):
        response = self.client.post(
            "/api/v1/technician-stock", json={}, headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 422, response.text)
        detail = response.json()["detail"]
        self.assertIsInstance(detail, list)
        self.assertEqual({tuple(error["loc"]) for error in detail}, {
            ("body", "technician_id"), ("body", "inventory_item_id"),
        })
        for error in detail:
            self.assertEqual(error["type"], "missing")
            self.assertEqual(error["msg"], "Field required")
            self.assertEqual(error["input"], {})

    def test_commit_conflict_does_not_persist_pending_insert(self):
        with patch.object(self.Session.class_, "commit", side_effect=self._integrity_error()):
            response = self.client.post(
                "/api/v1/technician-stock", json=self._payload(1), headers=self.admin_headers,
            )
        self.assertEqual(response.status_code, 409, response.text)
        with self.Session() as db:
            self.assertEqual(db.query(TechnicianStock).count(), 0)

    def test_flush_conflict_rolls_back_duplicate_and_partial_mutation(self):
        stock_id = self._create_stock(3)
        from backend.api.v1.technician_stock import service
        original_create = service.create_stock

        def conflicting_create(db, company_id, data):
            db.get(InventoryItem, self.item_id).quantity = 11
            db.flush()
            try:
                return original_create(db, company_id, data)
            except IntegrityError as exc:
                # Actual SQLite duplicate failure; substitute PostgreSQL diagnostics only.
                raise self._integrity_error() from exc

        with patch.object(service, "create_stock", side_effect=conflicting_create):
            response = self.client.post(
                "/api/v1/technician-stock", json=self._payload(1), headers=self.admin_headers,
            )
        self.assertEqual(response.status_code, 409, response.text)
        self._assert_quantity(stock_id, 3)
        with self.Session() as db:
            self.assertEqual(db.get(InventoryItem, self.item_id).quantity, 0)

    def test_actual_sqlite_duplicate_remains_safe_500_without_duplicate(self):
        stock_id = self._create_stock(3)
        with self.assertLogs("backend.api.errors", level="ERROR"):
            response = self.client.post(
                "/api/v1/technician-stock", json=self._payload(1), headers=self.admin_headers,
            )
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json(), {"detail": "Internal Server Error"})
        self._assert_quantity(stock_id, 3)

    def _create_text_record(self, route, **changes):
        if route == "expenses":
            payload = {"category": "  Travel  ", "amount": "12.50", "expense_date": "2026-10-02"}
        else:
            with self.Session() as db:
                customer = Customer(id=uuid4(), company_id=self.company_id, name="Test Customer")
                db.add(customer)
                db.commit()
                customer_id = str(customer.id)
            if route == "invoices":
                payload = {"customer_id": customer_id, "invoice_number": f"  INV-{uuid4()}  ",
                           "issue_date": "2026-10-02", "subtotal": "10.25", "discount": "1.10", "tax": "0.35"}
            else:
                payload = {"customer_id": customer_id, "service_type": "  Maintenance  ",
                           "summary": "  Original summary  ", "service_date": "2026-10-02T12:00:00"}
        payload.update(changes)
        response = self.client.post(f"/api/v1/{route}", json=payload, headers=self.admin_headers)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _assert_text_patch_normalization(self, route, model, field, padded):
        created = self._create_text_record(route, **{field: padded})
        record = created
        response = self.client.patch(
            f"/api/v1/{route}/{record['id']}", json={field: padded}, headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(created[field], padded.strip())
        self.assertEqual(response.json()[field], created[field])
        with self.Session() as db:
            self.assertEqual(getattr(db.get(model, UUID(record["id"])), field), created[field])

    def _assert_invalid_text_patch(self, route, model, field, message):
        record = self._create_text_record(route)
        service_module, update = {
            "expenses": ("expenses", "update_expense"),
            "invoices": ("invoices", "update_invoice"),
            "service-history": ("service_history", "update_history"),
        }[route]
        for value in ("", " \t\n "):
            with self.subTest(value=value):
                with patch(f"backend.api.v1.{service_module}.service.{update}") as writer:
                    response = self.client.patch(
                        f"/api/v1/{route}/{record['id']}",
                        json={field: value, "notes": "must not persist"}, headers=self.admin_headers,
                    )
                    writer.assert_not_called()
                self.assertEqual(response.status_code, 422, response.text)
                error = response.json()["detail"][0]
                self.assertEqual(error["loc"], ["body", field])
                self.assertEqual(error["msg"], f"Value error, {message}")
                with self.Session() as db:
                    stored = db.get(model, UUID(record["id"]))
                    self.assertEqual(getattr(stored, field), record[field])
                    self.assertIsNone(stored.notes)

    def _assert_omitted_text_patch(self, route, model, fields):
        record = self._create_text_record(route)
        response = self.client.patch(
            f"/api/v1/{route}/{record['id']}", json={"notes": "Updated notes"}, headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        with self.Session() as db:
            stored = db.get(model, UUID(record["id"]))
            self.assertEqual(stored.notes, "Updated notes")
            for field in fields:
                self.assertEqual(getattr(stored, field), record[field])

    def test_expense_patch_category_matches_create_normalization(self):
        self._assert_text_patch_normalization("expenses", Expense, "category", "  Supplies  ")

    def test_expense_patch_blank_category_rejected_before_persistence(self):
        self._assert_invalid_text_patch("expenses", Expense, "category", "category must not be empty")

    def test_expense_patch_omitted_category_unchanged(self):
        self._assert_omitted_text_patch("expenses", Expense, ("category",))

    def test_invoice_patch_number_matches_create_normalization(self):
        self._assert_text_patch_normalization("invoices", Invoice, "invoice_number", "  INV-NEW  ")

    def test_invoice_patch_blank_number_rejected_before_persistence(self):
        self._assert_invalid_text_patch("invoices", Invoice, "invoice_number", "invoice_number must not be empty")

    def test_invoice_patch_omitted_number_unchanged(self):
        self._assert_omitted_text_patch("invoices", Invoice, ("invoice_number",))

    def test_invoice_total_policy_and_patch_behavior_unchanged(self):
        for changes, expected in (({}, "9.50"), ({"discount": "20"}, "0"),
                                  ({"total": "37.25"}, "37.25"), ({"total": "0"}, "0")):
            with self.subTest(changes=changes):
                record = self._create_text_record("invoices", **changes)
                self.assertEqual(Decimal(record["total"]), Decimal(expected))
                response = self.client.patch(
                    f"/api/v1/invoices/{record['id']}", json={"subtotal": "100"}, headers=self.admin_headers,
                )
                self.assertEqual(response.status_code, 200, response.text)
                with self.Session() as db:
                    stored = db.get(Invoice, UUID(record["id"]))
                    self.assertEqual(stored.total, Decimal(expected))
                    self.assertEqual(stored.subtotal, Decimal("100"))

    def test_history_patch_service_type_matches_create_normalization(self):
        self._assert_text_patch_normalization("service-history", ServiceHistory, "service_type", "  Repair  ")

    def test_history_patch_blank_service_type_rejected_before_persistence(self):
        self._assert_invalid_text_patch("service-history", ServiceHistory, "service_type", "value must not be empty")

    def test_history_patch_summary_matches_create_normalization(self):
        self._assert_text_patch_normalization("service-history", ServiceHistory, "summary", "  Replaced filter  ")

    def test_history_patch_blank_summary_rejected_before_persistence(self):
        self._assert_invalid_text_patch("service-history", ServiceHistory, "summary", "value must not be empty")

    def test_history_patch_omitted_required_text_unchanged(self):
        self._assert_omitted_text_patch("service-history", ServiceHistory, ("service_type", "summary"))

    def test_patch_schema_explicit_null_and_omission_semantics_unchanged(self):
        for schema, fields in ((ExpenseUpdate, ("category",)), (InvoiceUpdate, ("invoice_number",)),
                               (ServiceHistoryUpdate, ("service_type", "summary"))):
            with self.subTest(schema=schema.__name__):
                self.assertEqual(schema().model_dump(exclude_unset=True), {})
                supplied_nulls = dict.fromkeys(fields)
                self.assertEqual(schema(**supplied_nulls).model_dump(exclude_unset=True), supplied_nulls)

    def _contract_payload(self):
        with self.Session() as db:
            customer = Customer(id=uuid4(), company_id=self.company_id, name="Contract Customer")
            db.add(customer)
            db.commit()
            customer_id = str(customer.id)
        return {"customer_id": customer_id, "contract_number": f"SC-{uuid4()}",
                "start_date": "2026-10-10", "end_date": "2026-10-20"}

    def _create_contract(self, **changes):
        payload = {**self._contract_payload(), **changes}
        response = self.client.post("/api/v1/service-contracts", json=payload, headers=self.admin_headers)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _patch_contract(self, record, payload):
        return self.client.patch(
            f"/api/v1/service-contracts/{record['id']}", json=payload, headers=self.admin_headers,
        )

    def _assert_contract_dates(self, record, start, end, notes=None):
        with self.Session() as db:
            stored = db.get(ServiceContract, UUID(record["id"]))
            self.assertEqual(stored.start_date, date.fromisoformat(start))
            self.assertEqual(stored.end_date, date.fromisoformat(end) if end is not None else None)
            self.assertEqual(stored.notes, notes)

    def _assert_invalid_contract_patch(self, payload):
        record = self._create_contract()
        from backend.api.v1.service_contracts import service
        with patch.object(service.repository, "update", wraps=service.repository.update) as writer:
            response = self._patch_contract(record, {**payload, "notes": "must not persist"})
            writer.assert_not_called()
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json(), {"detail": "end_date must be on or after start_date"})
        self._assert_contract_dates(record, record["start_date"], record["end_date"])

    def _assert_valid_contract_patch(self, payload):
        record = self._create_contract()
        response = self._patch_contract(record, payload)
        self.assertEqual(response.status_code, 200, response.text)
        self._assert_contract_dates(
            record, payload.get("start_date", record["start_date"]),
            payload.get("end_date", record["end_date"]),
        )

    def test_contract_patch_start_after_persisted_end_rejected(self):
        self._assert_invalid_contract_patch({"start_date": "2026-10-21"})

    def test_contract_patch_start_equal_persisted_end_valid(self):
        self._assert_valid_contract_patch({"start_date": "2026-10-20"})

    def test_contract_patch_start_before_persisted_end_valid(self):
        self._assert_valid_contract_patch({"start_date": "2026-10-19"})

    def test_contract_patch_end_before_persisted_start_rejected(self):
        self._assert_invalid_contract_patch({"end_date": "2026-10-09"})

    def test_contract_patch_end_equal_persisted_start_valid(self):
        self._assert_valid_contract_patch({"end_date": "2026-10-10"})

    def test_contract_patch_end_after_persisted_start_valid(self):
        self._assert_valid_contract_patch({"end_date": "2026-10-11"})

    def test_contract_patch_both_invalid_rejected_before_mutation(self):
        self._assert_invalid_contract_patch({"start_date": "2026-10-25", "end_date": "2026-10-24"})

    def test_contract_patch_both_valid_uses_supplied_dates(self):
        # New start exceeds the OLD end; both new dates must be used.
        self._assert_valid_contract_patch({"start_date": "2026-10-25", "end_date": "2026-10-30"})

    def test_contract_patch_explicit_end_null_clears_date(self):
        self._assert_valid_contract_patch({"end_date": None})

    def test_contract_patch_omitted_dates_preserved(self):
        record = self._create_contract()
        with patch("backend.services.service_contract.validate_contract_dates") as validator:
            response = self._patch_contract(record, {"notes": "Updated notes"})
            validator.assert_not_called()
        self.assertEqual(response.status_code, 200, response.text)
        self._assert_contract_dates(record, record["start_date"], record["end_date"], "Updated notes")

    def test_contract_patch_missing_target_preserves_404_before_validation(self):
        with patch("backend.services.service_contract.validate_contract_dates") as validator:
            response = self._patch_contract(
                {"id": str(uuid4())}, {"start_date": "2026-10-25", "end_date": "2026-10-24"},
            )
            validator.assert_not_called()
        self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(response.json(), {"detail": "service_contracts record not found"})

    def test_contract_patch_other_tenant_target_preserves_404(self):
        record = self._create_contract()
        with self.Session() as db:
            other_company = Company(id=uuid4(), name="Other Company", status="active")
            db.add(other_company)
            db.get(ServiceContract, UUID(record["id"])).company_id = other_company.id
            db.commit()
        with patch("backend.services.service_contract.validate_contract_dates") as validator:
            response = self._patch_contract(record, {"end_date": "2026-10-09"})
            validator.assert_not_called()
        self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(response.json(), {"detail": "service_contracts record not found"})
        self._assert_contract_dates(record, record["start_date"], record["end_date"])

    def test_contract_service_rejects_invalid_effective_range_before_repository_update(self):
        record = self._create_contract()
        service = ServiceContractService()
        with self.Session() as db:
            with patch.object(service.repository, "update", wraps=service.repository.update) as writer:
                with self.assertRaisesRegex(ValueError, "^end_date must be on or after start_date$"):
                    service.update_contract(db, self.company_id, UUID(record["id"]),
                                            {"end_date": date(2026, 10, 9), "notes": "must not persist"})
                writer.assert_not_called()
            self.assertFalse(db.dirty)
        self._assert_contract_dates(record, record["start_date"], record["end_date"])

    def test_contract_create_date_rule_and_wording_unchanged(self):
        payload = self._contract_payload()
        response = self.client.post(
            "/api/v1/service-contracts", json={**payload, "end_date": "2026-10-09"}, headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(response.json()["detail"][0]["msg"],
                         "Value error, end_date must be on or after start_date")
        with self.Session() as db:
            self.assertEqual(db.query(ServiceContract).count(), 0)
        for end in ("2026-10-10", "2026-10-20", None):
            with self.subTest(end=end):
                self._create_contract(end_date=end)

    def test_contract_non_date_patch_behavior_unchanged(self):
        record = self._create_contract()
        response = self._patch_contract(record, {"billing_frequency": "Quarterly", "contract_value": "42.50"})
        self.assertEqual(response.status_code, 200, response.text)
        self._assert_contract_dates(record, record["start_date"], record["end_date"])
        with self.Session() as db:
            stored = db.get(ServiceContract, UUID(record["id"]))
            self.assertEqual(stored.billing_frequency, "Quarterly")
            self.assertEqual(stored.contract_value, Decimal("42.50"))

    def test_contract_patch_malformed_date_remains_422(self):
        record = self._create_contract()
        response = self._patch_contract(record, {"start_date": "not-a-date", "notes": "must not persist"})
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(response.json()["detail"][0]["loc"], ["body", "start_date"])
        self._assert_contract_dates(record, record["start_date"], record["end_date"])

    def test_contract_patch_required_start_null_preserves_persistence_failure(self):
        record = self._create_contract()
        with self.assertLogs("backend.api.errors", level="ERROR"):
            response = self._patch_contract(record, {"start_date": None})
        self.assertEqual(response.status_code, 500, response.text)
        self.assertEqual(response.json(), {"detail": "Internal Server Error"})
        self._assert_contract_dates(record, record["start_date"], record["end_date"])

    def test_contract_patch_start_with_no_end_and_combined_clear_remain_valid(self):
        record = self._create_contract(end_date=None)
        response = self._patch_contract(record, {"start_date": "2026-11-01"})
        self.assertEqual(response.status_code, 200, response.text)
        self._assert_contract_dates(record, "2026-11-01", None)
        self._assert_valid_contract_patch({"start_date": "2026-11-01", "end_date": None})
