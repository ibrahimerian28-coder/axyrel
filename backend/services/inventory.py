"""Business service for the Axyrel Inventory domain."""

from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.inventory import InventoryRepository


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
