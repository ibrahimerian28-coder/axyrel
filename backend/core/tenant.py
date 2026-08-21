"""Company / tenant context foundation for Axyrel.

Task 23 only establishes the request context abstraction.
Tenant enforcement is implemented in Task 24.
"""

from contextvars import ContextVar
from uuid import UUID


_current_company_id: ContextVar[UUID | None] = ContextVar(
    "current_company_id", default=None
)


def set_company_context(company_id: UUID) -> None:
    """Set the active company identifier for the current request context."""
    _current_company_id.set(company_id)


def get_company_context() -> UUID | None:
    """Return the active company identifier, if one is set."""
    return _current_company_id.get()


def clear_company_context() -> None:
    """Clear the active company context."""
    _current_company_id.set(None)
