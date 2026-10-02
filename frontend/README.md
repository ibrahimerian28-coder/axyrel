# Axyrel Frontend v1 — Local Review

Owner-approved separate frontend phase; not Task 91. Historical Tasks 1–90 and Streamlit remain unchanged. Phase 1 provides login/session handling, typed API forwarding, React Query and shared states. Phase 2 adds Dashboard, Customers and Assets, linked profiles, supported create/edit forms and explicit phone actions. Other domains remain labelled later-phase placeholders, including destinations reached from related-record context. No later domain implementation or production deployment.

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

Focused integration command from frontend: `npm.cmd run test:phase2`; production-built Next on loopback 3101 plus actual synthetic FastAPI 8110. Foundation regression command uses its separate synthetic contract server. Both harnesses refuse to reuse existing servers on their ports.

## Local commands

Node 22.23.2 / npm 10.9.8. From frontend: `npm.cmd ci --ignore-scripts`, `npm.cmd run typecheck`, `npm.cmd run lint`, `npm.cmd run build`, `npm.cmd run test:foundation`. Tests start the production Next server on loopback port 3100 and a synthetic contract server on 8109; neither connects to a database. Browser installation: `npx.cmd playwright install chromium`. Normal development: `npm.cmd run dev`; AXYREL_BACKEND_URL is server-only and defaults to the existing loopback FastAPI address. Do not use production targets or real data for development.

NextJS App Router forwards existing FastAPI contracts rather than implementing business rules. Login uses existing OAuth2 username/password, verifies /auth/me and stores the bearer token in an HttpOnly SameSite Strict session cookie, Secure when served via HTTPS. There is no localStorage token, tenant selector, new refresh flow or claim of token revocation on logout. State-changing adapter routes require exact same-origin Origin headers. AXYREL_FRONTEND_ORIGIN explicitly identifies the browser origin when behind a proxy; locally the incoming Host and request protocol determine it. No forwarded-host/protocol headers are trusted. Frontend cache is cleared on login/logout; permissions come from /auth/me, and backend authorization remains decisive. Forwarding targets are allowlisted; errors are safe and authenticated responses no-store. Use HTTPS and an explicitly approved origin on any future approved deployment; production infrastructure is outside this phase.

The only backend extension is GET /api/v1/technician-directory. Existing service:read permission; same authenticated company; active Users with role technician; response only id/display_name. Accepted Task46 service-visit fixture explicitly assigns technician User.id to WorkOrder.assigned_technician_id and Task55 stock scenarios carry it through. No historical FK or identity validation is introduced; accepted standalone UUID fixtures remain legal. Unknown references stay unavailable, never fabricated. No user management, email/password exposure or schema/business/authorization policy changes.

## Brand and approved references

Original supplied logo: public/brand/axyrel-logo.png; rendered directly with img, proportional dimensions, no Next image optimization/filter/crop/recolor. ESLint's image-optimization suggestion is disabled intentionally for owner-required byte-preserved image use. SHA256: CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3.

Original design references preserved outside public assets: design-references/dashboard.png, customers.png, assets.png. They define navy/teal, calm workspace, spacing and layout direction. Their sample metrics, import/documents/filter-details/next-service/user-management elements and alternative embedded logo are not feature or logo authorization. Shared tokens have accessible text colors; the supplied official logo is the sole logo used by the application.

English strings are centralized at src/locales/en/common.ts; logical CSS supports dir=rtl without adding translation or persisted language preference. Mobile navigation has expanded state and desktop remains primary. No external font/CDN, analytics or third-party account infrastructure is required.
