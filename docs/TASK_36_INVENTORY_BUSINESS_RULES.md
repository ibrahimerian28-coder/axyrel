# Task 36 — Inventory Business Rules

## Scope

Centralizes inventory business rules above the repositories so API/UI layers do
not duplicate stock calculations or movement logic.

## Rules preserved from the legacy Inventory module

- `quantity <= min_limit` → `CRITICAL`.
- Otherwise, when `ideal_stock > 0` and `quantity < 50%` of ideal stock → `LOW`.
- Otherwise → `GOOD`.
- Current inventory value = `quantity * cost_price`.
- Warehouse stock may never become negative.
- Technician stock may never become negative.
- Stock movements use `IN`, `OUT`, and `ADJUSTMENT` transaction types.
- Warehouse-to-technician transfer decreases warehouse quantity and increases
  the technician's assigned quantity in the same database session.

## Included

- Stock status calculation.
- Inventory value calculation.
- Add warehouse stock.
- Remove warehouse stock with insufficient-stock protection.
- Adjust warehouse stock to a non-negative target.
- Transfer stock from warehouse to technician stock.
- Inventory transaction recording for each movement.

## Not included

- Production API endpoints.
- Streamlit UI integration.
- Real production data migration (Task 62).
- Work-order inventory consumption integration (Task 55).
