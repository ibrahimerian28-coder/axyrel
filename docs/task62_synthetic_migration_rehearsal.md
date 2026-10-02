# Task 62 — Synthetic migration rehearsal / readiness

Authority: OD-22. No real existing business data was accessed or migrated. No production target, import tool, source connector, baseline procedure or new business mapping is introduced. Acceptance is limited to the rehearsal below.

## Existing capabilities

| Capability | Accepted evidence | Boundary |
|---|---|---|
| Numbered schema migrations | backend/scripts/init_database.py, migrations/001 and 003–014 | Thirteen files, raw-byte SHA-256 ledger verification, ordered pending execution and atomic success records; untracked existing schemas refused. Schema migration is not source-data import. |
| Legacy Inventory row mapping | backend/migrations/inventory_data.py; docs/TASK32_INVENTORY_DATA_MIGRATION.md | Dedicated pure mapper for five Inventory fields. No live source reader or production transfer. |
| Tenant-scoped Inventory persistence | backend/schemas/inventory.py, backend/services/inventory.py, backend/repositories/inventory.py | Explicit company context required; generated UUIDs; existing same-company name uniqueness. No source-company or source-ID mapping. |
| Stock movement relationships | backend/models/inventory_transaction.py | Existing item FK and positive quantity check. Synthetic integrity fixture only; no approved historical movement conversion. |
| Schedule / Visit historical event conversion | migrations/012, 013; docs/task52_timezone_migration.md; docs/task53_timezone_migration.md | OD-14 Cairo interpretation, ambiguity rejection and targeted UTC instants. Prior accepted disposable tests; not rerun or extended here. Actual writer evidence must be reviewed before real upgrade. |
| Invoice, Contract and Expense foundations | docs/task37_billing_invoicing.md, docs/task38_service_contract_migration.md, docs/task39_expenses_migration.md | Target schema/services exist; source-data transfer was deferred. Target fields do not establish authoritative source mappings. Expenses source mapping is explicitly unresolved. |

Repository inventory found no additional dedicated legacy-row mapper in backend/migrations, and no approved source export or real-transfer plan. Synthetic rows are literals in the test; no legacy connector or dataset is loaded.

## Verified Inventory mapping

| Input field | Existing mapper behavior |
|---|---|
| item_name | str(value).strip(); reject an empty result |
| quantity, min_limit, ideal_stock | int(float(value)); TypeError/ValueError become zero; negatives clamp to zero; fractional values truncate |
| cost_price | Decimal(str(value)); InvalidOperation/TypeError/ValueError become Decimal zero; negative values clamp to zero |
| status | Always Active, irrespective of supplied source status |
| Any other key, including source id/company_id | Not mapped |

These are existing implementation facts, not a newly approved real-data cleansing policy. Non-finite and unusual Python values are not comprehensively supported: for example infinite quantity raises OverflowError. The mapper is not a strict import validator and can ignore unknown fields. The rehearsal does not claim every unsupported input is rejected. InventoryItemCreate additionally enforces accepted target name length and nonnegative fields; InventoryService rejects blank CREATE names. Finite two-decimal prices are used to avoid inventing a rounding policy.

Valid representative rows retain mapped values after PostgreSQL persistence. Mapping is deterministic for the tested inputs and does not mutate the input dictionary; generated database UUIDs are deliberately not deterministic. Synthetic tenant UUIDs are supplied explicitly, not derived from a legacy row. Generated item IDs are used for synthetic FK references; this does not define historical ID translation. Stock movement fixtures do not reconcile quantity or invent opening-balance/history semantics.

Existing repository reads isolate companies; identical names in different companies succeed, while duplicate trimmed names within one company produce the accepted structured PostgreSQL uniqueness violation. No overwrite, merge or duplicate resolution is introduced. An explicit test transaction rolls back all synthetic rows on either mapping or database failure; this verifies transaction capability, not a newly selected production batch/checkpoint policy. Missing item references fail PostgreSQL FK validation. Migration history remains unchanged after the rehearsal and a verified rerun skips all thirteen files.

## Reproduce safely

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_task62_migration_rehearsal.py
```

Eight cases use the accepted disposable fixture from Task 60. The configured URL supplies only local server access via maintenance postgres; the configured application database is never connected to. Nonlocal hosts are refused. A UUID-named axyrel_task60_test_* database is created, built through the tracked initializer and dropped after connections close. No ORM create_all, automatic ledger stamping, production credentials or real data are used. Tests require local CREATE DATABASE privilege and fail rather than silently skipping missing infrastructure.

## Before any future real-data migration

Owner decisions/evidence are required for the source snapshot and required domains; field definitions and encodings; company ownership; source-ID to target-ID/reference translation; missing references; duplicate handling; invalid rows and whether historical Inventory coercions are acceptable; precision/rounding; statuses; monetary/date/time meanings; and opening stock versus movement-history reconciliation. Expenses category/payment/vendor/reference and other source fields remain unresolved. No mapping for invoices, contracts or other domain sources is inferred from their target schemas.

Also require an approved target and source-access scope, backup/restore and dry-run review, reconciliation totals, transaction/retry/resume policy, and rollback/cutover authorization. Existing untracked databases need a separately owner-approved ledger baseline/reconciliation; OD-21 remains in force. No generic importer or real-data command is provided. Task 63 remains a separate validation task and must retain the absence of any real-data migration claim.
