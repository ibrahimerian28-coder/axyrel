"""Business service for tenant-scoped notifications."""
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.notification import NotificationRepository


class NotificationService:
    def __init__(self, repository: NotificationRepository | None = None) -> None:
        self.repository = repository or NotificationRepository()

    def list_notifications(self, db: Session, company_id: UUID | None, **filters):
        return self.repository.list(db, company_id, **filters)

    def get_notification(self, db: Session, company_id: UUID | None, notification_id: UUID):
        return self.repository.get(db, company_id, notification_id)

    def create_notification(self, db: Session, company_id: UUID | None, data: dict):
        return self.repository.create(db, company_id, data)

    def update_notification(self, db: Session, company_id: UUID | None, notification_id: UUID, data: dict):
        return self.repository.update(db, company_id, notification_id, data)

    def mark_read(self, db: Session, company_id: UUID | None, notification_id: UUID):
        return self.repository.mark_read(db, company_id, notification_id)
