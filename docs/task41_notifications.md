# Task 41 — Notifications

## Scope
Introduces the tenant-scoped notification persistence and service foundation.

## Implemented
- Notification ORM model
- Create/read/update repository operations
- Recipient filtering
- Status/type filtering
- Expiration filtering
- Mark-as-read operation
- Notification Pydantic schemas
- PostgreSQL migration and indexes
- Tenant isolation through explicit `company_id`

## Notification types
`notification_type` is intentionally generic so later modules can emit events such as inventory alerts, scheduling reminders, contract expiry alerts, payment reminders, and system notifications without changing the core table.

## Status
`unread` and `read` are the initial statuses. The field remains extensible for later delivery workflows.

## Deliberately deferred
- Notification UI
- API endpoints
- Email/SMS/push delivery
- Automated event generation from other modules
- Notification preferences

Those belong to later integration/API/settings work.
