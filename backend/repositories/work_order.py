"""Persistence operations for tenant-scoped Work Orders."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.tenant_isolation import require_company_id
from backend.models.work_order import WorkOrder
from backend.repositories.base import TenantScopedRepository


class WorkOrderRepository(TenantScopedRepository):
    """Tenant-scoped repository for Work Order records."""

    def get(
        self, db: Session, company_id: UUID | None, work_order_id: UUID
    ) -> WorkOrder | None:
        company_id = self._require_company_scope(company_id)
        return db.scalar(
            select(WorkOrder).where(
                WorkOrder.id == work_order_id,
                WorkOrder.company_id == company_id,
                WorkOrder.status != "Deleted",
            )
        )

    def list(
        self,
        db: Session,
        company_id: UUID | None,
        customer_id: UUID | None = None,
        asset_id: UUID | None = None,
        service_request_id: UUID | None = None,
        status: str | None = None,
        assigned_technician_id: UUID | None = None,
        search: str | None = None,
    ) -> list[WorkOrder]:
        company_id = require_company_id(company_id)
        stmt = select(WorkOrder).where(
            WorkOrder.company_id == company_id,
            WorkOrder.status != "Deleted",
        )

        if customer_id is not None:
            stmt = stmt.where(WorkOrder.customer_id == customer_id)
        if asset_id is not None:
            stmt = stmt.where(WorkOrder.asset_id == asset_id)
        if service_request_id is not None:
            stmt = stmt.where(WorkOrder.service_request_id == service_request_id)
        if assigned_technician_id is not None:
            stmt = stmt.where(
                WorkOrder.assigned_technician_id == assigned_technician_id
            )
        if status and status.strip():
            stmt = stmt.where(WorkOrder.status == status.strip())
        if search and search.strip():
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                WorkOrder.title.ilike(term) | WorkOrder.description.ilike(term)
            )

        return list(
            db.scalars(
                stmt.order_by(WorkOrder.created_at.desc())
            ).all()
        )

    def create(
        self, db: Session, company_id: UUID | None, data: dict
    ) -> WorkOrder:
        company_id = require_company_id(company_id)
        display_id = data.pop("display_id", None)
        if display_id is None:
            max_id = db.scalar(select(func.max(WorkOrder.display_id)).where(WorkOrder.company_id == company_id)) or 0
            display_id = int(max_id) + 1
        work_order = WorkOrder(company_id=company_id, display_id=display_id, **data)
        db.add(work_order)
        db.flush()
        return work_order

    def update(
        self,
        db: Session,
        company_id: UUID | None,
        work_order_id: UUID,
        data: dict,
    ) -> WorkOrder | None:
        work_order = self.get(db, company_id, work_order_id)
        if work_order is None:
            return None

        for key, value in data.items():
            setattr(work_order, key, value)
        db.flush()
        return work_order

    def soft_delete(
        self, db: Session, company_id: UUID | None, work_order_id: UUID
    ) -> WorkOrder | None:
        company_id = self._require_company_scope(company_id)
        work_order = db.scalar(
            select(WorkOrder).where(
                WorkOrder.id == work_order_id,
                WorkOrder.company_id == company_id,
            )
        )
        if work_order is None:
            return None

        work_order.status = "Deleted"
        db.flush()
        return work_order
