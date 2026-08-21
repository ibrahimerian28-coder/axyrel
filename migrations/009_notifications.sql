-- Task 41: Notifications foundation
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    recipient_user_id UUID NULL,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    status VARCHAR(20) NOT NULL DEFAULT 'unread',
    entity_type VARCHAR(50) NULL,
    entity_id UUID NULL,
    action_url VARCHAR(500) NULL,
    read_at TIMESTAMP NULL,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_notifications_company_id ON notifications(company_id);
CREATE INDEX IF NOT EXISTS ix_notifications_recipient_user_id ON notifications(recipient_user_id);
CREATE INDEX IF NOT EXISTS ix_notifications_notification_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS ix_notifications_priority ON notifications(priority);
CREATE INDEX IF NOT EXISTS ix_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS ix_notifications_expires_at ON notifications(expires_at);
CREATE INDEX IF NOT EXISTS ix_notifications_company_recipient_status
    ON notifications(company_id, recipient_user_id, status);
CREATE INDEX IF NOT EXISTS ix_notifications_company_created_at
    ON notifications(company_id, created_at);
