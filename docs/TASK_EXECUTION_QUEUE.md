# Axyrel Task Execution Queue

Date: 2026-10-02. Source: docs/90-tasks.rtf, with the explicit owner numbering clarification recorded in AUTONOMOUS_OWNER_DECISIONS.md. Detailed Tasks 18–90 define current execution. The trailing numbered phase summary is excluded. Historical unavailable titles do not block continuation from Task 50.

Tasks 18–45 completion is historical per the MASTER handoff's Task 46 checkpoint; no individual acceptance evidence is invented. Tasks 46–49 have accepted checkpoints and completed Git finalization. Their checkpoint Git wording describes creation-time history, not current status. Sequential execution is required; do not replay historical tasks.

Task 46 retains the roadmap title below; its accepted checkpoint additionally records the auth/security and Service Visit acceptance work. Accepted evidence and owner scope decisions remain authoritative.

## Task 01 — Final Logical ERD v1.0

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 02 — Final Database Schema v1.0

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 03 — Database Constraints & Indexes Validation

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 04 — Backend / API Architecture v1.0

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 05 — Map Existing Code → New Architecture

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 06 — Update Refactoring Plan

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 07 — Continue Refactoring from Task 18/90

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 08 — Official title unavailable in current historical source

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 09 — Official title unavailable in current historical source

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 10 — Official title unavailable in current historical source

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 11 — Official title unavailable in current historical source

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 12 — Official title unavailable in current historical source

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 13 — Official title unavailable in current historical source

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 14 — Official title unavailable in current historical source

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 15 — Official title unavailable in current historical source

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 16 — Official title unavailable in current historical source

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 17 — Official title unavailable in current historical source

Status: HISTORICAL / PRE-CURRENT-CHECKPOINT
Execution relevance: NONE for current autonomous continuation

## Task 18 — Establish New Project / Backend Structure

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 19 — Replace Old Data Access Foundation

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 20 — Establish Centralized Configuration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 21 — Authentication Foundation

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 22 — Authorization / Roles / Permissions

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 23 — Company / Tenant Context

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 24 — Tenant Isolation

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 25 — Customer Module Migration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 26 — Asset Module Migration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 27 — Service Request Migration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 28 — Work Order Migration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 29 — Scheduling Migration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 30 — Service Visit Migration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 31 — Service History Migration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 32 — Inventory Data Migration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 33 — Inventory Repository / Service

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 34 — Inventory Transactions

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 35 — Technician Stock

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 36 — Inventory Business Rules

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 37 — Billing / Invoicing Migration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 38 — Service Contract Migration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 39 — Expenses Migration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 40 — Profitability Migration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 41 — Notifications

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 42 — Activity / Audit Log

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 43 — Settings / Configuration

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 44 — Build API Endpoints

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 45 — Connect Streamlit UI to API

Status: HISTORICAL / COMPLETED BEFORE CURRENT TRUSTED CHECKPOINT

## Task 46 — Remove Direct Database Access from Streamlit

Status: DONE / ACCEPTED / COMMITTED / PUSHED

## Task 47 — Move Remaining Business Logic out of UI

Status: DONE / ACCEPTED / COMMITTED / PUSHED

## Task 48 — Standardize API Validation / Errors

Status: DONE / ACCEPTED / COMMITTED / PUSHED

## Task 49 — Standardize Authentication Context

Status: DONE / ACCEPTED / COMMITTED / PUSHED

## Task 50 — Customer → Asset Integration

Status: DONE / ACCEPTED
Dependencies/Carry-forward: See docs/task50_final_checkpoint.md; committed completion state must be verified against the Task 50 commit and actual remote before continuing.

## Task 51 — Service Request → Work Order Integration

Status: DONE / ACCEPTED
Dependencies/Carry-forward: Owner Option A recorded in OD-13; see docs/task51_final_checkpoint.md. Verify task commit/push before continuing.

## Task 52 — Work Order → Scheduling Integration

Status: DONE / ACCEPTED
Dependencies/Carry-forward: OD-14 adopted; Schedule effective-state validation and reviewed event-only TIMESTAMPTZ migration verified on disposable PostgreSQL. See docs/task52_final_checkpoint.md and docs/task52_timezone_migration.md. Verify task commit/push; production migration was not executed.

## Task 53 — Scheduling → Service Visit Integration

Status: DONE / ACCEPTED
Dependencies/Carry-forward: OD-15 Option A implemented; OD-14 applied to actual_start_at/actual_end_at with effective-state validation and reviewed disposable-PostgreSQL migration verification. See docs/task53_final_checkpoint.md and docs/task53_timezone_migration.md. Verify commit/push before continuing; production migration was not executed.

## Task 54 — Service Visit → Service History Integration

Status: DONE / ACCEPTED
Dependencies/Carry-forward: OD-16 Option A implemented; see docs/task54_final_checkpoint.md. Verify task commit/push before continuing. No Service History timestamp or schema changes.

## Task 55 — Work Order → Inventory Integration

