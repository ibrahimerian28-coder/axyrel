from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from backend.core.tenant_isolation import require_company_id
from backend.models.customer import Customer
from backend.repositories.base import TenantScopedRepository


class CustomerRepository(TenantScopedRepository):
    def get(self, db: Session, company_id: UUID | None, customer_id: UUID):
        company_id = self._require_company_scope(company_id)
        return db.scalar(select(Customer).where(Customer.id == customer_id, Customer.company_id == company_id, Customer.status != "Deleted"))

    def list(self, db: Session, company_id: UUID | None, search: str | None = None):
        company_id = require_company_id(company_id)
        stmt = select(Customer).where(Customer.company_id == company_id, Customer.status != "Deleted")
        if search and search.strip():
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                Customer.name.ilike(term) | Customer.phone.ilike(term) |
                Customer.phone_1.ilike(term) | Customer.phone_2.ilike(term) |
                Customer.phone_3.ilike(term) | Customer.phone_4.ilike(term) |
                Customer.area.ilike(term)
            )
        return db.scalars(stmt.order_by(Customer.area, Customer.display_id, Customer.name)).all()

    def create(self, db: Session, company_id: UUID | None, data: dict):
        company_id = require_company_id(company_id)
        display_id = data.pop("display_id", None)
        if display_id is None:
            max_id = db.scalar(select(func.max(Customer.display_id)).where(Customer.company_id == company_id)) or 1000
            display_id = int(max_id) + 1
        customer = Customer(company_id=company_id, display_id=display_id, **data)
        db.add(customer); db.flush()
        return customer

    def update(self, db: Session, company_id: UUID | None, customer_id: UUID, data: dict):
        customer = self.get(db, company_id, customer_id)
        if customer is None: return None
        for key, value in data.items(): setattr(customer, key, value)
        db.flush(); return customer

    def soft_delete(self, db: Session, company_id: UUID | None, customer_id: UUID):
        company_id = self._require_company_scope(company_id)
        customer = db.scalar(select(Customer).where(Customer.id == customer_id, Customer.company_id == company_id))
        if customer is None: return None
        customer.status = "Deleted"; db.flush(); return customer
