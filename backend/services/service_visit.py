"""Business service for the Axyrel Service Visit domain."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from backend.core.event_time import normalize_event_time
from backend.repositories.schedule import ScheduleRepository
from backend.repositories.service_visit import ServiceVisitRepository
from backend.repositories.work_order import WorkOrderRepository
from backend.services.inventory_rules import InventoryBusinessRules
from backend.services.status_lifecycle import (
    derive_work_order_status,
    ensure_service_visit_transition,
    ensure_work_order_transition,
)

SERVICE_VISIT_INSTALL_REF = "SERVICE_VISIT_INSTALL"
SERVICE_VISIT_REVERSAL_REF = "SERVICE_VISIT_REVERSAL"


class ServiceVisitService:
    """Application service for tenant-scoped service visits."""

    def __init__(
        self,
        repository: ServiceVisitRepository | None = None,
        work_order_repository: WorkOrderRepository | None = None,
        inventory_rules: InventoryBusinessRules | None = None,
        schedule_repository: ScheduleRepository | None = None,
    ) -> None:
        self.repository = repository or ServiceVisitRepository()
        self.work_order_repository = work_order_repository or WorkOrderRepository()
        self.inventory_rules = inventory_rules or InventoryBusinessRules()
        self.schedule_repository = schedule_repository or ScheduleRepository()

    def _validate_schedule(self, db: Session, company_id: UUID | None, schedule_id):
        if schedule_id is not None and self.schedule_repository.get(db, company_id, schedule_id) is None:
            raise ValueError("Schedule not found.")

    @staticmethod
    def _normalized_data(data: dict) -> dict:
        normalized = dict(data)
        for field in ("actual_start_at", "actual_end_at"):
            if normalized.get(field) is not None:
                normalized[field] = normalize_event_time(normalized[field])
        return normalized

    @staticmethod
    def _validate_range(start: datetime | None, end: datetime | None) -> None:
        if start is not None and end is not None:
            if normalize_event_time(end) < normalize_event_time(start):
                raise ValueError("actual_end_at must be later than or equal to actual_start_at")

    def list_visits(self, db: Session, company_id: UUID | None, **filters):
        for field in ("start_from", "start_to"):
            if filters.get(field) is not None:
                filters[field] = normalize_event_time(filters[field])
        return self.repository.list(db, company_id, **filters)

    def get_visit(self, db: Session, company_id: UUID | None, visit_id: UUID):
        return self.repository.get(db, company_id, visit_id)

    def create_visit(self, db: Session, company_id: UUID | None, data: dict):
        data = self._normalized_data(data)
        self._validate_schedule(db, company_id, data.get("schedule_id"))
        self._validate_range(data.get("actual_start_at"), data.get("actual_end_at"))
        work_order = self._required_work_order(db, company_id, data.get("work_order_id"))
        if work_order.status == "Cancelled":
            raise ValueError("Cannot create a service visit for a cancelled work order")

        status = data.get("status", "Planned")
        ensure_service_visit_transition("Planned", status)
        if not data.get("technician_id") and work_order.assigned_technician_id:
            data = {**data, "technician_id": work_order.assigned_technician_id}
        if not data.get("customer_id"):
            data = {**data, "customer_id": work_order.customer_id}

        visit = self.repository.create(db, company_id, data)
        self._sync_work_order_from_visits(db, company_id, work_order.id)
        return visit

    def update_visit(self, db: Session, company_id: UUID | None, visit_id: UUID, data: dict):
        visit = self.repository.get(db, company_id, visit_id)
        if visit is None:
            return None

        data = self._normalized_data(data)
        if "schedule_id" in data:
            self._validate_schedule(db, company_id, data["schedule_id"])
        self._validate_range(data.get("actual_start_at", visit.actual_start_at),
                             data.get("actual_end_at", visit.actual_end_at))
        work_order = self._required_work_order(db, company_id, visit.work_order_id)
        target_status = data.get("status")
        previous_status = visit.status
        if target_status is not None:
            target_status = ensure_service_visit_transition(visit.status, target_status)
            data = {**data, "status": target_status}
            if work_order.status == "Cancelled" and target_status != "Cancelled":
                raise ValueError("Cannot reopen a service visit on a cancelled work order")

        if "work_order_id" in data and data["work_order_id"] != visit.work_order_id:
            destination = self._required_work_order(db, company_id, data["work_order_id"])
            if destination.status == "Cancelled" and (target_status or previous_status) != "Cancelled":
                raise ValueError("Cannot reassign a non-cancelled service visit to a cancelled work order")

        updated = self.repository.update(db, company_id, visit_id, data)
        if updated is None:
            return None

        if target_status == "Cancelled" and previous_status != "Cancelled":
            self._restore_installed_parts(db, company_id, updated)

        self._sync_work_order_from_visits(db, company_id, updated.work_order_id)
        return updated

    def delete_visit(self, db: Session, company_id: UUID | None, visit_id: UUID):
        visit = self.repository.get(db, company_id, visit_id)
        if visit is None:
            return None
        work_order_id = visit.work_order_id
        if visit.status != "Cancelled":
            self._restore_installed_parts(db, company_id, visit)
        deleted = self.repository.soft_delete(db, company_id, visit_id)
        self._sync_work_order_from_visits(db, company_id, work_order_id)
        return deleted

    def install_part(
        self,
        db: Session,
        company_id: UUID | None,
        visit_id: UUID,
        inventory_item_id: UUID,
        quantity: int,
    ):
        visit = self.repository.get(db, company_id, visit_id)
        if visit is None:
            return None
        if visit.status in {"Cancelled", "Deleted"}:
            raise ValueError("Cannot install parts on a cancelled service visit")

        work_order = self._required_work_order(db, company_id, visit.work_order_id)
        technician_id = visit.technician_id or work_order.assigned_technician_id
        if technician_id is None:
            raise ValueError("Service visit has no technician to deduct inventory from")

        self.inventory_rules.consume_technician_stock(
            db,
            company_id,
            technician_id,
            inventory_item_id,
            quantity,
            reference_type=SERVICE_VISIT_INSTALL_REF,
            reference_id=str(visit.id),
            notes=f"Installed on service visit {visit.id}; technician_id={technician_id}",
        )
        return visit

    def _restore_installed_parts(self, db: Session, company_id: UUID | None, visit) -> None:
        installs = self.inventory_rules.transaction_repository.list_by_reference(
            db, company_id, SERVICE_VISIT_INSTALL_REF, str(visit.id)
        )
        reversals = self.inventory_rules.transaction_repository.list_by_reference(
            db, company_id, SERVICE_VISIT_REVERSAL_REF, str(visit.id)
        )
        def stock_owner_key(row):
            _, marker, owner = (row.notes or "").rpartition("; technician_id=")
            if not marker:
                raise ValueError("Cannot reverse service visit inventory: original technician is not recorded")
            return UUID(owner), row.inventory_item_id

        installed_qty: dict[tuple[UUID, UUID], int] = {}
        reversed_qty: dict[tuple[UUID, UUID], int] = {}
        for row in installs:
            key = stock_owner_key(row)
            installed_qty[key] = installed_qty.get(key, 0) + int(row.quantity)
        for row in reversals:
            key = stock_owner_key(row)
            reversed_qty[key] = reversed_qty.get(key, 0) + int(row.quantity)

        for (technician_id, item_id), quantity in installed_qty.items():
            remaining = quantity - reversed_qty.get((technician_id, item_id), 0)
            if remaining <= 0:
                continue
            self.inventory_rules.restore_technician_stock(
                db,
                company_id,
                technician_id,
                item_id,
                remaining,
                reference_type=SERVICE_VISIT_REVERSAL_REF,
                reference_id=str(visit.id),
                notes=f"Reversed from cancelled service visit {visit.id}; technician_id={technician_id}",
            )

    def _sync_work_order_from_visits(
        self, db: Session, company_id: UUID | None, work_order_id: UUID
    ) -> None:
        work_order = self.work_order_repository.get(db, company_id, work_order_id)
        if work_order is None:
            return
        visits = self.repository.list(db, company_id, work_order_id=work_order_id)
        derived = derive_work_order_status([visit.status for visit in visits])
        if derived is None or derived == work_order.status:
            return
        if work_order.status == "Cancelled" and derived != "Cancelled":
            return
        ensure_work_order_transition(work_order.status, derived)
        self.work_order_repository.update(
            db, company_id, work_order_id, {"status": derived}
        )

    def _required_work_order(self, db: Session, company_id: UUID | None, work_order_id):
        if work_order_id is None:
            raise ValueError("work_order_id is required")
        work_order = self.work_order_repository.get(db, company_id, work_order_id)
        if work_order is None:
            raise ValueError("Work order not found")
        return work_order