Status: DONE / ACCEPTED
Dependencies/Carry-forward: Existing accepted Work Order → Service Visit → inventory workflow verified with order-level acceptance tests; see docs/task55_final_checkpoint.md. No new direct consumption path or production behavior change. Verify commit/push; this is the third/final task of the resumed batch.

## Task 56 — Work Order → Billing Integration

Status: DONE / ACCEPTED
Dependencies/Carry-forward: OD-17 Option A implemented; see docs/task56_final_checkpoint.md. Verify commit/push before continuing. Optional links and approved Invoice totals preserved; no schema or monetary-rule changes.

## Task 57 — Expenses → Profitability Integration

Status: DONE / ACCEPTED
Dependencies/Carry-forward: OD-18 confirms Active-only Profitability expenses and separate non-Deleted Expense Summary semantics. Existing derived integration verified; see docs/task57_final_checkpoint.md. Verify commit/push before continuing. No production accounting-policy or schema changes.

## Task 58 — Notifications / Audit Integration

Status: DONE / ACCEPTED
Dependencies/Carry-forward: OD-19 Option A verified existing explicit API flows, tenant isolation, Notification state and Audit API/service immutability; see docs/task58_final_checkpoint.md. Automatic event generation remains deferred. Verify commit/push; third/final task of this resumed batch.

## Task 59 — Create Production Database

Status: DONE / ACCEPTED
Dependencies/Carry-forward: OD-20 defines isolated local PostgreSQL production-schema readiness, not live deployment. Complete accepted SQL chain and schema verified; see docs/task59_final_checkpoint.md and docs/task59_database_creation_procedure.md. Verify commit/push before continuing. No real production target, credentials or data modified.

## Task 60 — Create Migrations

Status: DONE / ACCEPTED
Dependencies/Carry-forward: OD-21 tracked numeric SQL migrations with raw SHA-256 checksums and per-migration atomic ledger records. See docs/task60_final_checkpoint.md and the updated Task 59 deployment procedure. Verify commit/push before continuing. Existing untracked schemas still require owner-approved reconciliation; no live production database changed.

## Task 61 — Create Required Indexes / Constraints

Status: DONE — ACCEPTED

Dependencies/Carry-forward: Migration 014 adds the three missing existing model-declared non-unique indexes. Existing primary/foreign keys, named uniqueness and inventory checks verified on disposable PostgreSQL. See docs/task61_final_checkpoint.md. Verify commit/push before stopping at the three-task batch limit.

## Task 62 — Migrate Required Existing Data

Status: DONE — ACCEPTED (OD-22 synthetic rehearsal/readiness only; no real data migrated)

Dependencies/Carry-forward: Existing Inventory mapping and synthetic PostgreSQL persistence/integrity verified. Expenses and other real-source mappings remain unresolved. See docs/task62_synthetic_migration_rehearsal.md and docs/task62_final_checkpoint.md. Preserve OD-21 tracking and OD-22 real-data deferral.

## Task 63 — Validate Migrated Data

Status: DONE — ACCEPTED (OD-23 synthetic validation/readiness only)

Dependencies/Carry-forward: Independent literal source-to-target expectations, tenant partitions, generated references and repeatability verified with Task 62 regression. No real data validated. See docs/task63_final_checkpoint.md; real-data policies remain unresolved under OD-22/23.

## Task 64 — Remove Obsolete Google Sheets Persistence

Status: DONE — ACCEPTED

Dependencies/Carry-forward: Sheets CSV/Apps Script fallback removed; unused external helper removed; existing supported API adapters retained. Unsupported facade reads fail explicitly; writes return False without external access. Compatibility dependency cleanup remains Task 65. See docs/task64_final_checkpoint.md. Stop after push verification at the three-task batch limit.

## Task 65 — Remove Obsolete data_service Dependencies

Status: DONE — ACCEPTED

Carry-forward: Removed unused facade/consumer dependency group; active API routing and contracts verified. See docs/task65_final_checkpoint.md. Historical Task 64 facade tests replaced by current runtime dependency checks.

## Task 66 — Remove Obsolete Legacy Business Logic

Status: DONE — ACCEPTED

Carry-forward: Unused legacy visit prediction and float coercion helpers removed; active API modules/import graph verified. See docs/task66_final_checkpoint.md. Maintenance architecture remnants remain Task 68.

## Task 67 — Remove Duplicated Business Logic

Status: DONE — ACCEPTED

Carry-forward: Customer/Inventory CREATE-only trim/blank rule consolidated internally with exact messages and unchanged PATCH behavior. See docs/task67_final_checkpoint.md. Stop after push verification at the three-task batch limit.

## Task 68 — Remove Obsolete Maintenance Architecture

Status: DONE — ACCEPTED

Carry-forward: Unused parts selector and legacy visit-history renderer removed; current routed Maintenance and Visit contracts verified. See docs/task68_final_checkpoint.md.

## Task 69 — Remove Obsolete Store Architecture

Status: DONE — ACCEPTED

Carry-forward: Unused legacy Store_Products identifier removed; current inventory-backed catalog rendering, error/empty paths and imports verified. No checkout/order scope added. See docs/task69_final_checkpoint.md.

