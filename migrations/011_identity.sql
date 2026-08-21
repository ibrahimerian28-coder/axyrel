-- Task 46 — Identity / Authentication foundation
-- Database-backed company and user identity for the MVP.
-- company_memberships is intentionally NOT part of the MVP.

CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
    email VARCHAR(320) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    password_hash VARCHAR(500) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'technician'
        CHECK (role IN ('admin', 'manager', 'technician')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_lower
    ON users (LOWER(email));
CREATE INDEX IF NOT EXISTS ix_users_company_id ON users(company_id);
CREATE INDEX IF NOT EXISTS ix_users_company_role ON users(company_id, role);
CREATE INDEX IF NOT EXISTS ix_users_active ON users(is_active);
