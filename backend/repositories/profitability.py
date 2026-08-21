"""Tenant-scoped aggregate queries for profitability reporting."""
from datetime import date
from decimal import Decimal
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from backend.core.tenant_isolation import require_company_id
from backend.models.expense import Expense
from backend.models.invoice import Invoice
from backend.repositories.base import TenantScopedRepository

REVENUE_STATUSES = ("Sent", "Paid", "Overdue")

class ProfitabilityRepository(TenantScopedRepository):
    def _scope(self, company_id: UUID | None) -> UUID:
        return require_company_id(company_id)

    def revenue_totals(self, db: Session, company_id: UUID | None, start_date: date | None = None, end_date: date | None = None):
        company_id = self._scope(company_id)
        stmt = select(
            func.coalesce(func.sum(Invoice.total), 0),
            func.coalesce(func.sum(Invoice.paid_amount), 0),
            func.count(Invoice.id),
        ).where(Invoice.company_id == company_id, Invoice.status.in_(REVENUE_STATUSES))
        if start_date is not None: stmt = stmt.where(Invoice.issue_date >= start_date)
        if end_date is not None: stmt = stmt.where(Invoice.issue_date <= end_date)
        return db.execute(stmt).one()

    def expense_totals(self, db: Session, company_id: UUID | None, start_date: date | None = None, end_date: date | None = None):
        company_id = self._scope(company_id)
        stmt = select(
            func.coalesce(func.sum(Expense.amount), 0),
            func.count(Expense.id),
        ).where(Expense.company_id == company_id, Expense.status == "Active")
        if start_date is not None: stmt = stmt.where(Expense.expense_date >= start_date)
        if end_date is not None: stmt = stmt.where(Expense.expense_date <= end_date)
        return db.execute(stmt).one()

    def expense_breakdown(self, db: Session, company_id: UUID | None, start_date: date | None = None, end_date: date | None = None):
        company_id = self._scope(company_id)
        stmt = select(Expense.category, func.sum(Expense.amount).label("amount")).where(
            Expense.company_id == company_id, Expense.status == "Active"
        ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc())
        if start_date is not None: stmt = stmt.where(Expense.expense_date >= start_date)
        if end_date is not None: stmt = stmt.where(Expense.expense_date <= end_date)
        return list(db.execute(stmt).all())
