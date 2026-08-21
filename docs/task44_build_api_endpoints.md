# Task 44 — Build API Endpoints

## Scope
Task 44 exposes the migrated backend domains through FastAPI v1 endpoints.

## API prefix
`/api/v1`

## Tenant boundary
Tenant-scoped requests originally required the `X-Company-ID` header. This was intentionally temporary until database-backed authentication was connected.

Task 46 replaces that temporary boundary: tenant context is now derived from the authenticated database user.

## Authorization
Endpoints use the existing JWT permission foundation from Task 22, now resolved against the authenticated database user's role.

## Endpoint groups
- `/customers`
- `/assets`
- `/service-requests`
- `/work-orders`
- `/schedules`
- `/service-visits`
- `/service-history`
- `/service-contracts`
- `/invoices`
- `/expenses`
- `/inventory`
- `/inventory-transactions`
- `/technician-stock`
- `/notifications`
- `/audit-logs`
- `/profitability/summary`
- `/profitability/expenses`

## Design rules
- API handlers delegate business operations to the existing service layer.
- API handlers do not contain direct SQL.
- Tenant company_id is never accepted from request bodies.
- Tenant company_id is resolved from the authenticated user.
- Mutating endpoints commit only after the service operation succeeds.
- Not-found records return HTTP 404.
- Read/write permissions use the existing authorization enum.

## Task 46 authentication endpoints
- `/auth/login`
- `/auth/me`

## Deliberately deferred
- `company_memberships`
- Production data migration
- External email/SMS/push delivery
