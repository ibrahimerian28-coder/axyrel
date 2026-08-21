"""Business service for the Axyrel Scheduling domain."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.schedule import ScheduleRepository


class ScheduleService:
    """Application service for tenant-scoped schedules."""

    def __init__(self, repository: ScheduleRepository | None = None) -> None:
        self.repository = repository or ScheduleRepository()

    def list_schedules(
        self,
        db: Session,
        company_id: UUID | None,
        work_order_id: UUID | None = None,
        technician_id: UUID | None = None,
        status: str | None = None,
        start_from: datetime | None = None,
        start_to: datetime | None = None,
    ):
        return self.repository.list(
            db, company_id, work_order_id, technician_id, status, start_from, start_to
        )

    def get_schedule(self, db: Session, company_id: UUID | None, schedule_id: UUID):
        return self.repository.get(db, company_id, schedule_id)

    def create_schedule(self, db: Session, company_id: UUID | None, data: dict):
        return self.repository.create(db, company_id, data)

    def update_schedule(self, db: Session, company_id: UUID | None, schedule_id: UUID, data: dict):
        return self.repository.update(db, company_id, schedule_id, data)

    def delete_schedule(self, db: Session, company_id: UUID | None, schedule_id: UUID):
        return self.repository.soft_delete(db, company_id, schedule_id)
