"""Business service for the Axyrel Work Order domain."""

from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.work_order import WorkOrderRepository


class WorkOrderService:
    """Application service for tenant-scoped work orders."""

    def __init__(self, repository: WorkOrderRepository | None = None) -> None:
        self.repository = repository or WorkOrderRepository()

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
        return self.repository.create(db, company_id, data)

    def update_work_order(
        self, db: Session, company_id: UUID | None, work_order_id: UUID, data: dict
    ):
        return self.repository.update(db, company_id, work_order_id, data)

    def delete_work_order(self, db: Session, company_id: UUID | None, work_order_id: UUID):
        return self.repository.soft_delete(db, company_id, work_order_id)
