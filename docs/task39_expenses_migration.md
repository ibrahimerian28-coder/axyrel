# Task 39 — Expenses Migration

## Scope

Migrate the Expenses domain from the legacy Streamlit/Google Sheets foundation into the PostgreSQL repository/service architecture.

## Source-derived legacy behavior

The legacy Expenses page currently reads the `Expenses` Google Sheet and displays the rows plus a count. The source project does not define a structured expense schema or CRUD workflow yet.

## Task 39 foundation

The new foundation provides:

- tenant/company ownership
- category
- description
- amount
- expense date
- payment method
- vendor
- reference
- notes
- active/deleted status
- repository CRUD/read operations
- date/category/status filtering
- service-layer access
- non-negative amount validation
- PostgreSQL migration and indexes

## Inference note

Because the legacy source did not expose a structured expense schema, fields such as category, payment method, vendor, and reference are modeled as a forward-compatible domain foundation. They should be confirmed against real business requirements before production data migration (Task 62).

## Deferred

- Profitability integration: Task 40
- Notifications/audit integrations: later integration tasks
- API endpoints: Task 44
- Streamlit UI connection: Task 45
- Existing-data migration: Task 62
- Removal of Google Sheets persistence: Task 64
