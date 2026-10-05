"""Business service for the Axyrel Scheduling domain."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from backend.core.event_time import normalize_event_time
from backend.core.service_lock import lock_service
from backend.repositories.service_visit import ServiceVisitRepository
from backend.repositories.schedule import ScheduleRepository
from backend.repositories.work_order import WorkOrderRepository


class ScheduleService:
    """Application service for tenant-scoped schedules."""

    def __init__(self, repository: ScheduleRepository | None = None,
                 work_order_repository: WorkOrderRepository | None = None) -> None:
        self.repository = repository or ScheduleRepository()
        self.work_order_repository = work_order_repository or WorkOrderRepository()

    def _validate_work_order(self, db: Session, company_id: UUID | None, work_order_id: UUID | None):
        if work_order_id is not None and self.work_order_repository.get(db, company_id, work_order_id) is None:
            raise ValueError("Work order not found.")

    @staticmethod
    def _normalized_data(data: dict) -> dict:
        normalized = dict(data)
        for field in ("start_at", "end_at"):
            if normalized.get(field) is not None:
                normalized[field] = normalize_event_time(normalized[field])
        return normalized

    @staticmethod
    def _validate_range(start_at: datetime | None, end_at: datetime | None) -> None:
        # Explicit null retains the existing required-column persistence contract.
        if start_at is not None and end_at is not None:
            if normalize_event_time(end_at) <= normalize_event_time(start_at):
                raise ValueError("end_at must be later than start_at")

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
        start_from = normalize_event_time(start_from) if start_from is not None else None
        start_to = normalize_event_time(start_to) if start_to is not None else None
        return self.repository.list(
            db, company_id, work_order_id, technician_id, status, start_from, start_to
        )

    def get_schedule(self, db: Session, company_id: UUID | None, schedule_id: UUID):
        return self.repository.get(db, company_id, schedule_id)

    def create_schedule(self, db: Session, company_id: UUID | None, data: dict):
        lock_service(db, company_id)
        data = self._normalized_data(data)
        self._validate_work_order(db, company_id, data.get("work_order_id"))
        order = self.work_order_repository.get(db, company_id, data.get("work_order_id"))
        if order and order.status in {"Completed", "Cancelled"}:
            raise ValueError("Cannot schedule a terminal work order")
        self._validate_range(data.get("start_at"), data.get("end_at"))
        return self.repository.create(db, company_id, data)

    def update_schedule(self, db: Session, company_id: UUID | None, schedule_id: UUID, data: dict):
        lock_service(db, company_id)
        record = self.repository.get(db, company_id, schedule_id)
        if record is None:
            return None
        visits = ServiceVisitRepository().list(db, company_id, schedule_id=schedule_id)
        if visits and any(key in data and data[key] != getattr(record, key) for key in ("work_order_id", "start_at", "end_at", "technician_id", "status")):
            raise ValueError("An executed appointment cannot be rescheduled; use a follow-up appointment or cancel its visit")
        data = self._normalized_data(data)
        if "work_order_id" in data:
            self._validate_work_order(db, company_id, data["work_order_id"])
        self._validate_range(data.get("start_at", record.start_at), data.get("end_at", record.end_at))
        return self.repository.update(db, company_id, schedule_id, data)

    def delete_schedule(self, db: Session, company_id: UUID | None, schedule_id: UUID):
        lock_service(db, company_id)
        if ServiceVisitRepository().list(db, company_id, schedule_id=schedule_id):
            raise ValueError("An executed appointment must be retained; cancel its visit instead")
        return self.repository.soft_delete(db, company_id, schedule_id)
