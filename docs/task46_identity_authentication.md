# Task 46 — Database-Backed Identity and Authentication

## Objective
Replace the Task 44 temporary tenant header model with database-backed user authentication while preserving the existing role/permission definitions and domain services.

## Identity model
The MVP uses a single-company user model:

- `companies` — tenant/company record.
- `users` — one user belongs to exactly one company.
- `users.role` uses the existing application roles: `admin`, `manager`, `technician`.

`company_memberships` is intentionally excluded from the MVP and remains a future architecture option.

## Authorization source of truth
The existing `Role` and `Permission` enums plus `ROLE_PERMISSIONS` remain the single source of truth for MVP authorization. No database permission tables are introduced, avoiding duplicated role-permission business logic.

## Authentication flow
```text
email + password
        ↓
POST /api/v1/auth/login
        ↓
PBKDF2 password verification
        ↓
JWT { sub=user_id, exp, role, permissions }
        ↓
Bearer token
        ↓
database user lookup
        ↓
company_id + role
```

The database user is authoritative for current identity and authorization. JWT role/permission claims are informational compatibility claims and are not trusted as the authorization source.

## Tenant isolation
`X-Company-ID` is no longer a trusted tenant selector. `CompanyID` is derived from the authenticated user's `company_id`.

This prevents a caller from changing the tenant simply by changing a request header.

## API endpoints
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

## Initial administrator
The project provides:

```text
python -m backend.scripts.create_admin
```

This creates the first company and administrator interactively without storing a password in source code.

## Streamlit compatibility
- Legacy mode continues using the existing Streamlit admin password.
- API mode authenticates through FastAPI login and stores the returned bearer token in Streamlit session state.
- `AXYREL_API_TOKEN` remains supported as a pre-issued JWT for operational compatibility.
- `AXYREL_COMPANY_ID` is retained only as a deprecated configuration field and is no longer sent to the API.

## Security rules
- Passwords are stored only as PBKDF2 hashes.
- Tenant context comes from the authenticated user.
- Inactive users cannot authenticate or access protected endpoints.
- No password or secret is hardcoded into the implementation.

## Task 46 hardening
- Users can authenticate only when both the user and the user's company are active.
- Existing bearer tokens are rejected after the company is deactivated because every authenticated request re-resolves the user and company from the database.
- `/api/v1/auth/me` returns the user's effective permissions derived from the database role.
- Streamlit API mode uses the authenticated role and effective permissions to build the available module menu; it no longer hardcodes every API-authenticated user as `admin`.
- The legacy Streamlit mode remains admin-only and is unchanged.
- Task 46 security tests cover inactive users/companies, token invalidity, tenant-header tampering, role permissions, and JWT permission-claim elevation attempts.
