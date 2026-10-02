# Task 47 — Final Accepted Checkpoint

## Status

- Task: Task 47 — Move Remaining Business Logic out of UI.
- Status: **ACCEPTED** by the owner, pending checkpoint commit/push.
- Acceptance date: **2026-10-02**.
- Branch: `checkpoint/pre-gemini-task46`.
- Baseline before Task 47: `84b96bbb7fd778b9a8bc4d78c11b23236b843262`.
- Task 48 has **NOT started**.

## Owner Decisions

1. **Invoice total:** The backend calculates total on CREATE when total is omitted. Explicit caller-supplied total remains supported, including zero. PATCH behavior remains unchanged.
2. **Service Visit relationship inheritance:** Current Work Order → Customer/Asset/Technician population remains a UI form preset. No new inheritance semantics were introduced. A8 required no Task 47 production change.
3. **Invoice negative-value widget restrictions:** Existing UI restrictions remain unchanged. No broader backend monetary-validation policy was introduced. Validation standardization remains Task 48 scope.

## Implemented Scope

- **A1 — Inventory valuation:** Moved behind the API/service boundary using backend Decimal monetary arithmetic.
- **A2 — Inventory minimum-stock classification:** Moved behind the API/service boundary, reusing existing InventoryBusinessRules. Only backend CRITICAL displays as UI "Low"; backend LOW continues displaying as "Good". Search does not alter summary scope.
- **A3 — Invoice CREATE total:** Moved to InvoiceService using Decimal: `max(Decimal("0"), subtotal - discount + tax)` when total is absent. Missing components use existing zero defaults. Explicit totals, including zero, remain supported; PATCH behavior and monetary-column handling remain unchanged.
- **A4 — Expense total:** Moved behind the API/service boundary. Scope remains all non-Deleted expenses, including non-Active records.
- **A5 — Open Work Order KPI:** Moved behind the API/service boundary. Completed, Closed and Deleted remain excluded. Cancelled remains counted to preserve existing behavior.
- **A6 — Customer CREATE name:** Backend trims leading/trailing whitespace and rejects blank names before repository mutation. PATCH behavior remains unchanged.
- **A7 — Inventory CREATE name:** Backend trims leading/trailing whitespace and rejects blank names before repository mutation. PATCH behavior remains unchanged.
- **A8 — Service Visit relationship inheritance:** No production change by explicit owner decision.

Active Streamlit paths delegate the moved authoritative calculations and rules to the backend. Friendly form validation, formatting and presentation remain UI responsibilities.

## API Additions

| Additive read-only endpoint | Existing permission |
|---|---|
| `GET /api/v1/inventory/summary` | `INVENTORY_READ` |
| `GET /api/v1/expenses/summary` | `EXPENSE_READ` |
| `GET /api/v1/work-orders/summary` | `SERVICE_READ` |

All three endpoints use authenticated tenant context and preserve tenant isolation. Static summary routes precede ID routes. Existing list response shapes remain unchanged, and no breaking API contract change was introduced.

## Verification Evidence

| Verification | Result |
|---|---|
| Task 47 focused tests | 58/58 PASS |
| Task 46 authentication | 10/10 PASS |
| Task 46 Service Visit | 6/6 PASS |
| Task 46 combined regression baseline | 16/16 PASS |
| `git diff --check` | PASS |
| Complete cumulative diff review | PASS — no blocking defects |

The final verification ran all three suites using the project interpreter and reviewed the complete cumulative diff, including the new test file. This document records that evidence; tests were not rerun for this documentation step.

## Architecture / Scope

Architecture remains:

Streamlit → FastAPI → Services / Business Rules → Repositories → PostgreSQL.

Design Freeze remained intact. Task 47 introduced:

- No database schema changes.
- No ORM model changes.
- No migrations.
- No ERD changes.
- No legacy restoration/removal.
- No Task 48 work.
- No Task 49 work.
- No Tasks 50–70 work.
- No Service Visit lifecycle changes.
- No warehouse transaction changes.
- No technician-stock changes.
- No new product features.

The added API response schemas do not change the database schema.

## Non-Blocking Observations

- No new live browser acceptance session was performed during final verification.
- UI behavior was verified through code inspection and Streamlit AppTest coverage.
- Existing dependency/UI deprecation warnings and Git line-ending notices were non-blocking.
- Cancelled remaining counted in the Open Work Order KPI is intentional behavior preservation for Task 47, not a new semantic decision.
- Backend LOW continuing to display as UI "Good" is intentional compatibility preservation for Task 47.

## Final Acceptance

**Task 47 is ACCEPTED.** All approved Task 47 implementation scope is complete. No blocking defects remain. Task 48 has not started.

Checkpoint commit/push remains pending. No commit, push or merge is authorized by this documentation step.

Next planned task after checkpoint commit/push: **Task 48 — Standardize API Validation / Errors**.
