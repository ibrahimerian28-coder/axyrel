"""Business service for the Axyrel Work Order domain."""

from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.service_visit import ServiceVisitRepository
from backend.repositories.work_order import WorkOrderRepository
from backend.services.service_visit import ServiceVisitService
from backend.services.status_lifecycle import ensure_work_order_transition


class WorkOrderService:
    """Application service for tenant-scoped work orders."""

    def __init__(
        self,
        repository: WorkOrderRepository | None = None,
        visit_repository: ServiceVisitRepository | None = None,
        visit_service: ServiceVisitService | None = None,
    ) -> None:
        self.repository = repository or WorkOrderRepository()
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

    def get_work_order(self, db: Session, company_id: UUID | None, work_order_id: UUID):
        return self.repository.get(db, company_id, work_order_id)

    def create_work_order(self, db: Session, company_id: UUID | None, data: dict):
        status = data.get("status", "Open")
        ensure_work_order_transition("Open", status)
        return self.repository.create(db, company_id, data)

    def update_work_order(
        self, db: Session, company_id: UUID | None, work_order_id: UUID, data: dict
    ):
        work_order = self.repository.get(db, company_id, work_order_id)
        if work_order is None:
            return None

        target_status = data.get("status")
        if target_status is not None:
            target_status = ensure_work_order_transition(work_order.status, target_status)
            data = {**data, "status": target_status}

        updated = self.repository.update(db, company_id, work_order_id, data)
        if updated is None:
            return None

        if target_status == "Cancelled":
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
        visits = self.visit_repository.list(db, company_id, work_order_id=work_order_id)
        for visit in visits:
            if visit.status != "Cancelled":
                self.visit_service.update_visit(
                    db, company_id, visit.id, {"status": "Cancelled"}
                )
        return self.repository.soft_delete(db, company_id, work_order_id)
