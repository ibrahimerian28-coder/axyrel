-- Axyrel core service-domain schema
-- Restores the base tables required by the Task 44 API and by migrations 006-010.
-- This migration is idempotent and safe to run before 011_identity.sql.

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    display_id INTEGER NULL,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(50) NULL,
    phone_1 VARCHAR(50) NULL,
    phone_2 VARCHAR(50) NULL,
    phone_3 VARCHAR(50) NULL,
    phone_4 VARCHAR(50) NULL,
    address VARCHAR(500) NULL,
    area VARCHAR(150) NULL,
    location_url VARCHAR(1000) NULL,
    install_date DATE NULL,
    cycle VARCHAR(50) NULL,
    device_type VARCHAR(150) NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Active'
);

CREATE INDEX IF NOT EXISTS ix_customers_company_id ON customers(company_id);
CREATE INDEX IF NOT EXISTS ix_customers_area ON customers(area);
CREATE INDEX IF NOT EXISTS ix_customers_name ON customers(name);

CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    display_id INTEGER NULL,
    asset_type VARCHAR(150) NOT NULL,
    serial_number VARCHAR(150) NULL,
    model VARCHAR(150) NULL,
    manufacturer VARCHAR(150) NULL,
    installation_date DATE NULL,
    warranty_start DATE NULL,
    warranty_end DATE NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Active',
    notes VARCHAR(1000) NULL
);

CREATE INDEX IF NOT EXISTS ix_assets_company_id ON assets(company_id);
CREATE INDEX IF NOT EXISTS ix_assets_customer_id ON assets(customer_id);
CREATE INDEX IF NOT EXISTS ix_assets_serial_number ON assets(serial_number);

CREATE TABLE IF NOT EXISTS service_requests (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    asset_id UUID NULL REFERENCES assets(id),
    display_id INTEGER NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NULL,
    priority VARCHAR(30) NOT NULL DEFAULT 'Normal',
    status VARCHAR(30) NOT NULL DEFAULT 'Open',
    source VARCHAR(50) NULL,
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT NULL
);

CREATE INDEX IF NOT EXISTS ix_service_requests_company_id ON service_requests(company_id);
CREATE INDEX IF NOT EXISTS ix_service_requests_customer_id ON service_requests(customer_id);
CREATE INDEX IF NOT EXISTS ix_service_requests_asset_id ON service_requests(asset_id);
CREATE INDEX IF NOT EXISTS ix_service_requests_status ON service_requests(status);
CREATE INDEX IF NOT EXISTS ix_service_requests_requested_at ON service_requests(requested_at);

CREATE TABLE IF NOT EXISTS work_orders (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    asset_id UUID NULL REFERENCES assets(id),
    service_request_id UUID NULL REFERENCES service_requests(id),
    display_id INTEGER NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NULL,
    priority VARCHAR(30) NOT NULL DEFAULT 'Normal',
    status VARCHAR(30) NOT NULL DEFAULT 'Open',
    assigned_technician_id UUID NULL,
    scheduled_start TIMESTAMP NULL,
    scheduled_end TIMESTAMP NULL,
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_work_orders_company_id ON work_orders(company_id);
CREATE INDEX IF NOT EXISTS ix_work_orders_customer_id ON work_orders(customer_id);
CREATE INDEX IF NOT EXISTS ix_work_orders_asset_id ON work_orders(asset_id);
CREATE INDEX IF NOT EXISTS ix_work_orders_service_request_id ON work_orders(service_request_id);
CREATE INDEX IF NOT EXISTS ix_work_orders_assigned_technician_id ON work_orders(assigned_technician_id);
CREATE INDEX IF NOT EXISTS ix_work_orders_status ON work_orders(status);

CREATE TABLE IF NOT EXISTS schedules (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    work_order_id UUID NOT NULL REFERENCES work_orders(id),
    technician_id UUID NULL,
    start_at TIMESTAMP NOT NULL,
    end_at TIMESTAMP NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Scheduled',
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_schedules_company_id ON schedules(company_id);
CREATE INDEX IF NOT EXISTS ix_schedules_work_order_id ON schedules(work_order_id);
CREATE INDEX IF NOT EXISTS ix_schedules_technician_id ON schedules(technician_id);
CREATE INDEX IF NOT EXISTS ix_schedules_start_at ON schedules(start_at);
CREATE INDEX IF NOT EXISTS ix_schedules_status ON schedules(status);

CREATE TABLE IF NOT EXISTS service_visits (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    work_order_id UUID NOT NULL REFERENCES work_orders(id),
    schedule_id UUID NULL REFERENCES schedules(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    asset_id UUID NULL REFERENCES assets(id),
    technician_id UUID NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Planned',
    actual_start_at TIMESTAMP NULL,
    actual_end_at TIMESTAMP NULL,
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_service_visits_company_id ON service_visits(company_id);
CREATE INDEX IF NOT EXISTS ix_service_visits_work_order_id ON service_visits(work_order_id);
CREATE INDEX IF NOT EXISTS ix_service_visits_schedule_id ON service_visits(schedule_id);
CREATE INDEX IF NOT EXISTS ix_service_visits_customer_id ON service_visits(customer_id);
CREATE INDEX IF NOT EXISTS ix_service_visits_asset_id ON service_visits(asset_id);
CREATE INDEX IF NOT EXISTS ix_service_visits_technician_id ON service_visits(technician_id);
CREATE INDEX IF NOT EXISTS ix_service_visits_status ON service_visits(status);

CREATE TABLE IF NOT EXISTS service_history (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    asset_id UUID NULL REFERENCES assets(id),
    service_visit_id UUID NULL REFERENCES service_visits(id),
    work_order_id UUID NULL REFERENCES work_orders(id),
    service_type VARCHAR(100) NOT NULL,
    service_date TIMESTAMP NOT NULL,
    summary TEXT NOT NULL,
    technician_id UUID NULL,
    notes TEXT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_service_history_company_id ON service_history(company_id);
CREATE INDEX IF NOT EXISTS ix_service_history_customer_id ON service_history(customer_id);
CREATE INDEX IF NOT EXISTS ix_service_history_asset_id ON service_history(asset_id);
CREATE INDEX IF NOT EXISTS ix_service_history_service_visit_id ON service_history(service_visit_id);
CREATE INDEX IF NOT EXISTS ix_service_history_work_order_id ON service_history(work_order_id);
CREATE INDEX IF NOT EXISTS ix_service_history_technician_id ON service_history(technician_id);
CREATE INDEX IF NOT EXISTS ix_service_history_service_date ON service_history(service_date);
CREATE INDEX IF NOT EXISTS ix_service_history_status ON service_history(status);
