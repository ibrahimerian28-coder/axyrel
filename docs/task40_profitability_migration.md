# Task 40 — Profitability Migration

## Scope
Move profitability calculations from the legacy `profits.py` UI placeholder into the PostgreSQL service/repository architecture. Profitability is a **derived domain** and therefore does not introduce a new persistence table in this task. It derives revenue from invoices and costs from active expenses.

## Derived rules
- Invoiced revenue = sum of `Invoice.total` for statuses `Sent`, `Paid`, and `Overdue`.
- Collected revenue = sum of `Invoice.paid_amount` for the same revenue statuses.
- Expenses = sum of `Expense.amount` where status is `Active`.
- Net profit = invoiced revenue - expenses.
- Cash net profit = collected revenue - expenses.
- Profit margin = net profit / invoiced revenue × 100; zero when revenue is zero.
- All aggregates are tenant-scoped by `company_id`.
- Date filters apply to invoice `issue_date` and expense `expense_date`.

## Why no profitability table?
Profitability is a reporting/derived domain. Persisting a duplicate total would create synchronization risks. The repository calculates aggregates from the authoritative Invoice and Expense records.

## Legacy note
The legacy `modules/profits.py` is only a Streamlit placeholder and does not expose reliable calculation rules. Therefore the rules above are an explicit domain inference for the new architecture and must be validated against the business owner's intended accounting rules before production.

## Deferred
- Profitability UI: Task 45
- API endpoints: Task 44
- Billing integration workflows: Task 56
- Production data migration: Task 62
