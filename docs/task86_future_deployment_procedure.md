# Task 86 — Rehearsed Deployment Procedure and Future Production Prerequisites

Authority: OD-26 offline/local rehearsal only. **No actual production deployment or hosting target is approved.** This procedure records reproducible accepted-MVP steps; production execution requires separately approved target/security/access and operational decisions.

## Reproduce the isolated rehearsal

From the accepted checkout and existing project virtual environment:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_task86_deployment_rehearsal.py
```

The harness requires only the existing local PostgreSQL test server and permission to create/drop disposable databases through maintenance postgres. It rejects nonlocal server configuration, generates an exact guarded UUID database name, closes processes/connections and drops only that generated target. It never connects to the configured application database. No workspace .env is read by deployment subprocesses; they run from a temporary directory with explicit synthetic settings and project PYTHONPATH.

The rehearsal sets production mode and a synthetic nondefault secret, with the generated PostgreSQL target on 127.0.0.1. This address is allowed by the existing validator's literal localhost prohibition; the rule is not changed or bypassed. Local rehearsal does not approve any loopback address as an actual production target. Existing local test-server connection credentials are used in memory only, never printed or stored as production secrets. No external URL is contacted.

The accepted initializer command executes all thirteen numbered migrations and records verified checksums. A second run skips the same thirteen entries with unchanged ledger. A synthetic company/admin is inserted only as test infrastructure. Two real local Uvicorn starts bind ephemeral loopback sockets, check /health, authenticate against migrated PostgreSQL, read canonical identity and create/read tenant-scoped synthetic Customer records, then stop through the server's normal exit signal and dispose connections. Persisted rows and unchanged migration history are independently checked. Streamlit AppTest renders the accepted app.py login screen under the same production-mode configuration/API base URL; this is script rendering, not interactive browser or public UI-server certification. Missing/default secret and malformed database URL stop application import before serving or schema work.

Observed environment: Python 3.13.14, FastAPI 0.141.1, Uvicorn 0.52.3, Streamlit 1.61.1, SQLAlchemy 2.0.52, psycopg 3.3.4, pydantic-settings 2.15.0, PyJWT 2.13.0. Two starts reproduce within this installed environment. requirements.txt has version ranges/unpinned packages; a future release needs a reviewed exact dependency/runtime artifact. This task does not claim reproduction on arbitrary fresh operating systems or dependency versions.

## Future target prerequisites and configuration

Before any real deployment, approve hosting/runtime target, exact release artifact, database identity/schema/search_path, connection/access security, serving addresses/TLS, secret delivery, operator permissions, operational backup/restore/rollback and acceptance criteria. No provider, domain, certificate, network topology or secret-manager choice is made here. Do not send credentials in chat or track them in Git. Real-data source/mapping/tenant/ID/duplicate/invalid-row policies remain separately gated under OD-22/23, including unresolved Expenses mapping.

Configure the existing variables securely for the approved target: AXYREL_ENV=production; DATABASE_URL for exactly that approved PostgreSQL database; nonblank nondefault SECRET_KEY; existing positive ACCESS_TOKEN_EXPIRE_MINUTES/AXYREL_API_TIMEOUT_SECONDS; AXYREL_UI_API_ENABLED=true; AXYREL_API_BASE_URL identifying the approved API address. Keep per-user authentication via the API; no preissued token or company selector is required. AXYREL_COMPANY_ID is deprecated and cannot select tenant scope. Do not change API-prefix semantics or invent environment values solely for deployment. See task85_configuration_readiness.md for the enforced baseline checks and their limits.

## Database initialization and migration

Use docs/task59_database_creation_procedure.md and accepted timezone upgrade reviews, preserving OD-21. On an approved fresh empty target, after independently confirming identity/access and secure configuration:

```powershell
.\.venv\Scripts\python.exe -B -m backend.scripts.init_database
```

This command uses configured DATABASE_URL and is **not authorized against production by this document**. Never run it on an unknown target. Existing tracked targets verify exact identity/checksums before pending migrations; mismatch stops without rewriting history. Untracked non-empty targets require explicit baseline/reconciliation approval, not automatic stamping, dropping or replay. A successful migration and ledger record commit together; earlier successful migrations remain if a later one fails. Review populated historical timestamp upgrades and index locking before approved execution.

## Application startup and verification

The accepted backend entry point is backend.main:app. Local command pattern (actual serving/binding/process supervision remains target-specific):

```powershell
.\.venv\Scripts\python.exe -B -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -B -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
```

Start the backend before the UI. These loopback examples are not an approved public topology; an actual target needs reviewed process supervision, routing and transport settings. Production validation runs before engine construction and again at ASGI lifespan start, refusing invalid required configuration. Streamlit loads the same configuration during app execution. Avoid printing settings, connection URLs, tokens, passwords or request bodies in operator logs.

/health confirms API process liveness only; it does not query PostgreSQL or certify schema readiness. Check verified migration history/schema separately, then approved synthetic identity login and authenticated read against the exact database to verify connectivity/auth/readiness. The rehearsal adds no public readiness or shutdown endpoint. Actual production test accounts/data/write authorization and browser UI verification require explicit approval before use.

## Shutdown, rollback and recovery

Stop serving through the approved process supervisor's graceful shutdown mechanism; rehearsal verifies Uvicorn's normal exit and database connection release. Do not treat killing the host or dropping a database as a rollback plan. A code rollback requires an approved compatible prior artifact and verification against current schema; no automatic downgrade or history rewrite is supplied. Migration failure rolls back that migration/record, not all previously committed migrations. Diagnose pending failure and rerun only the reviewed pending plan; never modify applied SQL/checksums/ledger to force success. Existing production restore or destructive reconciliation needs separate owner approval and tested backups. Disposable cleanup is limited to guarded generated test targets.

**Acceptance: OFFLINE PRODUCTION DEPLOYMENT REHEARSAL / READINESS VERIFIED.** Hosting approval, provisioning, production credentials, live traffic/data, operational infrastructure/security certification, production smoke testing, launch and real-world usage remain unfulfilled and separately gated.
