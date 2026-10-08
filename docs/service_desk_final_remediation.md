# Service Desk final remediation checkpoint

Status: remediations 1-3 implemented; remediation 4 failure semantics implemented,
but persistent revocable sessions STOPPED for owner architecture/migration approval.
Service Desk is not declared closed. No deployment or next-module work.

Subsequent owner approval authorized implementation and isolated migration tests.
See [persistent revocable sessions](persistent_revocable_sessions.md) for the
implemented architecture and final validation. The historical approval boundary
below records the previous checkpoint. Owner Review migration/deployment remain
unauthorized; no next-module work is started.

## Repository and data safety

- Initial branch: `frontend/v1` in `D:\Axyrel_BACKUP_BEFORE_GEMINI`.
- Initial local HEAD: `a5b0e4cc9786ad4b145206b1bc13b55c859690e0`.
- Initial live origin/frontend/v1 HEAD: `a5b0e4cc9786ad4b145206b1bc13b55c859690e0` (verified with `git -c http.sslBackend=openssl ls-remote`; default Schannel transport failed).
- Initial status: only `frontend/next-env.d.ts` modified; generated file excluded from staging.
- No main checkout, modification, merge, force push, or destructive Git operations.
- Owner Review database: no connections, reads, writes, migrations, reset, reseed,
  initialization, replacement, or deletion. The initial repository-wide guidance-file
  enumeration encountered denied access to `.owner-review` and did not access its data.
- Migrations executed/proposed for remediations 1-3: none.
- Official logo bytes untouched: HEAD and working-file Git blob hashes both
  `22a21e18fef6cafb70dc277e99afc9aa68b80fbc`.
- Backend regression harness rejects application/Owner Review DB connections;
  browser tests create generated local PostgreSQL databases. Test databases retained.

## Implemented behavior

1. Details opens the existing Service Desk drawer shell, without leaving the module.
   Full jobs and intake-only requests use existing records and human-readable IDs.
   Shows customer/asset, description, priority, technician, status, appointment range,
   notes and all contact numbers with existing Call/WhatsApp/Copy actions.
   The timeline reads Requests, Work Orders, Schedules, Visits and History; it stores
   nothing and creates no lifecycle model. Appointment cancellation labels describe
   the stored status at the appointment time, not an invented cancellation timestamp.
   Current follow-up/final-completion state is shown without inventing event times.
   Customer, Asset and History navigation stays available; legacy modules remain.
2. Customer rows/cards show the first stored phone and `+N more` opening Details.
   Search checks the existing aggregated phone search text and all customer phones,
   including non-visible numbers. No customer data is changed or normalized.
3. Shared frontend display utility formats dates as DD Mon YYYY and Cairo-local
   times in 12-hour AM/PM format, with appointment ranges. Service Desk, all existing
   service modules, dashboard schedules, customer history, asset dates, invoice/
   expense dates and inventory transaction timestamps use it. Native inputs,
   `eventInput`, offset handling, backend storage and scheduling conversions remain
   unchanged; technical offset inputs remain available for explicit clock changes.
4. Definitive `/auth/me` 401 now redirects to Login. Network errors and 5xx show a
   retry state; 403 shows permission state. Existing BFF behavior clears credentials
   only for authoritative upstream 401 or explicit Logout. No localStorage token.

## Authentication root cause and approval boundary

Current architecture:
- FastAPI login issues HS256 JWT bearer tokens with `sub`, role/permission claims
  and mandatory expiration; default lifetime is 60 minutes (environment override).
- Next BFF stores that JWT in `axyrel_session`: HttpOnly, SameSite=Strict, path=/;
  Secure is enabled for HTTPS public origin. No Max-Age/Expires: browser-session
  cookie, so browser/computer restart persistence is not guaranteed.
- No refresh token, session table, session version or per-session revocation store.
- Backend validates signature/expiration and rechecks user/company activity on
  every authenticated request. Disabled/deleted users and inactive companies get 401;
  authorization permissions use current DB roles rather than stale JWT roles.
- BFF sends a bearer header upstream, limits routes, checks write Origin and retains
  credentials on transport failures/timeouts/5xx/403. `/auth/me` failures are recoverable
  except definitive 401. No application inactivity timer or auth middleware found.
- Logout clears the browser cookie but does not revoke an already-issued JWT.
- Backend/frontend restart retains a valid JWT only while its cookie and signing
  key survive and before JWT expiration. Signing-key changes invalidate tokens.

Reasons users reach Login/auth loss: missing browser-session cookie, JWT expiry,
invalid signature/subject, inactive/deleted user or inactive company, explicit Logout.
Ordinary elapsed time is therefore enough to invalidate the existing credential.

