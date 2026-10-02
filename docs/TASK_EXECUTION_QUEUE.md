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

Status: NEXT

## Task 70 — Remove Obsolete Streamlit-to-Database Calls

Status: PENDING

## Task 71 — Unit Tests for Core Services

Status: PENDING

## Task 72 — API Tests

Status: PENDING

## Task 73 — Database / Repository Tests

Status: PENDING

## Task 74 — Core Workflow Tests

Status: PENDING

## Task 75 — Inventory Transaction Tests

Status: PENDING

## Task 76 — Billing / Expense / Profitability Tests

Status: PENDING

## Task 77 — Authentication / Authorization Tests

Status: PENDING

## Task 78 — Tenant Isolation Tests

Status: PENDING

## Task 79 — Fix Critical Bugs

Status: PENDING

## Task 80 — Validate Core User Workflows

Status: PENDING

## Task 81 — Validate Database Integrity

Status: PENDING

## Task 82 — Validate Permissions

Status: PENDING

## Task 83 — Validate Financial Calculations

Status: PENDING

## Task 84 — Validate Inventory Calculations

Status: PENDING

## Task 85 — Validate Production Configuration

Status: PENDING

## Task 86 — Production Deployment

Status: PENDING

## Task 87 — Production Smoke Test

Status: PENDING

## Task 88 — MVP Launch

Status: PENDING

## Task 89 — First Real-World Usage

Status: PENDING

## Task 90 — Post-Launch Critical Fixes Only

Status: PENDING
