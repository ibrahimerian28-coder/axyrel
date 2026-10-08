-- Additive only: no operational records changed. No server-side time expiration.
CREATE TABLE auth_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    secret_hash VARCHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ NULL
);
CREATE INDEX ix_auth_sessions_user_id ON auth_sessions(user_id);
CREATE INDEX ix_auth_sessions_company_id ON auth_sessions(company_id);
