"""Tenant-scoped persistence operations for invoices."""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.core.tenant_isolation import require_company_id
from backend.models.invoice import Invoice
from backend.repositories.base import TenantScopedRepository

class InvoiceRepository(TenantScopedRepository):
    def get(self, db: Session, company_id: UUID | None, invoice_id: UUID) -> Invoice | None:
        company_id = self._require_company_scope(company_id)
        return db.scalar(select(Invoice).where(
            Invoice.id == invoice_id, Invoice.company_id == company_id, Invoice.status != "Deleted"
        ))
    def list(self, db: Session, company_id: UUID | None, customer_id: UUID | None = None,
             work_order_id: UUID | None = None, status: str | None = None) -> list[Invoice]:
        company_id = require_company_id(company_id)
        stmt = select(Invoice).where(Invoice.company_id == company_id, Invoice.status != "Deleted")
        if customer_id is not None: stmt = stmt.where(Invoice.customer_id == customer_id)
        if work_order_id is not None: stmt = stmt.where(Invoice.work_order_id == work_order_id)
        if status is not None: stmt = stmt.where(Invoice.status == status)
        return list(db.scalars(stmt.order_by(Invoice.issue_date.desc(), Invoice.created_at.desc())).all())
    def create(self, db: Session, company_id: UUID | None, data: dict) -> Invoice:
        company_id = require_company_id(company_id)
        record = Invoice(company_id=company_id, **data)
        db.add(record); db.flush(); return record
    def update(self, db: Session, company_id: UUID | None, invoice_id: UUID, data: dict) -> Invoice | None:
        record = self.get(db, company_id, invoice_id)
        if record is None: return None
        for key, value in data.items(): setattr(record, key, value)
        db.flush(); return record
    def soft_delete(self, db: Session, company_id: UUID | None, invoice_id: UUID) -> Invoice | None:
        record = self.get(db, company_id, invoice_id)
        if record is None: return None
        record.status = "Deleted"; db.flush(); return record
