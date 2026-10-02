-- Task 61: complete existing ORM-declared non-unique indexes.
-- No table/column, uniqueness, foreign-key or business-rule changes.
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_audit_logs_company_id ON audit_logs(company_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_actor_user_id ON audit_logs(actor_user_id);
