# Task 49 — Final Checkpoint

- Date: **2026-10-02**.
- Official task: **Task 49 — Standardize Authentication Context**.
- Status at checkpoint creation: **ACCEPTED — pending Git commit/push**.

## 1. Baseline

- Project root: `D:\Axyrel_BACKUP_BEFORE_GEMINI`.
- Branch: `checkpoint/pre-gemini-task46`.
- Pre-Task49 committed HEAD: `c3a59187dd61ab337dee1ec399dcda63b5f27c82`.
- Task 48: **ACCEPTED / COMMITTED / PUSHED**.
- Task 50: **NOT STARTED**.

## 2. Task 49 Objective

Task 49 standardized authenticated request context without redesigning authentication.

```text
Bearer token
    → existing token validation
    → existing active database User/company validation
    → canonical AuthContext
        ├─ CurrentUser → ORM User
        ├─ CompanyID → authenticated company UUID
        ├─ permission guard → database role → existing ROLE_PERMISSIONS
        └─ /auth/me → database identity/effective permissions
```

## 3. Implemented Changes

| File | Implemented change |
|---|---|
| `backend/core/authentication.py` | Introduced frozen `AuthContext` and canonical `get_auth_context()` resolver. Company identity derives from the validated database User. CurrentUser remains an ORM User compatibility projection. Context construction remains role-agnostic; request-scoped FastAPI dependency caching is preserved. |
| `backend/api/dependencies.py` | CompanyID projects from canonical AuthContext. Existing tenant ContextVar assignment is preserved; the ContextVar remains secondary rather than tenant authority. |
| `backend/core/authorization.py` | Permission guard consumes canonical AuthContext and uses the current database User role. Existing Role conversion and ROLE_PERMISSIONS are unchanged. The dependency still returns ORM User. |
| `backend/api/v1/auth.py` | `/auth/me` consumes canonical AuthContext, with database-authoritative identity and permissions. Login implementation is unchanged. |
| `tests/test_task49_authentication_context.py` | Added 43 focused Task 49 tests using a disposable database. |

The final dependency audit covered 79 application endpoints: 76 domain endpoints use CompanyID and a permission guard through canonical context; `/auth/me` consumes context directly. Login remains separate and `/health` remains public. Representative runtime tests verified one token decode and one active-user lookup per request.

## 4. Trust / Security Model Preserved

- Database User remains identity authority; company_id comes from the authenticated database User.
- JWT role and permissions claims remain informational. Forged/stale privilege claims cannot elevate access; database role changes after token issuance are respected.
- Caller headers, query parameters, and request bodies cannot select authenticated tenant identity.
- No company or membership claim was added to JWT.
- No global authenticated user/context or cross-request context reuse was introduced.
- ORM User remains within the normal request DB session lifetime. The frozen context wrapper does not make the ORM entity immutable.

## 5. Token Contract Preserved

Task 49 did not change HS256, SECRET_KEY behavior, token lifetime, sub format, expiration behavior, accepted missing-exp compatibility, informational role/permissions claims, login token response, or token_type behavior. No token redesign occurred.

## 6. Error Contracts Preserved

| Condition | HTTP status | Detail | Bearer challenge |
|---|---|---|---|
| Missing/non-Bearer authentication | 401 | `Not authenticated` | Yes |
| Invalid/expired token | 401 | `Invalid or expired access token` | Yes |
| Missing subject | 401 | `Access token has no subject` | Yes |
| Invalid UUID subject | 401 | `Access token has an invalid subject` | Yes |
| Unknown/inactive user or missing/inactive company | 401 | `User is inactive, company is inactive, or user no longer exists` | Yes |
| Permission denied | 403 | `Insufficient permissions` | No |
| Invalid database role at permission guard | 403 | `User has an invalid application role` | No |
| Invalid database role at login | Explicit 500 | `User has an invalid application role` | No |
| Invalid database role at `/auth/me` | Safe JSON 500 | `{"detail":"Internal Server Error"}` | No |

The authentication challenge is `WWW-Authenticate: Bearer`. Task 49 intentionally did not unify the existing entry-point distinctions.

## 7. Tenant Isolation

Trusted tenant path:

```text
validated database User
    → AuthContext.company_id
    → CompanyID
    → tenant-scoped services/repositories
```

X-Company-ID and other caller company headers cannot select tenant. Query company values cannot select tenant; request-body company values do not establish authenticated tenant identity. JWT company claims are not used. ContextVar is not the source of tenant authority.

## 8. Test / Acceptance Results

| Final acceptance verification | Result |
|---|---|
| Task 49 | 43/43 PASS |
| Task 46 authentication | 10/10 PASS |
| Task 46 Service Visit | 6/6 PASS |
| Task 47 | 58/58 PASS |
| Task 48 | 60/60 PASS |
| Total | **177/177 PASS** |
| Acceptance matrix | **38/38 PASS** |
| Blocking defects | **0** |
| `git diff --check` | PASS |
| Complete cumulative diff review | READY FOR FINAL ACCEPTANCE |

All five suites were rerun for the final acceptance review using the project interpreter with `-B`. This document records that completed run; tests were not rerun for this documentation-only step.

## 9. Final Task 49 File Set

Production:

- `backend/core/authentication.py`
- `backend/api/dependencies.py`
- `backend/core/authorization.py`
- `backend/api/v1/auth.py`

Tests: `tests/test_task49_authentication_context.py`.

Checkpoint: `docs/task49_final_checkpoint.md`.

## 10. Out of Scope / Unchanged

Task 49 introduced no CompanyMembership, company switching, new authentication features, refresh tokens, MFA, password-reset architecture, new roles, new permissions, or audit attribution changes.

No schema changes, ORM model changes, migrations, domain-router mass edits, legacy Streamlit authentication restoration, timezone work, or Task 50 work were introduced. Design Freeze remained intact. API-backed mode remains the official required MVP mode.

## 11. Carry-Forward

- Task 52 must resolve/adopt the official Axyrel Date/Time & Timezone policy before final acceptance of Scheduling integration, including outstanding Schedule effective-state timestamp validation.
- Task 53 must verify/apply the approved timezone policy to Service Visit integration, including outstanding Service Visit effective-state timestamp validation.
- Long-term direction remains timezone-aware UTC instants plus separate timezone metadata, subject to later explicit schema/migration approval. Calendar-only business dates remain DATE.
- The Task 48 PostgreSQL uniqueness integration limitation remains: structured PostgreSQL diagnostics were tested with real psycopg exception classes and simulated diagnostics, but no isolated live PostgreSQL write integration was performed.

These items were not reinterpreted or resolved in Task 49.

## 12. Git State at Checkpoint Creation

At document creation time, Task 49 is accepted but **not yet committed or pushed**. The committed HEAD remains the pre-Task49 baseline above. No future Task 49 commit hash is recorded. No staging, commit, push, or merge was performed during checkpoint creation; main remains untouched.

The working tree at creation contains exactly:

```text
 M backend/core/authentication.py
 M backend/api/dependencies.py
 M backend/core/authorization.py
 M backend/api/v1/auth.py
?? tests/test_task49_authentication_context.py
?? docs/task49_final_checkpoint.md
```

This section records historical creation-time state and does not describe a later Git finalization.

## 13. Next Step

**Git finalization of Task 49 only.**

Task 50 remains **NOT STARTED** until Task 49 commit/push and post-commit verification are complete.
