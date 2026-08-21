


from uuid import UUID

from backend.core.tenant_isolation import require_company_id


class TenantScopedRepository:
    """Base helper for repositories that store company-owned records."""

    def _require_company_scope(self, company_id: UUID | None) -> UUID:
        return require_company_id(company_id)
