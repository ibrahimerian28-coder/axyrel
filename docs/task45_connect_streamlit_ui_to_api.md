# Task 45 — Connect Streamlit UI to API

## Objective
Connect the existing Streamlit presentation layer to the migrated FastAPI backend without rewriting the UI in this task.

## Implementation
- Added `utils/api_client.py` as the single HTTP boundary for Streamlit.
- Extended Task 43 settings with API base URL, bearer token, timeout, and an explicit UI API feature flag.
- Updated `utils/data_service.py` to route migrated `Customers`, `Inventory`, and `Expenses` reads/writes through FastAPI when `AXYREL_UI_API_ENABLED=true`.
- Preserved Google Sheets as the fallback for unsupported legacy screens and when API mode is disabled.
- Added an API/Legacy status indicator to the Streamlit sidebar.
- Kept domain/business logic out of Streamlit; API calls delegate to the Task 44 services.

## Supported API-backed UI domains in Task 45
- Customers → `/api/v1/customers`
- Inventory → `/api/v1/inventory`
- Expenses → `/api/v1/expenses`

## Deferred
Maintenance, Store, and remaining legacy screens continue to use their existing data source until their dedicated UI/domain migration is completed.

## Task 46 authentication transition
Task 45 originally used a static JWT plus `X-Company-ID`. Task 46 replaces the tenant header as a trusted selector.

API mode now supports:

- Interactive login through `POST /api/v1/auth/login`.
- Bearer token stored in Streamlit session state.
- Optional `AXYREL_API_TOKEN` as a pre-issued JWT compatibility path.
- `AXYREL_COMPANY_ID` is deprecated and is no longer sent to FastAPI.

The API derives the tenant from the authenticated database user.

## Operational requirement
The FastAPI server must be running before Streamlit is switched to API mode.

## Database bootstrap after Task 46

The repository includes the complete numbered SQL migration chain. The core
service-domain migration is `migrations/001_core_service_domain.sql`; it is
required because later migrations (including invoices and service contracts)
reference customers/work orders.

From the project root, initialize/repair the local PostgreSQL schema with:

```powershell
python -m backend.scripts.init_database
python -m backend.scripts.verify_database_schema
```

These migrations are idempotent. They create missing tables without deleting
existing company/user data.

After the schema check succeeds, restart Uvicorn and re-test:

- `GET /health`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/customers`

