# Task 32 — Inventory Data Migration

## Scope

Creates the PostgreSQL inventory-item data foundation and a deterministic mapping
from the legacy Google Sheets `Inventory` shape.

Legacy fields preserved:

- `item_name`
- `quantity`
- `min_limit`
- `cost_price`
- `ideal_stock`

## Safety

- Inventory quantity cannot become negative.
- Tenant ownership is represented by `company_id`.
- Item names are unique within a company.
- No live Google Sheets import is performed in Task 32.
- Existing Google Sheets persistence remains untouched.

The actual migration of required existing production data is scheduled for Task 62.

## Deferred work

- Task 33: Inventory Repository / Service
- Task 34: Inventory Transactions
- Task 35: Technician Stock
- Task 36: Inventory Business Rules
