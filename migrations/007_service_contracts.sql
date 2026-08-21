-- Task 38 — Service Contract Migration
-- Production data migration is intentionally deferred to Task 62.

CREATE TABLE IF NOT EXISTS service_contracts (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    contract_number VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Draft',
    start_date DATE NOT NULL,
    end_date DATE NULL,
    contract_value NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (contract_value >= 0),
    billing_frequency VARCHAR(30) NOT NULL DEFAULT 'Monthly',
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_service_contracts_company_number
        UNIQUE (company_id, contract_number),
    CONSTRAINT ck_service_contracts_date_range
        CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX IF NOT EXISTS ix_service_contracts_company_id
    ON service_contracts(company_id);
CREATE INDEX IF NOT EXISTS ix_service_contracts_customer_id
    ON service_contracts(customer_id);
CREATE INDEX IF NOT EXISTS ix_service_contracts_status
    ON service_contracts(status);
CREATE INDEX IF NOT EXISTS ix_service_contracts_billing_frequency
    ON service_contracts(billing_frequency);
CREATE INDEX IF NOT EXISTS ix_service_contracts_start_date
    ON service_contracts(start_date);
