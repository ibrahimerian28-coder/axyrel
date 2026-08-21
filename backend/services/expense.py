"""Business service for tenant-scoped expense records."""
from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.expense import ExpenseRepository


class ExpenseService:
    def __init__(self, repository: ExpenseRepository | None = None) -> None:
        self.repository = repository or ExpenseRepository()

    def list_expenses(self, db: Session, company_id: UUID | None, **filters):
        return self.repository.list(db, company_id, **filters)

    def get_expense(self, db: Session, company_id: UUID | None, expense_id: UUID):
        return self.repository.get(db, company_id, expense_id)

    def create_expense(self, db: Session, company_id: UUID | None, data: dict):
        return self.repository.create(db, company_id, data)

    def update_expense(self, db: Session, company_id: UUID | None, expense_id: UUID, data: dict):
        return self.repository.update(db, company_id, expense_id, data)

    def delete_expense(self, db: Session, company_id: UUID | None, expense_id: UUID):
        return self.repository.soft_delete(db, company_id, expense_id)
