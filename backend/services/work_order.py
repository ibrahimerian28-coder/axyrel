"""Business service for the Axyrel Work Order domain."""

from uuid import UUID

from sqlalchemy.orm import Session
from backend.core.service_lock import lock_service
from backend.repositories.schedule import ScheduleRepository

from backend.repositories.service_visit import ServiceVisitRepository
from backend.repositories.service_request import ServiceRequestRepository
from backend.repositories.work_order import WorkOrderRepository
from backend.schemas.work_order import WorkOrderSummary
from backend.services.service_visit import ServiceVisitService
from backend.services.status_lifecycle import ensure_work_order_transition


class WorkOrderService:
    """Application service for tenant-scoped work orders."""

    def __init__(
        self,
        repository: WorkOrderRepository | None = None,
        visit_repository: ServiceVisitRepository | None = None,
        visit_service: ServiceVisitService | None = None,
        request_repository: ServiceRequestRepository | None = None,
    ) -> None:
        self.repository = repository or WorkOrderRepository()
        self.request_repository = request_repository or ServiceRequestRepository()
        self.visit_repository = visit_repository or ServiceVisitRepository()
        self.visit_service = visit_service or ServiceVisitService(
            repository=self.visit_repository,
            work_order_repository=self.repository,
        )

    def list_work_orders(
        self,
        db: Session,
        company_id: UUID | None,
        customer_id: UUID | None = None,
        asset_id: UUID | None = None,
        service_request_id: UUID | None = None,
        status: str | None = None,
        assigned_technician_id: UUID | None = None,
        search: str | None = None,
    ):
        return self.repository.list(
            db,
            company_id,
            customer_id,
            asset_id,
            service_request_id,
            status,
            assigned_technician_id,
            search,
        )

    def get_summary(self, db: Session, company_id: UUID | None) -> WorkOrderSummary:
        work_orders = self.repository.list(db, company_id)
        return WorkOrderSummary(
            open_count=sum(
                order.status not in {"Completed", "Closed", "Deleted"}
                for order in work_orders
            )
        )

    def get_work_order(self, db: Session, company_id: UUID | None, work_order_id: UUID):
        return self.repository.get(db, company_id, work_order_id)

    def create_work_order(self, db: Session, company_id: UUID | None, data: dict):
        lock_service(db, company_id)
        status = data.get("status", "Open")
        ensure_work_order_transition("Open", status)
        self._validate_service_request(db, company_id, data.get("service_request_id"))
        return self.repository.create(db, company_id, data)

    def _validate_service_request(self, db, company_id, request_id):
        if request_id is not None and self.request_repository.get(db, company_id, request_id) is None:
            raise ValueError("Service request not found.")

    def update_work_order(
        self, db: Session, company_id: UUID | None, work_order_id: UUID, data: dict
    ):
        lock_service(db, company_id)
        work_order = self.repository.get(db, company_id, work_order_id)
        if work_order is None:
            return None

        if "service_request_id" in data:
            self._validate_service_request(db, company_id, data["service_request_id"])

        target_status = data.get("status")
        if target_status is not None:
            target_status = ensure_work_order_transition(work_order.status, target_status)
            data = {**data, "status": target_status}
            if target_status == "Completed":
                visits = self.visit_repository.list(db, company_id, work_order_id=work_order_id)
                schedules = ScheduleRepository().list(db, company_id, work_order_id=work_order_id)
                if any(v.status in {"Planned", "In Progress"} for v in visits) or any(s.status == "Scheduled" for s in schedules):
                    raise ValueError("Resolve remaining appointments and active visits before completing the job")

        updated = self.repository.update(db, company_id, work_order_id, data)
        if updated is None:
            return None

        if target_status == "Cancelled":
            for schedule in ScheduleRepository().list(db, company_id, work_order_id=work_order_id):
                if schedule.status == "Scheduled":
                    ScheduleRepository().update(db, company_id, schedule.id, {"status": "Cancelled"})
            visits = self.visit_repository.list(
                db, company_id, work_order_id=work_order_id
            )
            for visit in visits:
                if visit.status == "Cancelled":
                    continue
                self.visit_service.update_visit(
                    db, company_id, visit.id, {"status": "Cancelled"}
                )
        return updated

    def delete_work_order(self, db: Session, company_id: UUID | None, work_order_id: UUID):
        lock_service(db, company_id)
        visits = self.visit_repository.list(db, company_id, work_order_id=work_order_id)
        for visit in visits:
            if visit.status != "Cancelled":
                self.visit_service.update_visit(
                    db, company_id, visit.id, {"status": "Cancelled"}
                )
        return self.repository.soft_delete(db, company_id, work_order_id)
