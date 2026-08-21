# Task 43 — Settings / Configuration

## Scope
Centralize runtime/backend configuration without changing the legacy Streamlit UI contract.

## Implemented
- Typed `backend.core.config.Settings` based on pydantic-settings.
- Environment variable aliases for application name/version/environment/API prefix.
- Centralized DATABASE_URL, SECRET_KEY and token expiry settings.
- `.env.example` documenting supported runtime variables.
- Production security validation rejecting the development secret and localhost DB.
- Legacy `utils.config` kept as a compatibility facade so existing Streamlit imports do not break.

## Security
Secrets belong in `.env` or the deployment secret manager, not source control.
The existing Streamlit `st.secrets` password mechanism is intentionally not removed
in this task because that is part of the legacy UI/API integration work.

## Not included
- API endpoints
- Streamlit UI redesign
- authentication rewrite
- removal of Google Apps Script configuration
- production secret migration
- deployment configuration

Those belong to later integration/deployment tasks.
