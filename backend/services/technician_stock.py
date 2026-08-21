"""Application service for technician-assigned stock."""
from uuid import UUID
from sqlalchemy.orm import Session
from backend.repositories.technician_stock import TechnicianStockRepository

class TechnicianStockService:
    def __init__(self, repository: TechnicianStockRepository | None = None) -> None: self.repository = repository or TechnicianStockRepository()
    def get_stock(self, db: Session, company_id: UUID | None, stock_id: UUID): return self.repository.get(db, company_id, stock_id)
    def get_for_technician_item(self, db: Session, company_id: UUID | None, technician_id: UUID, inventory_item_id: UUID): return self.repository.get_for_technician_item(db, company_id, technician_id, inventory_item_id)
    def list_stock(self, db: Session, company_id: UUID | None, technician_id: UUID | None = None, inventory_item_id: UUID | None = None): return self.repository.list(db, company_id, technician_id, inventory_item_id)
    def create_stock(self, db: Session, company_id: UUID | None, data: dict):
        if int(data.get("quantity", 0)) < 0: raise ValueError("quantity must be non-negative")
        return self.repository.create(db, company_id, data)
    def set_quantity(self, db: Session, company_id: UUID | None, stock_id: UUID, quantity: int):
        if quantity < 0: raise ValueError("quantity must be non-negative")
        return self.repository.update_quantity(db, company_id, stock_id, quantity)
