"""Business service for tenant-scoped billing and invoices."""
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from backend.repositories.invoice import InvoiceRepository
from backend.repositories.work_order import WorkOrderRepository


class WorkOrderReferenceError(ValueError):
    """An invoice link does not resolve to a visible tenant Work Order."""

class InvoiceService:
    def __init__(self, repository: InvoiceRepository | None = None,
                 work_order_repository: WorkOrderRepository | None = None) -> None:
        self.repository = repository or InvoiceRepository()
        self.work_order_repository = work_order_repository or WorkOrderRepository()

    def _validate_work_order(self, db: Session, company_id: UUID | None, work_order_id: UUID | None):
        if work_order_id is not None and self.work_order_repository.get(db, company_id, work_order_id) is None:
            raise WorkOrderReferenceError("Work order not found.")
    def list_invoices(self, db: Session, company_id: UUID | None, **filters):
        return self.repository.list(db, company_id, **filters)
    def get_invoice(self, db: Session, company_id: UUID | None, invoice_id: UUID):
        return self.repository.get(db, company_id, invoice_id)
    def create_invoice(self, db: Session, company_id: UUID | None, data: dict):
        self._validate_work_order(db, company_id, data.get("work_order_id"))
        if "total" not in data:
            subtotal = Decimal(str(data.get("subtotal", "0")))
            discount = Decimal(str(data.get("discount", "0")))
            tax = Decimal(str(data.get("tax", "0")))
            data = {**data, "total": max(Decimal("0"), subtotal - discount + tax)}
        return self.repository.create(db, company_id, data)
    def update_invoice(self, db: Session, company_id: UUID | None, invoice_id: UUID, data: dict):
        record = self.repository.get(db, company_id, invoice_id)
        if record is None:
            return None
        if "work_order_id" in data:
            self._validate_work_order(db, company_id, data["work_order_id"])
        return self.repository.update(db, company_id, invoice_id, data)
    def delete_invoice(self, db: Session, company_id: UUID | None, invoice_id: UUID):
        return self.repository.soft_delete(db, company_id, invoice_id)
