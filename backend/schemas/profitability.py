"""Pydantic schemas for derived profitability reporting."""
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class ProfitabilitySummary(BaseModel):
    period_start: date | None = None
    period_end: date | None = None
    invoiced_revenue: Decimal = Decimal("0.00")
    collected_revenue: Decimal = Decimal("0.00")
    expenses: Decimal = Decimal("0.00")
    net_profit: Decimal = Decimal("0.00")
    cash_net_profit: Decimal = Decimal("0.00")
    profit_margin_percent: Decimal = Decimal("0.00")
    expense_count: int = 0
    invoice_count: int = 0
    model_config = ConfigDict(from_attributes=True)

class ExpenseBreakdown(BaseModel):
    category: str
    amount: Decimal
