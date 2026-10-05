# Axyrel Frontend v1 — Local Review

The approved MVP frontend is implemented through Phase 3 and the remaining operations modules. FastAPI/PostgreSQL remains authoritative. Streamlit remains unchanged. For persistent local owner review, use [OWNER_REVIEW.md](OWNER_REVIEW.md); the disposable Phase 2 harness below is retained for regression testing. See [MVP_COMPLETION_REPORT.md](MVP_COMPLETION_REPORT.md) for final scope and validation.

## Owner visual review with synthetic data only

Terminal 1, from repository root:

```powershell
.\.venv\Scripts\python.exe -B frontend\tests\phase2-api.py
```

This runs the real accepted FastAPI on 127.0.0.1:8110 against a new disposable SQLite database with synthetic records. It changes working directory before backend import and explicitly sets the test database/environment; no workspace .env, configured application database, production data or credentials are used. This verifies UI/API integration, not a fresh PostgreSQL migration/deployment. Ctrl+C gracefully closes the API and disposes its temporary database.

Terminal 2:

```powershell
Set-Location frontend
$env:AXYREL_BACKEND_URL = "http://127.0.0.1:8110"
$env:AXYREL_FRONTEND_ORIGIN = "http://127.0.0.1:3000"
npm.cmd run dev -- --port 3000
```

Open http://127.0.0.1:3000/login. Synthetic review account: admin@example.test / synthetic-password. Optional read-only presentation account: technician@example.test / synthetic-password. These are test-only identities, never production credentials. Navigate to Dashboard, Customers and Assets; adding/editing records affects only that temporary database. Local phone numbers require an explicit international format for WhatsApp; no country is guessed. Stop both terminals with Ctrl+C when done.

Focused integration command from frontend: `npm.cmd run test:phase2`; production-built Next on loopback 3120 plus actual synthetic FastAPI 8120. Foundation regression command uses its separate synthetic contract server. Both harnesses refuse to reuse existing servers on their ports.

## Local commands

Node 22.23.2 / npm 10.9.8. From frontend: `npm.cmd ci --ignore-scripts`, `npm.cmd run typecheck`, `npm.cmd run lint`, `npm.cmd run build`, `npm.cmd run test:foundation`. Tests start the production Next server on loopback port 3100 and a synthetic contract server on 8109; neither connects to a database. Browser installation: `npx.cmd playwright install chromium`. Normal development: `npm.cmd run dev`; AXYREL_BACKEND_URL is server-only and defaults to the existing loopback FastAPI address. Do not use production targets or real data for development.

NextJS App Router forwards existing FastAPI contracts rather than implementing business rules. Login uses existing OAuth2 username/password, verifies /auth/me and stores the bearer token in an HttpOnly SameSite Strict session cookie, Secure when served via HTTPS. There is no localStorage token, tenant selector, new refresh flow or claim of token revocation on logout. State-changing adapter routes require exact same-origin Origin headers. AXYREL_FRONTEND_ORIGIN explicitly identifies the browser origin when behind a proxy; locally the incoming Host and request protocol determine it. No forwarded-host/protocol headers are trusted. Frontend cache is cleared on login/logout; permissions come from /auth/me, and backend authorization remains decisive. Forwarding targets are allowlisted; errors are safe and authenticated responses no-store. Use HTTPS and an explicitly approved origin on any future approved deployment; production infrastructure is outside this phase.

The Phase 1 directory extension is GET /api/v1/technician-directory. Phase 2 image endpoints are documented below. Existing service:read permission; same authenticated company; active Users with role technician; response only id/display_name. Accepted Task46 service-visit fixture explicitly assigns technician User.id to WorkOrder.assigned_technician_id and Task55 stock scenarios carry it through. No historical FK or identity validation is introduced; accepted standalone UUID fixtures remain legal. Unknown references stay unavailable, never fabricated. No user management, email/password exposure or schema/business/authorization policy changes.

## Brand and approved references

Original supplied logo: public/brand/axyrel-logo.png; rendered directly with img, proportional dimensions, no Next image optimization/filter/crop/recolor. ESLint's image-optimization suggestion is disabled intentionally for owner-required byte-preserved image use. SHA256: CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3.

Original design references preserved outside public assets: design-references/dashboard.png, customers.png, assets.png. They define navy/teal, calm workspace, spacing and layout direction. Their sample metrics, import/documents/filter-details/next-service/user-management elements and alternative embedded logo are not feature or logo authorization. Shared tokens have accessible text colors; the supplied official logo is the sole logo used by the application.

English strings are centralized at src/locales/en/common.ts; logical CSS supports dir=rtl without adding translation or persisted language preference. Mobile navigation has expanded state and desktop remains primary. No external font/CDN, analytics or third-party account infrastructure is required.

## Private Customer and Asset profile images

