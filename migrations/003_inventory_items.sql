-- Task 32 — Inventory Data Migration
-- Production data import from the legacy Google Sheets Inventory source
-- is intentionally deferred to Task 62.

CREATE TABLE IF NOT EXISTS inventory_items (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    min_limit INTEGER NOT NULL DEFAULT 0 CHECK (min_limit >= 0),
    cost_price NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (cost_price >= 0),
    ideal_stock INTEGER NOT NULL DEFAULT 0 CHECK (ideal_stock >= 0),
    status VARCHAR(30) NOT NULL DEFAULT 'Active'
);

CREATE INDEX IF NOT EXISTS ix_inventory_items_company_id
    ON inventory_items(company_id);

CREATE INDEX IF NOT EXISTS ix_inventory_items_item_name
    ON inventory_items(item_name);

CREATE UNIQUE INDEX IF NOT EXISTS uq_inventory_items_company_item_name
    ON inventory_items(company_id, item_name);
