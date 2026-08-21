# Task 38 — Service Contract Migration

## Scope
Introduces the PostgreSQL/domain foundation for tenant-scoped service contracts.

## Added
- `backend/models/service_contract.py`
- `backend/schemas/service_contract.py`
- `backend/repositories/service_contract.py`
- `backend/services/service_contract.py`
- `migrations/007_service_contracts.sql`

## Relationships
- Service Contract → Customer (required)

## Contract fields
- contract_number
- status
- start_date
- end_date
- contract_value
- billing_frequency
- notes

## Validation
- contract value cannot be negative
- end date cannot precede start date
- contract number is unique within a company
- repository operations enforce company/tenant scope

## Deferred
- Production data migration → Task 62
- Contract-related API/UI integration → Tasks 44–45
- Billing/invoice integration → later integration work
- Notifications triggered by contract state → Task 41 / later integration
