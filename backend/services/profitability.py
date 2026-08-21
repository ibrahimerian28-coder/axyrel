"""Business service for derived profitability calculations."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID
from sqlalchemy.orm import Session
from backend.repositories.profitability import ProfitabilityRepository
from backend.schemas.profitability import ExpenseBreakdown, ProfitabilitySummary

class ProfitabilityService:
    def __init__(self, repository: ProfitabilityRepository | None = None) -> None:
        self.repository = repository or ProfitabilityRepository()

    def summary(self, db: Session, company_id: UUID | None, start_date: date | None = None, end_date: date | None = None) -> ProfitabilitySummary:
        revenue, collected, invoice_count = self.repository.revenue_totals(db, company_id, start_date, end_date)
        expenses, expense_count = self.repository.expense_totals(db, company_id, start_date, end_date)
        revenue = Decimal(revenue or 0)
        collected = Decimal(collected or 0)
        expenses = Decimal(expenses or 0)
        net_profit = revenue - expenses
        cash_net_profit = collected - expenses
        margin = (net_profit / revenue * Decimal("100")) if revenue else Decimal("0")
        return ProfitabilitySummary(
            period_start=start_date, period_end=end_date, invoiced_revenue=revenue,
            collected_revenue=collected, expenses=expenses, net_profit=net_profit,
            cash_net_profit=cash_net_profit,
            profit_margin_percent=margin.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            expense_count=expense_count, invoice_count=invoice_count,
        )

    def expense_breakdown(self, db: Session, company_id: UUID | None, start_date: date | None = None, end_date: date | None = None) -> list[ExpenseBreakdown]:
        return [ExpenseBreakdown(category=row[0], amount=Decimal(row[1] or 0)) for row in self.repository.expense_breakdown(db, company_id, start_date, end_date)]
