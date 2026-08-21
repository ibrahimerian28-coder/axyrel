"""Business service for immutable activity/audit logs."""
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.audit_log import AuditLogRepository


class AuditLogService:
    """Creates and queries audit records without exposing mutation operations."""

    def __init__(self, repository: AuditLogRepository | None = None) -> None:
        self.repository = repository or AuditLogRepository()

    def create_audit_log(self, db: Session, company_id: UUID | None, data: dict):
        return self.repository.create(db, company_id, data)

    def get_audit_log(self, db: Session, company_id: UUID | None, audit_log_id: UUID):
        return self.repository.get(db, company_id, audit_log_id)

    def list_audit_logs(self, db: Session, company_id: UUID | None, **filters):
        return self.repository.list(db, company_id, **filters)
