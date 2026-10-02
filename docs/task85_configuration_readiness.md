# Task 85 — Offline Production Configuration Readiness

Authority: OD-25. No production target, credentials, infrastructure or deployment is approved. Acceptance means **OFFLINE PRODUCTION CONFIGURATION / SECURITY READINESS VERIFIED** only.

The existing typed settings load environment variables/.env in normal operation. get_settings now validates before dependent database-engine initialization, and FastAPI's ASGI lifespan explicitly validates again before yielding to request serving. Cached settings therefore do not bypass the startup check. Invalid settings loading fails with a generic configuration error without exposing the input or chained validation error. Validator messages identify the field/rule, never its value.

Production mode is recognized case-insensitively with surrounding whitespace ignored. Required checks:

- SECRET_KEY must be nonblank and cannot use the existing change-me-in-production default, including padded forms.
- The existing prohibition on DATABASE_URL containing localhost is preserved, including case variants. No approved local production deployment is inferred from disposable test PostgreSQL.
- DATABASE_URL must parse as a PostgreSQL URL with a host, database and valid port syntax. Empty/malformed or non-PostgreSQL values are rejected under the accepted PostgreSQL architecture.
- Existing typed constraints, including positive token expiry/timeouts, still apply. Sensitive inputs are hidden from configuration error text.

No provider-specific TLS, domain, credential-length, secret-manager, role or network-topology policy is selected here. These checks preserve/enforce accepted baseline requirements and required-value validity; passing them is not comprehensive production security certification. A future actual target requires separately approved configuration/security/operational requirements. No production secret is generated, requested or stored.

Development/test mode remains usable with existing local/default configuration and is not subject to production-only rules. Normal typed configuration parsing remains in effect. Public API health/auth/error contracts and database-backed identity semantics are unchanged.

Offline verification command:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_task85_configuration_readiness.py
```

The tests launch isolated subprocesses from temporary directories without workspace .env access, with synthetic environment values. Acceptable URLs use database.invalid, are never resolved/connected to, and actual database connections are guarded. In-process TestClient uses no external HTTP. TestClient's Windows asyncio internal socket pair remains available. Tests cover rejected/default/absent/typed-invalid configuration, mode normalization, health/auth compatibility, ASGI validator invocation and refusal, pre-engine validation and secret-safe captured stdout/stderr. No real database or external service is probed.

Actual production deployment, schema application, DNS/certificates/secrets, operational backups/restore and production smoke testing remain outside this task and separately gated. OD-21 migration and OD-22/23 real-data safeguards remain unchanged.
