# Task 37 — Billing / Invoicing Migration

## Scope
Introduces the PostgreSQL/domain foundation for tenant-scoped invoices.

## Added
- `backend/models/invoice.py`
- `backend/schemas/invoice.py`
- `backend/repositories/invoice.py`
- `backend/services/invoice.py`
- `migrations/006_invoices.sql`

## Relationships
- Invoice → Customer (required)
- Invoice → Work Order (optional)

## Financial fields
- subtotal
- discount
- tax
- total
- paid_amount

## Status
The migration foundation is prepared for later API/UI integration.

## Deferred
- Production data migration → Task 62
- Work Order → Billing integration → Task 56
- Payment workflow/endpoints → later API work
- Streamlit UI → Task 45
