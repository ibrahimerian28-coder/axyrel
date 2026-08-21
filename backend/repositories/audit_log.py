"""Tenant-scoped, append-only persistence operations for audit logs."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.tenant_isolation import require_company_id
from backend.models.audit_log import AuditLog
from backend.repositories.base import TenantScopedRepository


class AuditLogRepository(TenantScopedRepository):
    """Repository intentionally exposes create/read only; audit entries are immutable."""

    def get(self, db: Session, company_id: UUID | None, audit_log_id: UUID) -> AuditLog | None:
        company_id = self._require_company_scope(company_id)
        return db.scalar(
            select(AuditLog).where(
                AuditLog.id == audit_log_id,
                AuditLog.company_id == company_id,
            )
        )

    def list(
        self,
        db: Session,
        company_id: UUID | None,
        actor_user_id: UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[AuditLog]:
        company_id = require_company_id(company_id)
        stmt = select(AuditLog).where(AuditLog.company_id == company_id)
        if actor_user_id is not None:
            stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        if entity_type is not None:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if entity_id is not None:
            stmt = stmt.where(AuditLog.entity_id == entity_id)
        if start_at is not None:
            stmt = stmt.where(AuditLog.created_at >= start_at)
        if end_at is not None:
            stmt = stmt.where(AuditLog.created_at <= end_at)
        return list(db.scalars(stmt.order_by(AuditLog.created_at.desc())).all())

    def create(self, db: Session, company_id: UUID | None, data: dict) -> AuditLog:
        company_id = require_company_id(company_id)
        record = AuditLog(company_id=company_id, **data)
        db.add(record)
        db.flush()
        return record
