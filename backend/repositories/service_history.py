"""Persistence operations for tenant-scoped service history."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.tenant_isolation import require_company_id
from backend.models.service_history import ServiceHistory
from backend.repositories.base import TenantScopedRepository


class ServiceHistoryRepository(TenantScopedRepository):
    """Tenant-scoped repository for service history records."""

    def get(self, db: Session, company_id: UUID | None, history_id: UUID) -> ServiceHistory | None:
        company_id = self._require_company_scope(company_id)
        return db.scalar(select(ServiceHistory).where(
            ServiceHistory.id == history_id,
            ServiceHistory.company_id == company_id,
            ServiceHistory.status != "Deleted",
        ))

    def list(
        self, db: Session, company_id: UUID | None, customer_id: UUID | None = None,
        asset_id: UUID | None = None, service_visit_id: UUID | None = None,
        work_order_id: UUID | None = None, technician_id: UUID | None = None,
        service_date_from: datetime | None = None, service_date_to: datetime | None = None,
    ) -> list[ServiceHistory]:
        company_id = require_company_id(company_id)
        stmt = select(ServiceHistory).where(
            ServiceHistory.company_id == company_id, ServiceHistory.status != "Deleted"
        )
        if customer_id is not None: stmt = stmt.where(ServiceHistory.customer_id == customer_id)
        if asset_id is not None: stmt = stmt.where(ServiceHistory.asset_id == asset_id)
        if service_visit_id is not None: stmt = stmt.where(ServiceHistory.service_visit_id == service_visit_id)
        if work_order_id is not None: stmt = stmt.where(ServiceHistory.work_order_id == work_order_id)
        if technician_id is not None: stmt = stmt.where(ServiceHistory.technician_id == technician_id)
        if service_date_from is not None: stmt = stmt.where(ServiceHistory.service_date >= service_date_from)
        if service_date_to is not None: stmt = stmt.where(ServiceHistory.service_date <= service_date_to)
        return list(db.scalars(stmt.order_by(ServiceHistory.service_date.desc(), ServiceHistory.created_at.desc())).all())

    def create(self, db: Session, company_id: UUID | None, data: dict) -> ServiceHistory:
        company_id = require_company_id(company_id)
        record = ServiceHistory(company_id=company_id, **data)
        db.add(record)
        db.flush()
        return record

    def update(self, db: Session, company_id: UUID | None, history_id: UUID, data: dict) -> ServiceHistory | None:
        record = self.get(db, company_id, history_id)
        if record is None: return None
        for key, value in data.items(): setattr(record, key, value)
        db.flush()
        return record

    def soft_delete(self, db: Session, company_id: UUID | None, history_id: UUID) -> ServiceHistory | None:
        record = self.get(db, company_id, history_id)
        if record is None: return None
        record.status = "Deleted"
        db.flush()
        return record
