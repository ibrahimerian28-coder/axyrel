# Task 42 — Activity / Audit Log

## Scope

Add an immutable, tenant-scoped audit log foundation for recording security and business activity.

## Audit record

Each entry can record:

- company / tenant
- actor user (optional for system actions)
- action
- entity type and entity ID
- human-readable description
- structured metadata JSON
- IP address
- user agent
- creation timestamp

## Architecture

`AuditLogService` → `AuditLogRepository` → `AuditLog` ORM model → PostgreSQL `audit_logs` table.

The repository intentionally provides create/read operations only. Update/delete operations are not exposed because audit history should be immutable.

## Tenant isolation

All reads and writes require a company ID through the existing tenant-isolation foundation.

## Not included

- automatic event hooks across every module
- API endpoints
- Streamlit audit UI
- authentication/authorization policy changes
- production migration of historical activity

Those concerns belong to later integration/API/production tasks.
