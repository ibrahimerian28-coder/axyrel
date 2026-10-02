# Task 48 — Final Checkpoint

## 1. Task Identity

- Task: **Task 48 — Standardize API Validation / Errors**.
- Status: **ACCEPTED**.
- Acceptance date: **2026-10-02**.
- Implementation and final acceptance were completed before the checkpoint commit.

## 2. Baseline

- Project root: `D:\Axyrel_BACKUP_BEFORE_GEMINI`.
- Branch: `checkpoint/pre-gemini-task46`.
- Pre-Task48 committed baseline: `c6786f840c332763c7cadefc751d3f722e8559ce`.
- Task 47: **ACCEPTED / COMMITTED / PUSHED**.
- Task 49: **NOT STARTED**.

## 3. Implemented Scope

### Phase 1 — Technician Stock API Boundary

Negative quantity service `ValueError` is translated to HTTP 400 on CREATE and quantity-update paths. The service remains the owner of the business rule. Rejected requests cause no persisted stock mutation. Zero and positive quantities remain valid; authentication, permissions, and existing 404 behavior are preserved.

### Phase 2 — Standard API Error Handling

HTTP 409 requires a psycopg PostgreSQL error, SQLSTATE exactly `23505`, and an exact allowlisted constraint name from structured diagnostics. Human-readable database messages are not parsed.

| Approved constraint | HTTP status | Fixed detail |
|---|---|---|
| `uq_inventory_items_company_item_name` | 409 | An inventory item with this name already exists. |
| `uq_technician_stock_company_technician_item` | 409 | Stock for this technician and inventory item already exists. |
| `uq_invoices_company_number` | 409 | An invoice with this number already exists. |
| `uq_service_contracts_company_number` | 409 | A service contract with this number already exists. |

Unknown/unapproved persistence errors remain safe HTTP 500, including unknown uniqueness, primary-key, foreign-key, CHECK, NOT NULL, and unsupported errors. Unexpected errors return exactly:

```json
{"detail":"Internal Server Error"}
```

Actual internal exceptions and tracebacks are logged server-side. SQL, parameters, constraint names, stack traces, and internal exception messages are not exposed in these client responses.

Existing FastAPI/application contracts are preserved: 400, 401, `WWW-Authenticate: Bearer`, 403, 404, structured 422, and explicit `HTTPException` behavior. No global `ValueError` handler was introduced.

### Phase 3 — CREATE/PATCH Text Validation Parity

Parity was implemented only for Expense `category`, Invoice `invoice_number`, and Service History `service_type` and `summary`.

PATCH reuses the existing CREATE validators for supplied non-null values. Normalization and blank rejection are preserved. Invalid PATCH input returns 422 before persistence. CREATE behavior and omission/null semantics remain unchanged. Task 47 invoice total behavior is preserved; no new monetary policy was introduced.

### Phase 4 — Service Contract Effective-Date PATCH Parity

CREATE and effective-state PATCH validation share the existing rule: `end_date >= start_date` when `end_date` is present. CREATE behavior and the wording `end_date must be on or after start_date` remain unchanged.

- Start-only PATCH uses the persisted end date.
- End-only PATCH uses the persisted start date.
- Both supplied dates use the supplied values.
- Neither supplied date adds no range validation.
- Explicit `end_date=null` remains allowed and clears the optional end date.
- Equality remains valid.
- Invalid effective state is rejected before repository mutation with HTTP 400.
- Malformed schema/type input remains 422.
- Missing or tenant-hidden targets retain existing 404 behavior; the tenant-scoped target is resolved before effective-state validation.

Tenant isolation and other update behavior remain unchanged. Explicit null semantics for required `start_date` were not redefined.

## 4. Files Changed

Cumulative Task 48 implementation and test files:

- `backend/api/v1/service_contracts.py`
- `backend/api/v1/technician_stock.py`
- `backend/main.py`
- `backend/schemas/expense.py`
- `backend/schemas/invoice.py`
- `backend/schemas/service_contract.py`
- `backend/schemas/service_history.py`
- `backend/services/service_contract.py`
- `backend/api/errors.py`
- `tests/test_task48_api_validation_errors.py`

Checkpoint documentation: `docs/task48_final_checkpoint.md`.

## 5. Final Test Results

| Final acceptance verification | Result |
|---|---|
| Task 48 | 60/60 PASS |
| Task 47 regression | 58/58 PASS |
| Task 46 authentication | 10/10 PASS |
| Task 46 Service Visit | 6/6 PASS |
| Total executed acceptance/regression tests | 134/134 PASS |
| Acceptance matrix | 30/30 PASS |
| `git diff --check` | PASS |
| Complete cumulative diff review | READY FOR FINAL ACCEPTANCE — no blocking findings |

All four suites were rerun for the final acceptance review using the project interpreter with `-B`. This document records that evidence; the 134 tests were not rerun for the documentation-only step.

## 6. PostgreSQL Test Limitation

The PostgreSQL uniqueness classifier was tested using real psycopg exception classes with simulated structured PostgreSQL diagnostics. Disposable SQLite tests exercised duplicate failures and transaction rollback.

Actual isolated PostgreSQL integration writes were not performed because no isolated PostgreSQL test database was configured. The configured application database was not modified.

This limitation was explicitly reviewed and accepted as **NON-BLOCKING** for Task 48. Actual PostgreSQL integration testing is not claimed.

## 7. Timezone / Timestamp Carry-Forward

Task 48 intentionally did **not** implement full Schedule or Service Visit effective-state timestamp PATCH parity because Axyrel currently has no coherent timezone policy. This requirement is **not closed and not forgotten**; it is carried forward to Tasks 52–53.

### Task 52 — Work Order → Scheduling integration

Before Task 52 final acceptance:

- Resolve and approve Axyrel's official Date/Time & Timezone policy.
- Resolve the outstanding Schedule effective-state timestamp validation under that approved policy.

### Task 53 — Scheduling → Service Visit integration

Before Task 53 final acceptance:

- Verify/apply the approved policy to Service Visit.
- Resolve the outstanding Service Visit effective-state timestamp validation.

Long-term architectural direction identified during Task 48:

- Timezone-aware instants.
- UTC normalization.
- Separate timezone metadata where required.
- Calendar-only business dates remain `DATE`.

This is architectural direction only. It does **not** authorize schema changes, migrations, historical timestamp conversion, or company/user timezone fields. Those require later explicit approval.

## 8. Out of Scope / Unchanged

Task 48 introduced none of the following:

- ERD, ORM model, migration, database schema, or database configuration changes.
- Authentication-context standardization or Task 49 work.
- Lifecycle or relationship redesign.
- Customer or inventory PATCH normalization.
- New monetary policy.
- Schedule or Service Visit timestamp implementation.
- Timezone conversion.
- UI features or new product modules/workflows.

Design Freeze remained intact. The API error-handling helper is limited to the approved Task 48 scope.

## 9. Acceptance Summary

- Task 48 status: **ACCEPTED**.
- Blocking defects: **NONE**.
- Known non-blocking limitation: No isolated PostgreSQL integration write test.
- Deferred tracked requirement: Date/Time & Timezone policy and outstanding Schedule/Service Visit timestamp parity → Tasks 52–53.
- Next official task: **Task 49 — Standardize Authentication Context**.

**TASK 49 HAS NOT STARTED.**

## 10. Git State

At checkpoint-document creation time, Task 48 implementation is accepted. Implementation changes and this checkpoint document remain uncommitted. No Task 48 push or merge has occurred, and main remains untouched.

The current committed HEAD remains the pre-Task48 baseline recorded above. The future Task 48 checkpoint commit hash is not yet available.
