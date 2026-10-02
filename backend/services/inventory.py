"""Business service for the Axyrel Inventory domain."""

from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.repositories.inventory import InventoryRepository
from backend.schemas.inventory import InventorySummary
from backend.services.inventory_rules import InventoryBusinessRules


class InventoryService:
    """Application service for tenant-scoped inventory operations."""

    def __init__(
        self,
        repository: InventoryRepository | None = None,
    ) -> None:
        self.repository = repository or InventoryRepository()

    def list_items(
        self,
        db: Session,
        company_id: UUID | None,
        search: str | None = None,
        status: str | None = None,
    ):
        return self.repository.list(db, company_id, search, status)

    def get_summary(self, db: Session, company_id: UUID | None) -> InventorySummary:
        items = self.repository.list(db, company_id)
        low_stock_item_ids = [
            item.id for item in items
            if InventoryBusinessRules.stock_status(item).code == "CRITICAL"
        ]
        return InventorySummary(
            item_count=len(items),
            low_stock_count=len(low_stock_item_ids),
            total_stock_value=sum(
                (InventoryBusinessRules.item_value(item) for item in items), Decimal("0")
            ),
            low_stock_item_ids=low_stock_item_ids,
        )

    def get_item(
        self,
        db: Session,
        company_id: UUID | None,
        item_id: UUID,
    ):
        return self.repository.get(db, company_id, item_id)

    def create_item(
        self,
        db: Session,
        company_id: UUID | None,
        data: dict,
    ):
        item_name = data["item_name"].strip()
        if not item_name:
            raise ValueError("Item name is required.")
        data = {**data, "item_name": item_name}
        return self.repository.create(db, company_id, data)

    def update_item(
        self,
        db: Session,
        company_id: UUID | None,
        item_id: UUID,
        data: dict,
    ):
        return self.repository.update(db, company_id, item_id, data)

    def delete_item(
        self,
        db: Session,
        company_id: UUID | None,
        item_id: UUID,
    ):
        return self.repository.soft_delete(db, company_id, item_id)
