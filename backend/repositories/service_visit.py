"""Persistence operations for tenant-scoped service visits."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.tenant_isolation import require_company_id
from backend.models.service_visit import ServiceVisit
from backend.repositories.base import TenantScopedRepository


class ServiceVisitRepository(TenantScopedRepository):
    """Tenant-scoped repository for service visit records."""

    def get(self, db: Session, company_id: UUID | None, visit_id: UUID) -> ServiceVisit | None:
        company_id = self._require_company_scope(company_id)
        return db.scalar(
            select(ServiceVisit).where(
                ServiceVisit.id == visit_id,
                ServiceVisit.company_id == company_id,
                ServiceVisit.status != "Deleted",
            )
        )

    def list(
        self,
        db: Session,
        company_id: UUID | None,
        work_order_id: UUID | None = None,
        schedule_id: UUID | None = None,
        technician_id: UUID | None = None,
        status: str | None = None,
        start_from: datetime | None = None,
        start_to: datetime | None = None,
    ) -> list[ServiceVisit]:
        company_id = require_company_id(company_id)
        stmt = select(ServiceVisit).where(
            ServiceVisit.company_id == company_id,
            ServiceVisit.status != "Deleted",
        )
        if work_order_id is not None:
            stmt = stmt.where(ServiceVisit.work_order_id == work_order_id)
        if schedule_id is not None:
            stmt = stmt.where(ServiceVisit.schedule_id == schedule_id)
        if technician_id is not None:
            stmt = stmt.where(ServiceVisit.technician_id == technician_id)
        if status and status.strip():
            stmt = stmt.where(ServiceVisit.status == status.strip())
        if start_from is not None:
            stmt = stmt.where(ServiceVisit.actual_start_at >= start_from)
        if start_to is not None:
            stmt = stmt.where(ServiceVisit.actual_start_at <= start_to)
        return list(db.scalars(stmt.order_by(ServiceVisit.created_at.desc())).all())

    def create(self, db: Session, company_id: UUID | None, data: dict) -> ServiceVisit:
        company_id = require_company_id(company_id)
        visit = ServiceVisit(company_id=company_id, **data)
        db.add(visit)
        db.flush()
        return visit

    def update(
        self, db: Session, company_id: UUID | None, visit_id: UUID, data: dict
    ) -> ServiceVisit | None:
        visit = self.get(db, company_id, visit_id)
        if visit is None:
            return None
        for key, value in data.items():
            setattr(visit, key, value)
        db.flush()
        return visit

    def soft_delete(
        self, db: Session, company_id: UUID | None, visit_id: UUID
    ) -> ServiceVisit | None:
        visit = self.get(db, company_id, visit_id)
        if visit is None:
            return None
        visit.status = "Deleted"
        db.flush()
        return visit