One optional image per existing record, with preview, replace/remove and fallback. FastAPI provides GET/PUT/DELETE `/api/v1/customers/{id}/image` and equivalent assets endpoints. PUT sends the raw JPEG/PNG/WebP file with its matching Content-Type (no multipart filename). Both input and the same-origin frontend proxy are limited to 5 * 1024 * 1024 bytes. Backend validates actual content and normalizes a metadata-free, static WebP up to 1024px. Read/manage permissions and tenant record checks remain authoritative. There is no public image endpoint; the frontend forwards its HttpOnly session only on the allowlisted image routes and protects mutations with exact-origin checks.

Set server-only `AXYREL_PRIVATE_IMAGE_ROOT` to a private directory outside any web/static root. Development default is `.private-images` relative to the backend working directory (git-ignored). Restrict the directory to the backend service account using OS permissions/Windows ACLs; do not expose it through a file server. The synthetic review harness creates it inside its disposable directory. Install the updated requirements (Pillow >=12.3,<13). Back up the directory together with the database for persistent local development; ephemeral filesystem deployments do not preserve images. Production storage/deployment is outside this checkpoint.

Storage is abstracted through ImageStorage.read/replace/remove. A future private S3-compatible adapter can be selected in the factory without changing Customer/Asset business logic or API/UI. It must preserve atomic single-key replacement, bounded reads and deletion. Keys are derived from server-authenticated company, resource and existing UUID; no image schema migration is needed. Only processed pixels are retained. Soft-deleted records become inaccessible through the existing record lookup; their stored image is retained alongside the soft-deleted record until an explicitly reviewed retention/purge policy. Explicit Remove image deletes the object.

Asset CSV import is implemented with authenticated tenant-local preview, structured errors, explicit confirmation, transactional revalidation and idempotent retry. It creates Assets only; existing records are never updated. See MVP_COMPLETION_REPORT.md for limits and normalization.


## Phase 3 Service Flow

Requests, Work Orders, Schedule, Service Visits and Service History now use the existing authenticated FastAPI contracts. Request/customer/asset selectors and the read-only technician directory supply readable relationships. History displays explicit stored records; visit completion does not create synthetic history. Work Order and Visit status choices reflect the accepted lifecycle, with server validation authoritative. Schedule supports a seven-day view and responsive agenda with Cairo event times; unchanged timestamps retain their API values on edits. Visit parts use the existing technician-stock installation API and recorded reversal ledger.

Validation from the repository root: `.\.venv\Scripts\python.exe -B tests/run_phase3_backend_validation.py`. From frontend: `npm.cmd run test:phase3`. The latter serves real FastAPI on 8130 and production Next on 3130 using a generated local PostgreSQL database named `axyrel_phase3_test_<random hex>`. It reads local PostgreSQL connection configuration only to create/drop that disposable database through the postgres administration database; it never connects to the configured application database. It refuses remote hosts and stale fixture markers. Run browser suites sequentially to avoid short sign-in assertion timeouts under CPU load.

After a Windows Playwright shutdown, run `.\.venv\Scripts\python.exe -B frontend/tests/phase3-api.py --cleanup` from the repository root. Cleanup accepts only the generated database name stored in the git-ignored test marker and refuses other targets. No application migrations or production/deployment operations occur. See PHASE3_IMPLEMENTATION_REPORT.md for scope, API limitations and validation evidence.


## Remaining MVP operations

Inventory items, existing record-only transactions, Technician Stock, Invoices, Expenses, backend Profitability and real-data Reports are available. No warehouse transfer API or fabricated historical metrics were added. Run `npm.cmd run test:mvp` from frontend. From the repository root, run `.\.venv\Scripts\python.exe -B tests/test_asset_csv_import.py` and `.\.venv\Scripts\python.exe -B tests/run_mvp_backend_regressions.py`. Use isolated disposable PostgreSQL fixtures for these suites; never point them at owner-review or production data.


## Owner Acceptance Remediation Round 1

Login opens Dashboard and the redundant Workspace navigation item is removed; the shell/module URLs remain compatible. Customers have an optional dynamic labeled phone collection (up to 100), with Egypt default, server E.164 validation and legacy preservation. Asset profiles now hold country/state/locality/address/location URL, maintenance cycle in months and warranty period in whole calendar years; the backend calculates the warranty end. See OWNER_ROUND1_REMEDIATION_REPORT.md and design-references/GEOGRAPHIC_REFERENCE.md.

Run focused browser validation with `npx.cmd playwright test --config playwright.round1.config.ts`. For isolated PostgreSQL suites use `tests/isolated_backend_suite.py test_owner_round1` or the regression runners; their connection guards reject configured application and Owner Review targets. Windows browser suites need permission to clean up their own spawned test servers. Disposable API/frontend ports can be configured with AXYREL_PHASE3_TEST_PORT and AXYREL_TEST_FRONTEND_PORT; request Origin assertions follow that configured origin. On Windows, clean only the generated marker-identified disposable database using the fixture's --cleanup with the matching AXYREL_PHASE3_TEST_PORT. Never use owner-review as a regression target.