Exact limitation: a persistent cookie alone cannot outlive JWT expiry; a much longer
JWT cannot provide per-session Logout/security revocation. No existing durable
revocation primitive safely satisfies the complete owner requirement.

Recommended minimal architecture (NOT implemented):
1. Add a tenant-linked `auth_sessions` table holding a hash of a cryptographically
   random opaque session secret, user/company references, creation timestamp and
   revocation timestamp. Never store the raw secret in DB, logs or browser storage.
2. Issue a persistent HttpOnly/Strict/Secure-as-applicable cookie; renew browser
   Max-Age on successful validation, with no server inactivity/ordinary time expiry.
   Browser eviction/deletion limits still apply; finite browser cookie retention
   requires renewal during use and cannot promise unlimited absence retention.
3. Resolve opaque sessions via DB on authenticated requests and recheck active user/
   company and current permissions; preserve existing API JWT callers separately.
4. Revoke the session server-side at Logout, then clear cookie; allow owner/admin
   security revocation and ensure disabled/deleted accounts lose access immediately.
5. Preserve Origin/CSRF controls, constant-time comparisons where relevant, cookie
   flags and generic recoverable outage handling. Add isolated backend/browser tests
   for time passage, restarts, cookie persistence, revocation and failure boundaries.

Schema implication: one additive session-table migration with foreign keys/indexes,
no changes to operational Service Desk data. This is a material authentication
architecture change requiring explicit owner approval before implementation or
migration against persistent Owner Review. Non-expiring sessions increase the
importance of secret protection and durable revocation; a revocation-store outage
must fail closed on API access while preserving the browser credential for retry.

## Validation

- Backend: `.venv/Scripts/python.exe -B tests/run_service_desk_regressions.py
  test_service_desk test_service_desk_postgresql test_task53_schedule_service_visit
  test_task54_visit_history_integration test_task55_work_order_inventory
  test_task46_auth test_task49_authentication_context test_task77_auth_roles`:
  **176 tests across 8 isolated modules, 0 failures** (35/38/22/13/13/10/43/2).
- Frontend typecheck: passed.
- Production build: passed after final source edits.
- Lint: passed with 0 errors and 0 warnings.
- `npm.cmd run test:foundation`: 5 passed, exit 0.
- `npm.cmd run test:phase2 -- journeys.spec.ts`: final sequential run 5 passed, exit 0.
- `npm.cmd run test:mvp -- workflows.spec.ts`: 5 passed, exit 0.
- `npm.cmd run test:phase3` with disposable ports 18365/13365: **31 passed, exit 0**.
- Relevant unique regression total: **176 backend + 46 browser tests passed**.
- Windows test-server teardown hung after assertions completed; verified the exact
  disposable listening-port PIDs and stopped only those servers, allowing Playwright
  to report its final result/exit status. No Owner Review or normal app process stopped.
- Initial browser run interrupted after an overlapping rebuild invalidated served
  assets. A second run exposed a missing required name in the synthetic customer
  update and an old weekday-format expectation; these fixtures/expectations were
  corrected and the run stopped before repeating the same stale expectation.
  A concurrent foundation run cleared generated test output, removing a Phase 3
  DB marker; that run was interrupted. A customer/asset journey timed out at Login
  under concurrent test load; it is rerun sequentially. Final runs use a fixed
  production build and sequential suites to avoid output-directory collisions.
- Regression assertions changed only to the approved date display expectations;
  scheduling payload/UTC conversion and lifecycle assertions remain intact.
- Persistent-session lifetime, browser-restart persistence and server-side Logout
  revocation tests remain pending the approved architecture; no claims of completion.

## Files changed

- `frontend/src/lib/datetime.ts`
- `frontend/src/features/service-desk/screen.tsx`
- `frontend/src/features/phase2/screens.tsx`
- `frontend/src/features/phase3/contracts.ts`
- `frontend/src/features/phase3/screens.tsx`
- `frontend/src/features/phase4/screens.tsx`
- `frontend/src/app/workspace/page.tsx`
- `frontend/tests/phase3/schedule-display.spec.ts`
- `frontend/tests/phase3/service-desk.spec.ts`
- `frontend/tests/phase3/work-order-schedule-ux.spec.ts`
- `frontend/tests/browser/foundation.spec.ts`
- `frontend/tests/phase2/journeys.spec.ts`
- `docs/service_desk_final_remediation.md`

## Manual Owner Acceptance retests

Retest full-job and intake-only Details, human-readable identifiers, all contact
numbers/actions, secondary-number search, desktop/mobile and RTL drawers, date/time
and range display, rescheduling, active visits, parts install/reversal, multi-visit
follow-up and separate history. Verify recoverable auth outages, 403 permission state,
definitive 401 Login and explicit Logout. Persistent browser/computer restart and
long-lived revocable sessions remain blocked pending architecture approval.
