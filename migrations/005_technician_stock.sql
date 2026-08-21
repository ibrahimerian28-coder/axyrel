CREATE TABLE IF NOT EXISTS technician_stock (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    technician_id UUID NOT NULL,
    inventory_item_id UUID NOT NULL REFERENCES inventory_items(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    CONSTRAINT uq_technician_stock_company_technician_item UNIQUE (company_id, technician_id, inventory_item_id)
);
CREATE INDEX IF NOT EXISTS ix_technician_stock_company_id ON technician_stock(company_id);
CREATE INDEX IF NOT EXISTS ix_technician_stock_technician_id ON technician_stock(technician_id);
CREATE INDEX IF NOT EXISTS ix_technician_stock_inventory_item_id ON technician_stock(inventory_item_id);
