"""Tenant-scoped persistence operations for technician stock."""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.core.tenant_isolation import require_company_id
from backend.models.technician_stock import TechnicianStock
from backend.repositories.base import TenantScopedRepository

class TechnicianStockRepository(TenantScopedRepository):
    def get(self, db: Session, company_id: UUID | None, stock_id: UUID):
        company_id = self._require_company_scope(company_id)
        return db.scalar(select(TechnicianStock).where(TechnicianStock.id == stock_id, TechnicianStock.company_id == company_id))
    def get_for_technician_item(self, db: Session, company_id: UUID | None, technician_id: UUID, inventory_item_id: UUID):
        company_id = self._require_company_scope(company_id)
        return db.scalar(select(TechnicianStock).where(TechnicianStock.company_id == company_id, TechnicianStock.technician_id == technician_id, TechnicianStock.inventory_item_id == inventory_item_id))
    def list(self, db: Session, company_id: UUID | None, technician_id: UUID | None = None, inventory_item_id: UUID | None = None):
        company_id = require_company_id(company_id)
        stmt = select(TechnicianStock).where(TechnicianStock.company_id == company_id)
        if technician_id is not None: stmt = stmt.where(TechnicianStock.technician_id == technician_id)
        if inventory_item_id is not None: stmt = stmt.where(TechnicianStock.inventory_item_id == inventory_item_id)
        return list(db.scalars(stmt.order_by(TechnicianStock.technician_id, TechnicianStock.inventory_item_id)).all())
    def create(self, db: Session, company_id: UUID | None, data: dict):
        company_id = require_company_id(company_id); stock = TechnicianStock(company_id=company_id, **data); db.add(stock); db.flush(); return stock
    def update_quantity(self, db: Session, company_id: UUID | None, stock_id: UUID, quantity: int):
        stock = self.get(db, company_id, stock_id)
        if stock is None: return None
        stock.quantity = quantity; db.flush(); return stock
