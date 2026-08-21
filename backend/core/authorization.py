"""Database-backed authorization foundation for Axyrel."""
from __future__ import annotations

from enum import StrEnum
from typing import Callable

from fastapi import Depends, HTTPException, status

from backend.core.authentication import CurrentUser
from backend.models.user import User


class Role(StrEnum):
    """MVP application roles."""

    ADMIN = "admin"
    MANAGER = "manager"
    TECHNICIAN = "technician"


class Permission(StrEnum):
    """MVP permissions used by the backend authorization layer."""

    COMPANY_READ = "company:read"
    COMPANY_MANAGE = "company:manage"
    USER_READ = "user:read"
    USER_MANAGE = "user:manage"
    CUSTOMER_READ = "customer:read"
    CUSTOMER_MANAGE = "customer:manage"
    ASSET_READ = "asset:read"
    ASSET_MANAGE = "asset:manage"
    SERVICE_READ = "service:read"
    SERVICE_MANAGE = "service:manage"
    INVENTORY_READ = "inventory:read"
    INVENTORY_MANAGE = "inventory:manage"
    BILLING_READ = "billing:read"
    BILLING_MANAGE = "billing:manage"
    EXPENSE_READ = "expense:read"
    EXPENSE_MANAGE = "expense:manage"
    REPORT_READ = "report:read"
    SETTINGS_MANAGE = "settings:manage"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.MANAGER: frozenset(
        {
            Permission.COMPANY_READ,
            Permission.USER_READ,
            Permission.CUSTOMER_READ,
            Permission.CUSTOMER_MANAGE,
            Permission.ASSET_READ,
            Permission.ASSET_MANAGE,
            Permission.SERVICE_READ,
            Permission.SERVICE_MANAGE,
            Permission.INVENTORY_READ,
            Permission.INVENTORY_MANAGE,
            Permission.BILLING_READ,
            Permission.BILLING_MANAGE,
            Permission.EXPENSE_READ,
            Permission.EXPENSE_MANAGE,
            Permission.REPORT_READ,
            Permission.AUDIT_READ,
        }
    ),
    Role.TECHNICIAN: frozenset(
        {
            Permission.CUSTOMER_READ,
            Permission.ASSET_READ,
            Permission.SERVICE_READ,
            Permission.SERVICE_MANAGE,
            Permission.INVENTORY_READ,
        }
    ),
}


def permissions_for_role(role: Role | str) -> frozenset[Permission]:
    return ROLE_PERMISSIONS[Role(role)]


def has_permission(role: Role | str, permission: Permission | str) -> bool:
    return Permission(permission) in permissions_for_role(role)


def require_permission(permission: Permission | str) -> Callable:
    """Create a FastAPI dependency backed by the authenticated DB user role."""
    required = Permission(permission)

    def dependency(user: CurrentUser) -> User:
        try:
            role = Role(user.role)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has an invalid application role",
            ) from exc

        if required not in permissions_for_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency
