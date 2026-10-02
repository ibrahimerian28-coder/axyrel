"""Task 47 create-name and invoice-total rules using a disposable database."""
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
from backend.models.inventory_item import InventoryItem
from backend.models.invoice import Invoice
from backend.models.user import User
from backend.services.customer import CustomerService
from backend.services.inventory import InventoryService
from backend.services.invoice import InvoiceService
from backend.core.authorization import Permission, Role, ROLE_PERMISSIONS
from backend.core.security import create_access_token
from backend.services.inventory_rules import InventoryBusinessRules
from backend.models.expense import Expense
from backend.services.expense import ExpenseService
from backend.models.work_order import WorkOrder
from backend.services.work_order import WorkOrderService


class Task47CreateNameTests(unittest.TestCase):
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
            company = Company(id=uuid4(), name="Task 47 Company", status="active")
            admin = User(
                id=uuid4(), company=company, email="admin@example.com",
                full_name="Admin", password_hash=self.password_hash, role="admin",
            )
            db.add_all([company, admin])
            db.commit()
            self.company_id = company.id

        def override_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def _post(self, resource, payload):
        login = self.client.post(
            "/api/v1/auth/login",
            data={"username": "admin@example.com", "password": "Password123!"},
        )
        self.assertEqual(login.status_code, 200, login.text)
        return self.client.post(
            f"/api/v1/{resource}", json=payload,
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )

    def _assert_no_records(self, model):
        with self.Session() as db:
            self.assertEqual(db.query(model).count(), 0)

    def test_customer_empty_name_rejected_without_persistence(self):
        response = self._post("customers", {"name": ""})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["detail"], "Name is required.")
        self._assert_no_records(Customer)

    def test_customer_whitespace_name_rejected_without_persistence(self):
        response = self._post("customers", {"name": " \t\n "})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["detail"], "Name is required.")
        self._assert_no_records(Customer)

    def test_customer_padded_name_stored_trimmed(self):
        response = self._post("customers", {"name": " \tField Customer\n "})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["name"], "Field Customer")
        with self.Session() as db:
            record = db.get(Customer, UUID(response.json()["id"]))
            self.assertEqual(record.name, "Field Customer")
            self.assertEqual(record.company_id, self.company_id)

    def test_customer_service_rejects_blank_before_repository_mutation(self):
        service = CustomerService()
        for name in ("", " \t\n "):
            with self.subTest(name=name), self.Session() as db:
                with patch.object(service.repository, "create") as create:
                    with self.assertRaisesRegex(ValueError, "Name is required"):
                        service.create_customer(db, self.company_id, {"name": name})
                    create.assert_not_called()
                db.commit()
            self._assert_no_records(Customer)

    def test_customer_service_stores_padded_name_trimmed(self):
        with self.Session() as db:
            record = CustomerService().create_customer(
                db, self.company_id, {"name": "  Direct Customer  "},
            )
            record_id = record.id
            db.commit()
        with self.Session() as db:
            self.assertEqual(db.get(Customer, record_id).name, "Direct Customer")

    def test_inventory_empty_name_rejected_without_persistence(self):
        response = self._post("inventory", {"item_name": ""})
        # The existing schema's min_length check rejects this before the service.
        self.assertEqual(response.status_code, 422, response.text)
        self._assert_no_records(InventoryItem)

    def test_inventory_whitespace_name_rejected_without_persistence(self):
        response = self._post("inventory", {"item_name": " \t\n "})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["detail"], "Item name is required.")
        self._assert_no_records(InventoryItem)

    def test_inventory_padded_name_stored_trimmed(self):
        response = self._post("inventory", {"item_name": " \tFilter Part\n "})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["item_name"], "Filter Part")
        with self.Session() as db:
            record = db.get(InventoryItem, UUID(response.json()["id"]))
            self.assertEqual(record.item_name, "Filter Part")
            self.assertEqual(record.company_id, self.company_id)

    def test_inventory_service_rejects_blank_before_repository_mutation(self):
        service = InventoryService()
        for name in ("", " \t\n "):
            with self.subTest(name=name), self.Session() as db:
                with patch.object(service.repository, "create") as create:
                    with self.assertRaisesRegex(ValueError, "Item name is required"):
                        service.create_item(db, self.company_id, {"item_name": name})
                    create.assert_not_called()
                db.commit()
            self._assert_no_records(InventoryItem)

    def test_inventory_service_stores_padded_name_trimmed(self):
        with self.Session() as db:
            record = InventoryService().create_item(
                db, self.company_id, {"item_name": "  Direct Part  "},
            )
            record_id = record.id
            db.commit()
        with self.Session() as db:
            self.assertEqual(db.get(InventoryItem, record_id).item_name, "Direct Part")

    def _invoice_payload(self):
        with self.Session() as db:
            customer = Customer(company_id=self.company_id, name="Invoice Customer")
            db.add(customer)
            db.commit()
            return {
                "customer_id": customer.id,
                "invoice_number": f"INV-{uuid4()}",
                "issue_date": date.today(),
            }

    def _create_invoice(self, **amounts):
        payload = {**self._invoice_payload(), **amounts}
        with self.Session() as db:
            invoice = InvoiceService().create_invoice(db, self.company_id, payload)
            db.commit()
            db.refresh(invoice)
            db.expunge(invoice)
            return invoice

    def _create_invoice_api(self, **amounts):
        payload = self._invoice_payload()
        payload["customer_id"] = str(payload["customer_id"])
        payload["issue_date"] = payload["issue_date"].isoformat()
        response = self._post("invoices", {**payload, **amounts})
        self.assertEqual(response.status_code, 201, response.text)
        return response

    def test_invoice_omitted_total_calculated_by_service(self):
        invoice = self._create_invoice(
            subtotal=Decimal("100"), discount=Decimal("20"), tax=Decimal("5"),
        )
        self.assertEqual(invoice.total, Decimal("85"))

    def test_invoice_negative_calculated_total_stored_as_decimal_zero(self):
        invoice = self._create_invoice(
            subtotal=Decimal("10"), discount=Decimal("20"), tax=Decimal("1"),
        )
        self.assertIsInstance(invoice.total, Decimal)
        self.assertEqual(invoice.total, Decimal("0"))

    def test_invoice_missing_components_use_existing_zero_defaults(self):
        cases = [
            ({}, Decimal("0")),
            ({"subtotal": Decimal("25")}, Decimal("25")),
            ({"discount": Decimal("5")}, Decimal("0")),
            ({"tax": Decimal("3")}, Decimal("3")),
        ]
        for amounts, expected in cases:
            with self.subTest(amounts=amounts):
                self.assertEqual(self._create_invoice(**amounts).total, expected)

    def test_invoice_fractional_components_use_decimal_arithmetic(self):
        invoice = self._create_invoice(
            subtotal=Decimal("0.10"), discount=Decimal("0.03"), tax=Decimal("0.02"),
        )
        self.assertEqual(invoice.total, Decimal("0.09"))

    def test_invoice_explicit_total_preserved(self):
        response = self._create_invoice_api(subtotal="100.00", total="7.25")
        with self.Session() as db:
            invoice = db.get(Invoice, UUID(response.json()["id"]))
            self.assertEqual(invoice.total, Decimal("7.25"))

    def test_invoice_explicit_zero_total_preserved(self):
        response = self._create_invoice_api(subtotal="100.00", total=0)
        with self.Session() as db:
            invoice = db.get(Invoice, UUID(response.json()["id"]))
            self.assertEqual(invoice.total, Decimal("0"))

    def test_invoice_patch_does_not_recalculate_total(self):
        response = self._create_invoice_api(subtotal="100.00", total="7.25")
        invoice_id = response.json()["id"]
        login = self.client.post(
            "/api/v1/auth/login",
            data={"username": "admin@example.com", "password": "Password123!"},
        )
        self.assertEqual(login.status_code, 200, login.text)
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = self.client.patch(
            f"/api/v1/invoices/{invoice_id}", json={"subtotal": "200.00"}, headers=headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        with self.Session() as db:
            invoice = db.get(Invoice, UUID(invoice_id))
            self.assertEqual(invoice.subtotal, Decimal("200"))
            self.assertEqual(invoice.total, Decimal("7.25"))
        response = self.client.patch(
            f"/api/v1/invoices/{invoice_id}", json={"total": "9.50"}, headers=headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        with self.Session() as db:
            self.assertEqual(db.get(Invoice, UUID(invoice_id)).total, Decimal("9.50"))

    def test_invoice_api_persists_backend_calculated_total(self):
        response = self._create_invoice_api(subtotal="100.25", discount="20.10", tax="5.05")
        self.assertEqual(Decimal(str(response.json()["total"])), Decimal("85.20"))
        with self.Session() as db:
            invoice = db.get(Invoice, UUID(response.json()["id"]))
            self.assertEqual(invoice.total, Decimal("85.20"))
            self.assertEqual(invoice.company_id, self.company_id)

    def test_invoice_ui_create_payload_omits_total(self):
        from streamlit.testing.v1 import AppTest

        customer_id = str(uuid4())
        with patch("modules.invoices.list_records") as list_records, patch(
            "modules.invoices.create_record", return_value={"id": str(uuid4())},
        ) as create_record:
            list_records.side_effect = lambda resource: (
                [{"id": customer_id, "name": "UI Customer"}] if resource == "customers" else []
            )
            ui = AppTest.from_string("from modules.invoices import app\napp()").run()
            self.assertEqual(len(ui.exception), 0)
            ui.text_input[0].set_value("UI-001")
            ui.number_input[0].set_value(100.25)
            ui.number_input[1].set_value(20.10)
            ui.number_input[2].set_value(5.05)
            ui.button[0].click().run()
            self.assertEqual(len(ui.exception), 0)
            create_record.assert_called_once()
            resource, payload = create_record.call_args.args
            self.assertEqual(resource, "invoices")
            self.assertNotIn("total", payload)
            self.assertEqual(payload["customer_id"], customer_id)
            self.assertEqual(payload["subtotal"], 100.25)
            self.assertEqual(payload["discount"], 20.10)
            self.assertEqual(payload["tax"], 5.05)

    def _inventory_item(self, **fields):
        with self.Session() as db:
            item = InventoryItem(
                company_id=fields.pop("company_id", self.company_id),
                item_name=fields.pop("item_name", "Summary Part"), **fields,
            )
            db.add(item)
            db.commit()
            return item.id

    def _inventory_summary(self):
        with self.Session() as db:
            return InventoryService().get_summary(db, self.company_id)

    def _admin_headers(self):
        with self.Session() as db:
            admin = db.query(User).filter_by(email="admin@example.com").one()
            return {"Authorization": f"Bearer {create_access_token(str(admin.id))}"}

    def test_inventory_value_multiple_items(self):
        self._inventory_item(quantity=3, cost_price=Decimal("10"))
        self._inventory_item(quantity=2, cost_price=Decimal("7"))
        summary = self._inventory_summary()
        self.assertEqual(summary.item_count, 2)
        self.assertEqual(summary.total_stock_value, Decimal("44"))

    def test_inventory_value_fractional_costs(self):
        self._inventory_item(quantity=3, cost_price=Decimal("0.10"))
        self._inventory_item(quantity=2, cost_price=Decimal("1.25"))
        summary = self._inventory_summary()
        self.assertIsInstance(summary.total_stock_value, Decimal)
        self.assertEqual(summary.total_stock_value, Decimal("2.80"))

    def test_inventory_value_zero_quantity(self):
        self._inventory_item(quantity=0, cost_price=Decimal("12.34"))
        self.assertEqual(self._inventory_summary().total_stock_value, Decimal("0"))

    def test_inventory_summary_empty(self):
        summary = self._inventory_summary()
        self.assertEqual(summary.item_count, 0)
        self.assertEqual(summary.total_stock_value, Decimal("0"))
        self.assertEqual(summary.low_stock_count, 0)
        self.assertEqual(summary.low_stock_item_ids, [])

    def test_inventory_summary_includes_inactive(self):
        item_id = self._inventory_item(
            quantity=2, min_limit=3, cost_price=Decimal("4"), status="Inactive",
        )
        summary = self._inventory_summary()
        self.assertEqual(summary.item_count, 1)
        self.assertEqual(summary.total_stock_value, Decimal("8"))
        self.assertEqual(summary.low_stock_item_ids, [item_id])

    def test_inventory_summary_excludes_deleted(self):
        self._inventory_item(quantity=2, min_limit=3, cost_price=Decimal("4"), status="Deleted")
        summary = self._inventory_summary()
        self.assertEqual(summary.item_count, 0)
        self.assertEqual(summary.total_stock_value, Decimal("0"))
        self.assertEqual(summary.low_stock_item_ids, [])

    def test_inventory_summary_tenant_isolation(self):
        own_id = self._inventory_item(quantity=1, min_limit=2, cost_price=Decimal("3"))
        with self.Session() as db:
            other = Company(id=uuid4(), name="Other Company", status="active")
            db.add(other)
            db.commit()
            other_id = other.id
        self._inventory_item(company_id=other_id, quantity=100, min_limit=200, cost_price=Decimal("99"))
        response = self.client.get(
            "/api/v1/inventory/summary",
            headers={**self._admin_headers(), "X-Company-ID": str(other_id)},
            params={"company_id": str(other_id)},
        )
        self.assertEqual(response.status_code, 200, response.text)
        summary = response.json()
        self.assertEqual(summary["item_count"], 1)
        self.assertEqual(Decimal(str(summary["total_stock_value"])), Decimal("3"))
        self.assertEqual(summary["low_stock_count"], 1)
        self.assertEqual(summary["low_stock_item_ids"], [str(own_id)])

    def test_inventory_classification_below_minimum(self):
        item_id = self._inventory_item(quantity=1, min_limit=2)
        self.assertEqual(self._inventory_summary().low_stock_item_ids, [item_id])

    def test_inventory_classification_equal_minimum(self):
        item_id = self._inventory_item(quantity=2, min_limit=2)
        self.assertEqual(self._inventory_summary().low_stock_item_ids, [item_id])

    def test_inventory_classification_above_minimum(self):
        self._inventory_item(quantity=3, min_limit=2)
        self.assertEqual(self._inventory_summary().low_stock_item_ids, [])

    def test_inventory_backend_low_remains_ui_good(self):
        item_id = self._inventory_item(quantity=3, min_limit=1, ideal_stock=10)
        with self.Session() as db:
            self.assertEqual(InventoryBusinessRules.stock_status(db.get(InventoryItem, item_id)).code, "LOW")
        self.assertEqual(self._inventory_summary().low_stock_item_ids, [])
        self.assertEqual(self._inventory_summary().low_stock_count, 0)

    def test_inventory_low_count_matches_classified_ids(self):
        below = self._inventory_item(quantity=1, min_limit=2)
        equal = self._inventory_item(quantity=2, min_limit=2)
        self._inventory_item(quantity=3, min_limit=2)
        summary = self._inventory_summary()
        self.assertEqual(set(summary.low_stock_item_ids), {below, equal})
        self.assertEqual(summary.low_stock_count, len(summary.low_stock_item_ids))

    def test_inventory_summary_static_route_and_list_compatibility(self):
        item_id = self._inventory_item(quantity=2, cost_price=Decimal("1.25"))
        headers = self._admin_headers()
        response = self.client.get("/api/v1/inventory/summary", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(set(response.json()), {
            "item_count", "low_stock_count", "total_stock_value", "low_stock_item_ids",
        })
        response = self.client.get("/api/v1/inventory", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(set(response.json()[0]), {
            "id", "company_id", "item_name", "quantity", "min_limit", "cost_price", "ideal_stock", "status",
        })
        self.assertEqual(response.json()[0]["id"], str(item_id))
        response = self.client.get(f"/api/v1/inventory/{item_id}", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)

    def test_inventory_summary_requires_inventory_read_permission(self):
        response = self.client.get("/api/v1/inventory/summary")
        self.assertEqual(response.status_code, 401, response.text)
        with self.Session() as db:
            technician = User(
                company_id=self.company_id, email="reader@example.com", full_name="Reader",
                password_hash=self.password_hash, role="technician",
            )
            db.add(technician)
            db.commit()
            headers = {"Authorization": f"Bearer {create_access_token(str(technician.id))}"}
        # All current valid roles have inventory:read; exercise denial by temporarily
        # removing only that permission from the existing role map in this test.
        with patch.dict(ROLE_PERMISSIONS, {
            Role.TECHNICIAN: ROLE_PERMISSIONS[Role.TECHNICIAN] - {Permission.INVENTORY_READ},
        }):
            response = self.client.get("/api/v1/inventory/summary", headers=headers)
            self.assertEqual(response.status_code, 403, response.text)
        response = self.client.get("/api/v1/inventory/summary", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)

    def test_inventory_summary_independent_of_search(self):
        self._inventory_item(item_name="Match", quantity=1, min_limit=2, cost_price=Decimal("3"))
        self._inventory_item(item_name="Other", quantity=2, min_limit=3, cost_price=Decimal("4"))
        headers = self._admin_headers()
        before = self.client.get("/api/v1/inventory/summary", headers=headers)
        self.assertEqual(before.status_code, 200, before.text)
        filtered = self.client.get("/api/v1/inventory", params={"search": "Match"}, headers=headers)
        self.assertEqual(filtered.status_code, 200, filtered.text)
        self.assertEqual(len(filtered.json()), 1)
        after = self.client.get("/api/v1/inventory/summary", headers=headers)
        self.assertEqual(after.status_code, 200, after.text)
        self.assertEqual(after.json(), before.json())
        self.assertEqual(after.json()["item_count"], 2)
        self.assertEqual(after.json()["low_stock_count"], 2)
        self.assertEqual(Decimal(str(after.json()["total_stock_value"])), Decimal("11"))

    def test_inventory_ui_uses_summary_and_preserves_it_during_search(self):
        from streamlit.testing.v1 import AppTest

        good_id, low_id = str(uuid4()), str(uuid4())
        # Contrasting raw values prove that the UI renders the backend decision.
        items = [
            {"id": good_id, "item_name": "Backend Good", "quantity": 0, "min_limit": 10, "cost_price": "0.10"},
            {"id": low_id, "item_name": "Backend Low", "quantity": 99, "min_limit": 0, "cost_price": "5.00"},
        ]
        summary = {"item_count": 7, "low_stock_count": 4, "total_stock_value": "999.25", "low_stock_item_ids": [low_id]}
        with patch("modules.inventory.list_records") as lists, patch("modules.inventory.request") as request:
            lists.side_effect = lambda resource, **kwargs: items[1:] if kwargs.get("search") else items
            request.side_effect = lambda method, path: summary if path == "/inventory/summary" else []
            ui = AppTest.from_string("from modules.inventory import app\napp()").run()
            self.assertEqual(len(ui.exception), 0)
            self.assertEqual([m.value for m in ui.metric], ["7", "4", "999.25 EGP"])
            labels = [e.label for e in ui.expander]
            self.assertTrue(any("Backend Good" in label and "🟢 Good" in label for label in labels))
            self.assertTrue(any("Backend Low" in label and "🔴 Low" in label for label in labels))
            ui.text_input[1].set_value("Backend Low").run()
            self.assertEqual(len(ui.exception), 0)
            self.assertEqual([m.value for m in ui.metric], ["7", "4", "999.25 EGP"])
            labels = [e.label for e in ui.expander]
            self.assertFalse(any("Backend Good" in label for label in labels))
            self.assertTrue(any("Backend Low" in label and "🔴 Low" in label for label in labels))
            summary_calls = [call for call in request.call_args_list if call.args[1] == "/inventory/summary"]
            self.assertEqual(len(summary_calls), 2)
            for call in summary_calls:
                self.assertEqual(call.args, ("GET", "/inventory/summary"))
                self.assertEqual(call.kwargs, {})

    def _expense(self, amount, status="Active", company_id=None):
        with self.Session() as db:
            expense = Expense(
                company_id=company_id or self.company_id, category="Parts",
                amount=Decimal(amount), expense_date=date.today(), status=status,
            )
            db.add(expense)
            db.commit()
            return expense.id

    def _expense_summary(self):
        with self.Session() as db:
            return ExpenseService().get_summary(db, self.company_id)

    def test_expense_summary_empty_returns_zero(self):
        summary = self._expense_summary()
        self.assertIsInstance(summary.total_amount, Decimal)
        self.assertEqual(summary.total_amount, Decimal("0"))

    def test_expense_summary_multiple_expenses(self):
        self._expense("10")
        self._expense("25")
        self.assertEqual(self._expense_summary().total_amount, Decimal("35"))

    def test_expense_summary_fractional_amounts(self):
        self._expense("0.10")
        self._expense("0.20")
        summary = self._expense_summary()
        self.assertIsInstance(summary.total_amount, Decimal)
        self.assertEqual(summary.total_amount, Decimal("0.30"))

    def test_expense_summary_includes_non_active_non_deleted(self):
        self._expense("10", status="Active")
        self._expense("20", status="Inactive")
        self._expense("30", status="Cancelled")
        self.assertEqual(self._expense_summary().total_amount, Decimal("60"))

    def test_expense_summary_excludes_deleted(self):
        self._expense("10")
        self._expense("90", status="Deleted")
        self.assertEqual(self._expense_summary().total_amount, Decimal("10"))

    def test_expense_summary_tenant_isolation(self):
        self._expense("7.25")
        with self.Session() as db:
            other = Company(id=uuid4(), name="Other Expense Company", status="active")
            db.add(other)
            db.commit()
            other_id = other.id
        self._expense("1000", company_id=other_id)
        response = self.client.get(
            "/api/v1/expenses/summary",
            headers={**self._admin_headers(), "X-Company-ID": str(other_id)},
            params={"company_id": str(other_id)},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(Decimal(str(response.json()["total_amount"])), Decimal("7.25"))

    def test_expense_list_response_shape_unchanged(self):
        expense_id = self._expense("3.50")
        self._expense("4.50", status="Cancelled")
        self._expense("99", status="Deleted")
        headers = self._admin_headers()
        response = self.client.get("/api/v1/expenses", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(set(response.json()[0]), {
            "id", "company_id", "category", "description", "amount", "expense_date",
            "payment_method", "vendor", "reference", "notes", "status", "created_at", "updated_at",
        })
        summary = self.client.get("/api/v1/expenses/summary", headers=headers)
        self.assertEqual(summary.status_code, 200, summary.text)
        self.assertEqual(
            Decimal(str(summary.json()["total_amount"])),
            sum((Decimal(str(row["amount"])) for row in response.json()), Decimal("0")),
        )
        response = self.client.get(f"/api/v1/expenses/{expense_id}", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)

    def test_expense_summary_static_route(self):
        self._expense("12.34")
        response = self.client.get("/api/v1/expenses/summary", headers=self._admin_headers())
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(set(response.json()), {"total_amount"})
        self.assertEqual(Decimal(str(response.json()["total_amount"])), Decimal("12.34"))

    def test_expense_summary_requires_expense_read_permission(self):
        response = self.client.get("/api/v1/expenses/summary")
        self.assertEqual(response.status_code, 401, response.text)
        with self.Session() as db:
            technician = User(
                company_id=self.company_id, email="expense-tech@example.com", full_name="Tech",
                password_hash=self.password_hash, role="technician",
            )
            db.add(technician)
            db.commit()
            headers = {"Authorization": f"Bearer {create_access_token(str(technician.id))}"}
        response = self.client.get("/api/v1/expenses/summary", headers=headers)
        self.assertEqual(response.status_code, 403, response.text)
        response = self.client.get("/api/v1/expenses/summary", headers=self._admin_headers())
        self.assertEqual(response.status_code, 200, response.text)

    def test_expense_ui_consumes_backend_total(self):
        from streamlit.testing.v1 import AppTest

        expenses = [{"id": str(uuid4()), "category": "Parts", "amount": "1.25", "expense_date": "2026-10-02"}]
        with patch("modules.expenses.list_records", return_value=expenses), patch(
            "modules.expenses.request", return_value={"total_amount": "999.25"},
        ) as request:
            ui = AppTest.from_string("from modules.expenses import app\napp()").run()
            self.assertEqual(len(ui.exception), 0)
            self.assertEqual([metric.value for metric in ui.metric], ["1", "999.25 EGP"])
            request.assert_called_once_with("GET", "/expenses/summary")

    def _work_order(self, status, company_id=None):
        with self.Session() as db:
            tenant_id = company_id or self.company_id
            customer = Customer(company_id=tenant_id, name="KPI Customer")
            db.add(customer)
            db.flush()
            # Closed/Deleted fixtures represent persisted historical data, without
            # changing or bypassing the application's lifecycle implementation.
            order = WorkOrder(company_id=tenant_id, customer_id=customer.id, title="KPI Order", status=status)
            db.add(order)
            db.commit()
            return order.id

    def _work_order_summary(self):
        with self.Session() as db:
            return WorkOrderService().get_summary(db, self.company_id)

    def test_work_order_summary_empty(self):
        self.assertEqual(self._work_order_summary().open_count, 0)

    def test_work_order_summary_counts_open(self):
        self._work_order("Open")
        self.assertEqual(self._work_order_summary().open_count, 1)

    def test_work_order_summary_counts_in_progress(self):
        self._work_order("In Progress")
        self.assertEqual(self._work_order_summary().open_count, 1)

    def test_work_order_summary_excludes_completed(self):
        self._work_order("Completed")
        self.assertEqual(self._work_order_summary().open_count, 0)

    def test_work_order_summary_excludes_closed(self):
        self._work_order("Closed")
        self.assertEqual(self._work_order_summary().open_count, 0)

    def test_work_order_summary_excludes_deleted(self):
        self._work_order("Deleted")
        self.assertEqual(self._work_order_summary().open_count, 0)

    def test_work_order_summary_counts_cancelled(self):
        self._work_order("Cancelled")
        self.assertEqual(self._work_order_summary().open_count, 1)

    def test_work_order_summary_mixed_statuses(self):
        for status in ("Open", "Open", "In Progress", "Completed", "Closed", "Deleted", "Cancelled"):
            self._work_order(status)
        self.assertEqual(self._work_order_summary().open_count, 4)

    def test_work_order_summary_tenant_isolation(self):
        self._work_order("Cancelled")
        with self.Session() as db:
            other = Company(id=uuid4(), name="Other KPI Company", status="active")
            db.add(other)
            db.commit()
            other_id = other.id
        self._work_order("Open", company_id=other_id)
        self._work_order("In Progress", company_id=other_id)
        response = self.client.get(
            "/api/v1/work-orders/summary",
            headers={**self._admin_headers(), "X-Company-ID": str(other_id)},
            params={"company_id": str(other_id)},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"open_count": 1})

    def test_work_order_list_response_shape_unchanged(self):
        order_id = self._work_order("Open")
        self._work_order("Deleted")
        headers = self._admin_headers()
        response = self.client.get("/api/v1/work-orders", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(set(response.json()[0]), {
            "id", "company_id", "customer_id", "asset_id", "service_request_id", "display_id",
            "title", "description", "priority", "status", "assigned_technician_id",
            "scheduled_start", "scheduled_end", "notes", "created_at",
        })
        self.assertEqual(response.json()[0]["id"], str(order_id))
        response = self.client.get(f"/api/v1/work-orders/{order_id}", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)

    def test_work_order_summary_static_route(self):
        self._work_order("Cancelled")
        response = self.client.get("/api/v1/work-orders/summary", headers=self._admin_headers())
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"open_count": 1})

    def test_work_order_summary_requires_service_read_permission(self):
        response = self.client.get("/api/v1/work-orders/summary")
        self.assertEqual(response.status_code, 401, response.text)
        with self.Session() as db:
            technician = User(
                company_id=self.company_id, email="kpi-tech@example.com", full_name="Tech",
                password_hash=self.password_hash, role="technician",
            )
            db.add(technician)
            db.commit()
            headers = {"Authorization": f"Bearer {create_access_token(str(technician.id))}"}
        # All valid roles currently have service:read; remove only that permission
        # temporarily to verify the summary uses the existing authorization gate.
        with patch.dict(ROLE_PERMISSIONS, {
            Role.TECHNICIAN: ROLE_PERMISSIONS[Role.TECHNICIAN] - {Permission.SERVICE_READ},
        }):
            response = self.client.get("/api/v1/work-orders/summary", headers=headers)
            self.assertEqual(response.status_code, 403, response.text)
        response = self.client.get("/api/v1/work-orders/summary", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)

    def test_dashboard_consumes_backend_open_count(self):
        from streamlit.testing.v1 import AppTest

        with patch("modules.dashboard.list_records") as lists, patch("modules.dashboard.request") as request:
            lists.side_effect = lambda resource: {
                "customers": [{"id": "customer"}], "inventory": [{"id": "item"}],
                "service-visits": [{"id": "visit"}],
            }[resource]
            request.side_effect = lambda method, path: (
                {"open_count": 17} if path == "/work-orders/summary" else {"net_profit": "12.34"}
            )
            ui = AppTest.from_string("from modules.dashboard import app\napp()").run()
            self.assertEqual(len(ui.exception), 0)
            self.assertEqual([metric.value for metric in ui.metric], ["1", "1", "17", "1", "12.34 EGP"])
            request.assert_any_call("GET", "/work-orders/summary")
            request.assert_any_call("GET", "/profitability/summary")
            self.assertEqual([call.args[0] for call in lists.call_args_list], ["customers", "inventory", "service-visits"])
