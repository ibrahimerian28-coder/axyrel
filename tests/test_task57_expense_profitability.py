"""OD-18 derived reporting acceptance using the disposable billing fixture."""
import unittest
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import test_task56_order_billing_integration as billing_fixture
from backend.models.expense import Expense
from backend.models.invoice import Invoice
from backend.models.user import User
from backend.services.profitability import ProfitabilityService
from backend.services.expense import ExpenseService


class Task57ExpenseProfitabilityTests(unittest.TestCase):
    # Reuse only fixture setup, not the billing test methods.
    setUpClass = classmethod(billing_fixture.Task56OrderBillingTests.setUpClass.__func__)
    tearDownClass = classmethod(billing_fixture.Task56OrderBillingTests.tearDownClass.__func__)
    setUp = billing_fixture.Task56OrderBillingTests.setUp

    def _expense(self, **data):
        response = self.client.post("/api/v1/expenses", headers=self.headers,
                                    json={"category": "Travel", "amount": "10.25", "expense_date": "2026-10-02", **data})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _summary(self, **params):
        response = self.client.get("/api/v1/profitability/summary", headers=self.headers, params=params)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def _breakdown(self, **params):
        response = self.client.get("/api/v1/profitability/expenses", headers=self.headers, params=params)
        self.assertEqual(response.status_code, 200, response.text)
        return {row["category"]: Decimal(row["amount"]) for row in response.json()}

    def _change(self, record, data):
        response = self.client.patch(f"/api/v1/expenses/{record['id']}", headers=self.headers, json=data)
        self.assertEqual(response.status_code, 200, response.text)

    def test_expense_api_create_is_immediately_derived_without_revenue(self):
        self._expense()
        result = self._summary()
        self.assertEqual(Decimal(result["expenses"]), Decimal("10.25"))
        self.assertEqual(Decimal(result["net_profit"]), Decimal("-10.25"))
        self.assertEqual(Decimal(result["cash_net_profit"]), Decimal("-10.25"))
        self.assertEqual(Decimal(result["profit_margin_percent"]), 0)
        self.assertEqual(result["expense_count"], 1)
        self.assertEqual(self._breakdown(), {"Travel": Decimal("10.25")})

    def test_only_active_expenses_count_and_expense_summary_stays_separate(self):
        for status, amount in (("Active", "10"), ("Cancelled", "20"), ("Inactive", "30"), ("Deleted", "40")):
            self._expense(status=status, amount=amount)
        result = self._summary()
        self.assertEqual(Decimal(result["expenses"]), 10)
        self.assertEqual(result["expense_count"], 1)
        self.assertEqual(self._breakdown(), {"Travel": Decimal("10")})
        response = self.client.get("/api/v1/expenses/summary", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(Decimal(response.json()["total_amount"]), 60)

    def test_amount_category_and_date_patch_are_reflected(self):
        expense = self._expense()
        self._change(expense, {"amount": "12.34", "category": "  Parts  ", "expense_date": "2026-10-03"})
        self.assertEqual(Decimal(self._summary()["expenses"]), Decimal("12.34"))
        self.assertEqual(self._breakdown(), {"Parts": Decimal("12.34")})
        self.assertEqual(self._summary(end_date="2026-10-02")["expense_count"], 0)

    def test_status_patch_removes_and_restores_report_population(self):
        expense = self._expense()
        self._change(expense, {"status": "Cancelled"})
        self.assertEqual(self._summary()["expense_count"], 0)
        self.assertEqual(self._breakdown(), {})
        self._change(expense, {"status": "Active"})
        self.assertEqual(self._summary()["expense_count"], 1)

    def test_soft_delete_removes_expense_from_both_reports(self):
        expense = self._expense()
        response = self.client.delete(f"/api/v1/expenses/{expense['id']}", headers=self.headers)
        self.assertEqual(response.status_code, 204, response.text)
        self.assertEqual(self._summary()["expense_count"], 0)
        self.assertEqual(self._breakdown(), {})
        with self.Session() as db:
            self.assertEqual(db.get(Expense, UUID(expense["id"])).status, "Deleted")
            self.assertEqual(ExpenseService().get_summary(db, self.company).total_amount, 0)

    def test_inclusive_date_filters_and_one_sided_bounds(self):
        for day, amount in (("2026-10-01", "1"), ("2026-10-02", "2"), ("2026-10-03", "3")):
            self._expense(expense_date=day, amount=amount)
        for params, expected, count in (({"start_date": "2026-10-02", "end_date": "2026-10-02"}, "2", 1),
                                        ({"start_date": "2026-10-02"}, "5", 2),
                                        ({"end_date": "2026-10-02"}, "3", 2)):
            result = self._summary(**params)
            self.assertEqual(Decimal(result["expenses"]), Decimal(expected))
            self.assertEqual(result["expense_count"], count)
            self.assertEqual(sum(self._breakdown(**params).values()), Decimal(expected))

    def test_decimal_expenses_category_totals_and_counts(self):
        self._expense(amount="0.10", category="A")
        self._expense(amount="0.20", category="A")
        self._expense(amount="0.15", category="B")
        result = self._summary()
        self.assertEqual(Decimal(result["expenses"]), Decimal("0.45"))
        self.assertEqual(result["expense_count"], 3)
        self.assertEqual(self._breakdown(), {"A": Decimal("0.30"), "B": Decimal("0.15")})

    def test_existing_revenue_statuses_formulas_and_margin_are_preserved(self):
        for status, total, paid in (("Sent", "100", "20"), ("Paid", "50", "50"), ("Overdue", "25", "5"),
                                     ("Draft", "1000", "1000"), ("Cancelled", "2000", "2000"), ("Deleted", "3000", "3000")):
            response = self.client.post("/api/v1/invoices", headers=self.headers,
                                        json={"customer_id": str(self.customer), "invoice_number": str(uuid4()),
                                              "issue_date": "2026-10-02", "status": status, "total": total, "paid_amount": paid})
            self.assertEqual(response.status_code, 201, response.text)
        self._expense(amount="25")
        result = self._summary()
        for field, expected in (("invoiced_revenue", "175"), ("collected_revenue", "75"), ("net_profit", "150"),
                                ("cash_net_profit", "50"), ("profit_margin_percent", "85.71")):
            self.assertEqual(Decimal(result[field]), Decimal(expected))
        self.assertEqual(result["invoice_count"], 3)

    def test_tenant_isolation_applies_to_expenses_breakdown_and_revenue(self):
        self._expense(amount="5")
        with self.Session() as db:
            db.add(Expense(company_id=self.foreign_company, category="Foreign", amount=Decimal("999"),
                           expense_date=date(2026, 10, 2), status="Active"))
            foreign_invoice = db.get(Invoice, self.foreign_invoice)
            foreign_invoice.status, foreign_invoice.total = "Paid", Decimal("999")
            db.commit()
        result = self._summary()
        self.assertEqual(Decimal(result["expenses"]), 5)
        self.assertEqual(Decimal(result["invoiced_revenue"]), 0)
        self.assertEqual(self._breakdown(), {"Travel": Decimal("5")})

    def test_invalid_expense_patch_has_no_reporting_effect(self):
        expense = self._expense()
        before = self._summary()
        response = self.client.patch(f"/api/v1/expenses/{expense['id']}", headers=self.headers,
                                     json={"category": "  ", "amount": "100"})
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self._summary(), before)

    def test_empty_report_and_direct_service_use_the_same_population(self):
        result = self._summary()
        self.assertEqual(result["expense_count"], 0)
        self.assertEqual(self._breakdown(), {})
        self._expense(amount="7", status="Active")
        self._expense(amount="20", status="Inactive")
        with self.Session() as db:
            report = ProfitabilityService().summary(db, self.company)
            self.assertEqual(report.expenses, Decimal("7"))
            self.assertEqual(ExpenseService().get_summary(db, self.company).total_amount, Decimal("27"))

    def test_auth_permission_and_query_validation_contracts(self):
        for route in ("summary", "expenses"):
            self.assertEqual(self.client.get(f"/api/v1/profitability/{route}").status_code, 401)
            self.assertEqual(self.client.get(f"/api/v1/profitability/{route}", headers=self.headers,
                                             params={"start_date": "invalid"}).status_code, 422)
        with self.Session() as db:
            db.get(User, self.admin).role = "technician"
            db.commit()
        for route in ("summary", "expenses"):
            self.assertEqual(self.client.get(f"/api/v1/profitability/{route}", headers=self.headers).status_code, 403)


if __name__ == "__main__":
    unittest.main()
