# Axyrel — API-backed Field Service MVP

Axyrel is the current PostgreSQL + FastAPI + Streamlit MVP for field-service operations.
The Streamlit UI now talks to FastAPI; Google Sheets is no longer part of the active MVP UI path.

## Current working domains

- Authentication and role-based permissions
- Tenant-scoped customers
- Inventory and inventory movements
- Service requests
- Work orders
- Service visits
- Expenses
- Invoices
- Profitability reporting

## Architecture

```text
Streamlit UI
    |
    v
FastAPI /api/v1
    |
    v
Service layer -> Repository layer
    |
    v
PostgreSQL
```

Tenant context is derived from the authenticated API user. The old `X-Company-ID` header is not required by the UI.

## Requirements

- Python 3.11+ (the project was previously tested by the project owner on Python 3.13)
- PostgreSQL 17
- A PostgreSQL database named `axyrel`

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Environment

Copy `.env.example` to `.env` and set the real PostgreSQL password and a development secret:

```powershell
Copy-Item .env.example .env
notepad .env
```

Required values:

```env
AXYREL_UI_API_ENABLED=true
DATABASE_URL=postgresql+psycopg://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/axyrel
SECRET_KEY=replace-with-a-development-secret
```

Do **not** commit `.env` or `.streamlit/secrets.toml`.

## Database

The numbered SQL migrations in `migrations/` are the authoritative schema bootstrap used by the project.
If the database has already been initialized, do not drop it just to run the demo.

Verify the connection:

```powershell
python -c "from backend.core.database import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT 1')).scalar())"
```

Verify the tables:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d axyrel -c "\dt"
```

The MVP should contain the core service, identity, inventory, billing, expense, notification, and audit tables.

## Start FastAPI

Terminal 1:

```powershell
python -m uvicorn backend.main:app --reload
```

Health check:

```text
http://127.0.0.1:8000/health
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

## Start Streamlit

Terminal 2, from the project root with the virtual environment activated:

```powershell
streamlit run app.py
```

Log in with the database-backed user created by the project's identity setup, for example the existing development administrator used during local testing.

## Important repair notes

This review removed the previous split-brain behavior where some Streamlit pages used PostgreSQL/FastAPI while other pages silently fell back to Google Sheets. The active UI modules now use the API client consistently.

The inventory Pydantic schema was also aligned with the actual PostgreSQL ORM model (`item_name`, `min_limit`, `cost_price`, and `ideal_stock`).

Display IDs for customers, assets, service requests, and work orders are assigned per company when new records are created.

The repository intentionally does not include local virtual-environment files, Python bytecode caches, Streamlit secrets, or `.env` credentials.

## Validation performed on the delivered source

- Python source compilation: no syntax errors across the project source files.
- Backend/UI module structure reviewed against the API routes and Pydantic/ORM models.
- Inventory schema/model mismatch repaired.
- Customer PATCH/DELETE behavior aligned with the existing FastAPI routes.
- Streamlit navigation switched to the API-backed MVP modules.

A live PostgreSQL/Streamlit runtime test must be executed on the Windows development machine because the uploaded archive does not contain the local PostgreSQL server or the project's installed virtual environment.
