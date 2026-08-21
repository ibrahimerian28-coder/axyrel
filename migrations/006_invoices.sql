-- Task 37 — Billing / Invoicing Migration
-- Production invoice data migration is intentionally deferred to Task 62.

CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    work_order_id UUID NULL REFERENCES work_orders(id),
    invoice_number VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Draft',
    issue_date DATE NOT NULL,
    due_date DATE NULL,
    subtotal NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    discount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (discount >= 0),
    tax NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (tax >= 0),
    total NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (total >= 0),
    paid_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (paid_amount >= 0),
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_invoices_company_number UNIQUE (company_id, invoice_number)
);

CREATE INDEX IF NOT EXISTS ix_invoices_company_id ON invoices(company_id);
CREATE INDEX IF NOT EXISTS ix_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS ix_invoices_work_order_id ON invoices(work_order_id);
CREATE INDEX IF NOT EXISTS ix_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS ix_invoices_issue_date ON invoices(issue_date);
