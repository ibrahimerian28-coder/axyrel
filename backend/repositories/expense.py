"""Tenant-scoped persistence operations for expenses."""
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.tenant_isolation import require_company_id
from backend.models.expense import Expense
from backend.repositories.base import TenantScopedRepository


class ExpenseRepository(TenantScopedRepository):
    def get(self, db: Session, company_id: UUID | None, expense_id: UUID) -> Expense | None:
        company_id = self._require_company_scope(company_id)
        return db.scalar(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.company_id == company_id,
                Expense.status != "Deleted",
            )
        )

    def list(
        self,
        db: Session,
        company_id: UUID | None,
        category: str | None = None,
        status: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Expense]:
        company_id = require_company_id(company_id)
        stmt = select(Expense).where(
            Expense.company_id == company_id,
            Expense.status != "Deleted",
        )
        if category is not None:
            stmt = stmt.where(Expense.category == category)
        if status is not None:
            stmt = stmt.where(Expense.status == status)
        if start_date is not None:
            stmt = stmt.where(Expense.expense_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(Expense.expense_date <= end_date)
        return list(db.scalars(stmt.order_by(Expense.expense_date.desc(), Expense.created_at.desc())).all())

    def create(self, db: Session, company_id: UUID | None, data: dict) -> Expense:
        company_id = require_company_id(company_id)
        record = Expense(company_id=company_id, **data)
        db.add(record)
        db.flush()
        return record

    def update(
        self, db: Session, company_id: UUID | None, expense_id: UUID, data: dict
    ) -> Expense | None:
        record = self.get(db, company_id, expense_id)
        if record is None:
            return None
        for key, value in data.items():
            setattr(record, key, value)
        db.flush()
        return record

    def soft_delete(self, db: Session, company_id: UUID | None, expense_id: UUID) -> Expense | None:
        record = self.get(db, company_id, expense_id)
        if record is None:
            return None
        record.status = "Deleted"
        db.flush()
        return record
