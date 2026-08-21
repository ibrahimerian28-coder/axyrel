"""Persistence operations for tenant-scoped schedules."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.tenant_isolation import require_company_id
from backend.models.schedule import Schedule
from backend.repositories.base import TenantScopedRepository


class ScheduleRepository(TenantScopedRepository):
    """Tenant-scoped repository for schedule records."""

    def get(self, db: Session, company_id: UUID | None, schedule_id: UUID) -> Schedule | None:
        company_id = self._require_company_scope(company_id)
        return db.scalar(
            select(Schedule).where(
                Schedule.id == schedule_id,
                Schedule.company_id == company_id,
                Schedule.status != "Deleted",
            )
        )

    def list(
        self,
        db: Session,
        company_id: UUID | None,
        work_order_id: UUID | None = None,
        technician_id: UUID | None = None,
        status: str | None = None,
        start_from: datetime | None = None,
        start_to: datetime | None = None,
    ) -> list[Schedule]:
        company_id = require_company_id(company_id)
        stmt = select(Schedule).where(
            Schedule.company_id == company_id,
            Schedule.status != "Deleted",
        )
        if work_order_id is not None:
            stmt = stmt.where(Schedule.work_order_id == work_order_id)
        if technician_id is not None:
            stmt = stmt.where(Schedule.technician_id == technician_id)
        if status and status.strip():
            stmt = stmt.where(Schedule.status == status.strip())
        if start_from is not None:
            stmt = stmt.where(Schedule.start_at >= start_from)
        if start_to is not None:
            stmt = stmt.where(Schedule.start_at <= start_to)

        return list(db.scalars(stmt.order_by(Schedule.start_at.asc())).all())

    def create(self, db: Session, company_id: UUID | None, data: dict) -> Schedule:
        company_id = require_company_id(company_id)
        schedule = Schedule(company_id=company_id, **data)
        db.add(schedule)
        db.flush()
        return schedule

    def update(
        self,
        db: Session,
        company_id: UUID | None,
        schedule_id: UUID,
        data: dict,
    ) -> Schedule | None:
        schedule = self.get(db, company_id, schedule_id)
        if schedule is None:
            return None
        for key, value in data.items():
            setattr(schedule, key, value)
        db.flush()
        return schedule

    def soft_delete(
        self, db: Session, company_id: UUID | None, schedule_id: UUID
    ) -> Schedule | None:
        schedule = self.get(db, company_id, schedule_id)
        if schedule is None:
            return None
        schedule.status = "Deleted"
        db.flush()
        return schedule