## Task 70 — Remove Obsolete Streamlit-to-Database Calls

Status: DONE — ACCEPTED

Carry-forward: No direct database calls remain in presentation sources; import boundary and authenticated HTTP/failure contract verified. See docs/task70_final_checkpoint.md. Stop after push verification at the batch limit.

## Task 71 — Unit Tests for Core Services

Status: DONE — ACCEPTED

Carry-forward: Twelve isolated core-rule tests added; accepted integration coverage preserved and impacted Task 47 contracts verified. See docs/task71_final_checkpoint.md.

## Task 72 — API Tests

Status: DONE — ACCEPTED

Carry-forward: Resource authentication, tenant-isolated CRUD, UUID validation and Audit immutability tested; Task 48/49 API contracts regressed. See docs/task72_final_checkpoint.md.

## Task 73 — Database / Repository Tests

Status: DONE — ACCEPTED

Carry-forward: Actual migrated PostgreSQL repositories/tenant/rollback/reporting and Inventory live API 409/recovery verified. Other allowlisted live API conflicts remain unverified. See docs/task73_final_checkpoint.md. Stop after push verification at batch limit.

## Task 74 — Core Workflow Tests

Status: DONE — ACCEPTED

Carry-forward: Linked synthetic API journey, failure integrity and tenant isolation verified alongside Work Order inventory lifecycle regression. See docs/task74_final_checkpoint.md.

## Task 75 — Inventory Transaction Tests

Status: DONE — ACCEPTED

Carry-forward: Migrated PostgreSQL stock movement, rejection, reference and transaction rollback cases verified with repository regressions. Preserve existing zero-adjustment/generic-record semantics. See docs/task75_final_checkpoint.md.

## Task 76 — Billing / Expense / Profitability Tests

Status: DONE — ACCEPTED

Carry-forward: Migrated PostgreSQL financial API semantics, tenant/reporting isolation and actual Invoice 409/recovery verified with Task 56/57 regressions. Stock/Contract full live API conflicts remain unverified. See docs/task76_final_checkpoint.md. Stop after push verification at batch limit.

## Task 77 — Authentication / Authorization Tests

Status: DONE — ACCEPTED

Carry-forward: Literal resource role matrices and established auth/context regressions verified; database roles remain authoritative. See docs/task77_final_checkpoint.md.

## Task 78 — Tenant Isolation Tests

Status: DONE — ACCEPTED

Carry-forward: Fifteen-resource PostgreSQL read/mutation matrices and selected explicit company-write attempts verified with repository regressions. Scope limitations explicit. See docs/task78_final_checkpoint.md.

## Task 79 — Fix Critical Bugs

Status: DONE — ACCEPTED

Carry-forward: Bounded critical regression audit passed 88 checks with no confirmed blocking defect in scope; no runtime repair required. Existing limitations retained. See docs/task79_final_checkpoint.md. Stop after push verification at batch limit.

## Task 80 — Validate Core User Workflows

Status: DONE — ACCEPTED

Carry-forward: Accepted API journey and stock lifecycle validation passed 16 checks; synthetic/disposable scope and OD-24 final-run exception recorded. See docs/task80_final_checkpoint.md.

## Task 81 — Validate Database Integrity

Status: DONE — ACCEPTED

Carry-forward: Current PostgreSQL constraints/indexes and synthetic outcome/rejection/rollback integrity passed 18 checks; no real-data certification. See docs/task81_final_checkpoint.md.

## Task 82 — Validate Permissions

Status: DONE — ACCEPTED

Carry-forward: Existing role/resource matrices and canonical database-authoritative permissions passed 45 checks; no policy changes. See docs/task82_final_checkpoint.md.

## Task 83 — Validate Financial Calculations

Status: DONE — ACCEPTED

Carry-forward: Accepted invoice and separate reporting calculation policies passed 31 checks on synthetic fixtures; no accounting-policy change. See docs/task83_final_checkpoint.md.

## Task 84 — Validate Inventory Calculations

Status: DONE — ACCEPTED

Carry-forward: Movement/rollback, thresholds and inventory valuation/summary contracts passed 28 checks; accepted encoding/presentation semantics preserved. See docs/task84_final_checkpoint.md.

## Task 85 — Validate Production Configuration

Status: DONE — ACCEPTED

Carry-forward: OD-25 offline production configuration/security readiness verified; startup now invokes validation and fails closed, 52 cases passed. No real production target/deployment approved. See docs/task85_final_checkpoint.md and docs/task85_configuration_readiness.md.

## Task 86 — Production Deployment

Status: OWNER DECISION REQUIRED — NOT ACCEPTED

Gate: OD-25 approves only Task 85 offline readiness; actual production target, deployment/security requirements and necessary actions/access are unapproved. No deployment attempted; Task 87–90 not started. See docs/task86_owner_decision_required.md.

## Task 87 — Production Smoke Test

Status: PENDING

## Task 88 — MVP Launch

Status: PENDING

## Task 89 — First Real-World Usage

Status: PENDING

## Task 90 — Post-Launch Critical Fixes Only

Status: PENDING
