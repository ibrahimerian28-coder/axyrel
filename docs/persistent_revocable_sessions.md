# Persistent revocable authentication sessions

Owner-approved implementation on `frontend/v1`, based on checkpoint
`85ed6c52bb02431a16596d5b5f834399c6f80963` (local and live remote verified).
The pre-existing generated `frontend/next-env.d.ts` change is excluded from staging.

## Architecture and security

Browser login calls the BFF, which checks Origin and calls `POST /auth/sessions`.
The backend authenticates the current active user/company and issues `axs_` plus
32 cryptographically random bytes encoded as base64url. Only the SHA-256 hash
is stored. The BFF never returns the credential to browser JavaScript. It sets
`axyrel_session`, HttpOnly, SameSite=Strict, path `/`, Secure for the configured
HTTPS public origin, with a 400-day Max-Age. Successful authenticated BFF use
renews that retention with the same credential: no refresh token or rotation race.

Every backend request resolves the session hash from the database and checks its
revocation state, current user, company activity, and matching company reference.
Existing authorization dependencies derive permissions from the current DB role.
There is no inactivity timeout or server-side time expiration, and no session
state kept in process memory. JWT signing-key changes do not invalidate sessions.
No raw credential is stored in DB, URLs, application logs, localStorage or
sessionStorage. Browser cookie storage necessarily retains the credential.

`POST /auth/sessions/logout` durably revokes the credential before the BFF clears
the cookie. It is idempotent and works for disabled accounts and revoked sessions.
`DELETE /auth/sessions/{session_id}` allows current admins to revoke a session
only within their authenticated company; unknown/foreign IDs return the same 204.
The browser does not forward arbitrary auth endpoints through the resource BFF.

The backend accepts opaque credentials through the existing bearer header, using
the reserved `axs_` prefix to select database resolution. `POST /auth/login` still
issues expiring JWTs with its original response, signing and authorization
contract. JWT API callers remain supported. Existing browser JWT cookies require
a new sign-in to adopt persistent sessions; no automatic credential exchange is
introduced. Opaque Logout does not change JWT API revocation semantics.

Cookie-authenticated mutations require exact same Origin at the BFF; Strict
SameSite adds protection. The backend consumes explicit bearer headers, not
browser cookies. Production must configure the correct HTTPS public origin.
Missing/revoked credentials and disabled/deleted users/inactive companies return
401. Permission failures return 403. Session-store failures fail closed with
generic 5xx; the BFF retains cookies on 403, network errors, timeout and 5xx.
The workspace preserves its existing recoverable retry state. Failed Logout
retains the cookie and shows a retry error rather than claiming revocation.

## Migration and limits

`migrations/016_persistent_auth_sessions.sql` is additive: UUID primary key,
user/company foreign keys, unique 64-character hash, timestamptz creation and
revocation fields, and user/company indexes. Cascading account deletion removes
only its session records. There are no operational data updates or expiry fields.
Existing migrations are unchanged. Migration-count regression assertions now
derive counts from discovered migration files.

No migration or connection to the persistent Owner Review database is authorized
or performed. Tests apply migrations only to generated isolated PostgreSQL DBs;
SQLite tests use temporary files. Disposable PostgreSQL databases are retained.
Deployment remains pending owner approval and a separately authorized migration.

Finite browser retention, cookie deletion/eviction, profile loss, private browsing,
and browser policy can still require sign-in. A 400-day cookie cannot guarantee
unlimited persistence during absence. Computer restart is covered indirectly by
durable server storage and actual browser-profile restart testing; no machine
reboot is performed. An already-authorized in-flight request may finish while a
concurrent Logout commits; subsequent validation rejects the revoked credential.
A late successful response can re-set that already-revoked cookie; it cannot
restore access, and the next authoritative 401 clears it. No credential rotation
or automatic session issuance occurs during renewal.

## Changed files

- `.gitignore`
- `backend/api/v1/auth.py`
- `backend/core/authentication.py`
- `backend/models/__init__.py`
- `backend/models/auth_session.py`
- `backend/services/auth_sessions.py`
- `frontend/src/lib/auth/server.ts`
- `frontend/src/app/api/auth/login/route.ts`
- `frontend/src/app/api/auth/logout/route.ts`
- `frontend/src/app/api/backend/[...path]/route.ts`
- `migrations/016_persistent_auth_sessions.sql`
- `requirements-test.txt`
- `tests/test_persistent_sessions.py`
- `tests/test_persistent_sessions_postgresql.py`
- `tests/test_task60_tracked_migrations.py`
- `tests/test_task62_migration_rehearsal.py`
- `tests/run_service_desk_regressions.py`
- `frontend/tests/mock-api.mjs`
- `frontend/tests/browser/foundation.spec.ts`
- `frontend/tests/browser/session-failures.spec.ts`
- `frontend/tests/phase3/persistent-sessions.spec.ts`
- `docs/service_desk_final_remediation.md`
- `docs/persistent_revocable_sessions.md`

## Validation

- Backend: **242 test executions across 16 isolated modules, 0 final failures**.
  This includes the existing eight-module Service Desk/authentication suite
  (176), persistent sessions including inherited JWT compatibility checks (17),
  real PostgreSQL process restart (1), tracked migrations (17), and database
  readiness/index/migration rehearsal/inventory/tenant checks (31).
  The reused JWT cases are counted as executions, not additional unique cases.
  Final per-module evidence is in ignored
  `test-results/service-desk-backend/final-results.json` and adjacent logs.
- Browser: **55 passed**, all four suites exited 0 against the final production
  build: foundation 11, Phase 3 32, full Phase 2 7, inventory/financial MVP 5.
  Phase 3 used disposable backend/frontend ports 18408/13408; MVP 18409/13409.
- Typecheck: passed. Lint: passed, 0 errors/warnings. Production build: passed.
- Persistent-cookie issuance, retention renewal and actual Chromium profile
  restart passed. Opaque Logout revocation/reuse, disabled/deleted users, inactive
  companies, current permissions, tenant isolation and admin revocation scope
  passed. Ancient creation metadata (1990) remained valid after a real backend
  process restart and JWT key change. Distinct actual server PIDs were verified.
- Backend store failures denied access with 500 and recovered after restoration.
  Browser tests verified actual BFF upstream network failure, timeout, 500, 403,
  401 and failed Logout; workspace tests verified retry/permission/Login states.
  Origin protection covered Login, Logout and operational/image mutations.
  Local browser tests used HTTP; HTTPS Secure selection was reviewed in code.
- The local test environment lacked `httpx`; it was installed in `.venv` and is
  declared in `requirements-test.txt`. No production dependency was changed.
- Validation infrastructure corrections: Playwright initially cleared the shared
  backend output directory, so backend artifacts now live outside that tree and
  the required modules were rerun. The PostgreSQL restart check initially hit a
  five-second client timeout and then a Windows temporary-directory/process
  cleanup error. Its test-only timeout is now 30 seconds and a child bootstrap
  records the actual server PID; the corrected isolated rerun passed (37.557s).
  The original aggregate result is retained alongside final consolidated results.
- Windows Playwright server teardown hung after assertions passed. Only verified
  disposable listening-port PIDs were stopped; each suite then reported exit 0.
  No normal application or Owner Review process was stopped.
- All changed files and additive migration contents reviewed; `git diff --check`
  passed. Local checkpoint hash is provided in the owner-review handoff. No push,
  merge, Owner Review migration, deployment or next-module work performed.
