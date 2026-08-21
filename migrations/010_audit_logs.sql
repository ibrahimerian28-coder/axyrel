-- Task 42: Activity / Audit Log
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    actor_user_id UUID NULL,
    action VARCHAR(80) NOT NULL,
    entity_type VARCHAR(80) NULL,
    entity_id UUID NULL,
    description TEXT NULL,
    event_metadata JSONB NULL,
    ip_address VARCHAR(64) NULL,
    user_agent VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_company_created_at
    ON audit_logs (company_id, created_at);
CREATE INDEX IF NOT EXISTS ix_audit_logs_company_actor
    ON audit_logs (company_id, actor_user_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_company_entity
    ON audit_logs (company_id, entity_type, entity_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_company_action
    ON audit_logs (company_id, action);

-- Audit records are append-only by application design. No UPDATE/DELETE
-- repository operations are exposed in Task 42.
