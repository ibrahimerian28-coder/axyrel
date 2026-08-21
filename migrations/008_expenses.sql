-- Task 39: Expenses Migration
-- Tenant-scoped expense foundation for Axyrel.

CREATE TABLE IF NOT EXISTS expenses (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    category VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    expense_date DATE NOT NULL,
    payment_method VARCHAR(50),
    vendor VARCHAR(200),
    reference VARCHAR(100),
    notes TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT expenses_amount_non_negative CHECK (amount >= 0)
);

CREATE INDEX IF NOT EXISTS ix_expenses_company_id ON expenses(company_id);
CREATE INDEX IF NOT EXISTS ix_expenses_expense_date ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS ix_expenses_status ON expenses(status);
CREATE INDEX IF NOT EXISTS ix_expenses_company_category ON expenses(company_id, category);
