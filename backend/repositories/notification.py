"""Tenant-scoped persistence operations for notifications."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.tenant_isolation import require_company_id
from backend.models.notification import Notification
from backend.repositories.base import TenantScopedRepository


class NotificationRepository(TenantScopedRepository):
    def get(self, db: Session, company_id: UUID | None, notification_id: UUID) -> Notification | None:
        company_id = self._require_company_scope(company_id)
        return db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.company_id == company_id,
            )
        )

    def list(
        self,
        db: Session,
        company_id: UUID | None,
        recipient_user_id: UUID | None = None,
        status: str | None = None,
        notification_type: str | None = None,
        include_expired: bool = False,
    ) -> list[Notification]:
        company_id = require_company_id(company_id)
        stmt = select(Notification).where(Notification.company_id == company_id)
        if recipient_user_id is not None:
            stmt = stmt.where(Notification.recipient_user_id == recipient_user_id)
        if status is not None:
            stmt = stmt.where(Notification.status == status)
        if notification_type is not None:
            stmt = stmt.where(Notification.notification_type == notification_type)
        if not include_expired:
            stmt = stmt.where(
                (Notification.expires_at.is_(None)) | (Notification.expires_at > datetime.utcnow())
            )
        return list(db.scalars(stmt.order_by(Notification.created_at.desc())).all())

    def create(self, db: Session, company_id: UUID | None, data: dict) -> Notification:
        company_id = require_company_id(company_id)
        record = Notification(company_id=company_id, **data)
        db.add(record)
        db.flush()
        return record

    def update(
        self, db: Session, company_id: UUID | None, notification_id: UUID, data: dict
    ) -> Notification | None:
        record = self.get(db, company_id, notification_id)
        if record is None:
            return None
        for key, value in data.items():
            setattr(record, key, value)
        db.flush()
        return record

    def mark_read(self, db: Session, company_id: UUID | None, notification_id: UUID) -> Notification | None:
        record = self.get(db, company_id, notification_id)
        if record is None:
            return None
        record.status = "read"
        record.read_at = datetime.utcnow()
        db.flush()
        return record
