"""Tenant isolation primitives for repository access.

Task 24 establishes the rule that tenant-scoped repository operations
must receive an explicit company_id. No implicit global-company fallback.
"""

from uuid import UUID


class TenantScopeRequiredError(ValueError):
    """Raised when a tenant-scoped operation has no company context."""


def require_company_id(company_id: UUID | None) -> UUID:
    """Return a valid company id or fail closed."""
    if company_id is None:
        raise TenantScopeRequiredError(
            "company_id is required for tenant-scoped data access"
        )
    return company_id
