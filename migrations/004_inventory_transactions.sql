-- Task 34 — Inventory Transactions
-- Inventory movement ledger. Stock business rules are finalized in Task 36.

CREATE TABLE IF NOT EXISTS inventory_transactions (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    inventory_item_id UUID NOT NULL REFERENCES inventory_items(id) ON DELETE RESTRICT,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('IN', 'OUT', 'ADJUSTMENT')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    reference_type VARCHAR(50),
    reference_id VARCHAR(100),
    notes VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_inventory_transactions_company_id
    ON inventory_transactions(company_id);
CREATE INDEX IF NOT EXISTS ix_inventory_transactions_item_id
    ON inventory_transactions(inventory_item_id);
CREATE INDEX IF NOT EXISTS ix_inventory_transactions_type
    ON inventory_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS ix_inventory_transactions_created_at
    ON inventory_transactions(created_at);
