"""Persistence operations for tenant-scoped inventory items."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.tenant_isolation import require_company_id
from backend.models.inventory_item import InventoryItem
from backend.repositories.base import TenantScopedRepository


class InventoryRepository(TenantScopedRepository):
    """Tenant-scoped repository for InventoryItem records."""

    def get(
        self,
        db: Session,
        company_id: UUID | None,
        item_id: UUID,
    ) -> InventoryItem | None:
        company_id = self._require_company_scope(company_id)
        return db.scalar(
            select(InventoryItem).where(
                InventoryItem.id == item_id,
                InventoryItem.company_id == company_id,
                InventoryItem.status != "Deleted",
            )
        )

    def list(
        self,
        db: Session,
        company_id: UUID | None,
        search: str | None = None,
        status: str | None = None,
    ) -> list[InventoryItem]:
        company_id = require_company_id(company_id)
        stmt = select(InventoryItem).where(
            InventoryItem.company_id == company_id,
            InventoryItem.status != "Deleted",
        )

        if search and search.strip():
            stmt = stmt.where(
                InventoryItem.item_name.ilike(f"%{search.strip()}%")
            )

        if status and status.strip():
            stmt = stmt.where(InventoryItem.status == status.strip())

        return list(
            db.scalars(
                stmt.order_by(InventoryItem.item_name)
            ).all()
        )

    def create(
        self,
        db: Session,
        company_id: UUID | None,
        data: dict,
    ) -> InventoryItem:
        company_id = require_company_id(company_id)
        item = InventoryItem(company_id=company_id, **data)
        db.add(item)
        db.flush()
        return item

    def update(
        self,
        db: Session,
        company_id: UUID | None,
        item_id: UUID,
        data: dict,
    ) -> InventoryItem | None:
        item = self.get(db, company_id, item_id)
        if item is None:
            return None

        for key, value in data.items():
            setattr(item, key, value)
        db.flush()
        return item

    def soft_delete(
        self,
        db: Session,
        company_id: UUID | None,
        item_id: UUID,
    ) -> InventoryItem | None:
        item = self.get(db, company_id, item_id)
        if item is None:
            return None

        item.status = "Deleted"
        db.flush()
        return item
