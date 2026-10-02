# Axyrel Frontend v1 — Phase 1

Owner-approved separate frontend phase; not Task 91. Historical Tasks 1–90 and Streamlit remain unchanged. This foundation provides login/session handling, typed API forwarding, React Query, responsive/RTL-ready navigation and shared loading/error/empty/permission states. Domain entries are labelled later-phase placeholders; Dashboard/Customers/Assets screens are not implemented.

## Local commands

Node 22.23.2 / npm 10.9.8. From frontend: `npm.cmd ci --ignore-scripts`, `npm.cmd run typecheck`, `npm.cmd run lint`, `npm.cmd run build`, `npm.cmd run test:foundation`. Tests start the production Next server on loopback port 3100 and a synthetic contract server on 8109; neither connects to a database. Browser installation: `npx.cmd playwright install chromium`. Normal development: `npm.cmd run dev`; AXYREL_BACKEND_URL is server-only and defaults to the existing loopback FastAPI address. Do not use production targets or real data for development.

NextJS App Router forwards existing FastAPI contracts rather than implementing business rules. Login uses existing OAuth2 username/password, verifies /auth/me and stores the bearer token in an HttpOnly SameSite Strict session cookie, Secure when served via HTTPS. There is no localStorage token, tenant selector, new refresh flow or claim of token revocation on logout. State-changing adapter routes require exact same-origin Origin headers. AXYREL_FRONTEND_ORIGIN explicitly identifies the browser origin when behind a proxy; locally the incoming Host and request protocol determine it. No forwarded-host/protocol headers are trusted. Frontend cache is cleared on login/logout; permissions come from /auth/me, and backend authorization remains decisive. Forwarding targets are allowlisted; errors are safe and authenticated responses no-store. Use HTTPS and an explicitly approved origin on any future approved deployment; production infrastructure is outside this phase.

The only backend extension is GET /api/v1/technician-directory. Existing service:read permission; same authenticated company; active Users with role technician; response only id/display_name. Accepted Task46 service-visit fixture explicitly assigns technician User.id to WorkOrder.assigned_technician_id and Task55 stock scenarios carry it through. No historical FK or identity validation is introduced; accepted standalone UUID fixtures remain legal. Unknown references stay unavailable, never fabricated. No user management, email/password exposure or schema/business/authorization policy changes.

## Brand and approved references

Original supplied logo: public/brand/axyrel-logo.png; rendered directly with img, proportional dimensions, no Next image optimization/filter/crop/recolor. ESLint's image-optimization suggestion is disabled intentionally for owner-required byte-preserved image use. SHA256: CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3.

Original design references preserved outside public assets: design-references/dashboard.png, customers.png, assets.png. They define navy/teal, calm workspace, spacing and layout direction. Their sample metrics, import/documents/filter-details/next-service/user-management elements and alternative embedded logo are not feature or logo authorization. Shared tokens have accessible text colors; the supplied official logo is the sole logo used by the application.

English strings are centralized at src/locales/en/common.ts; logical CSS supports dir=rtl without adding translation or persisted language preference. Mobile navigation has expanded state and desktop remains primary. No external font/CDN, analytics or third-party account infrastructure is required.
