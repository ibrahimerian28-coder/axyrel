"""Application service for inventory transaction records."""

from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.inventory_transactions import InventoryTransactionRepository


ALLOWED_TRANSACTION_TYPES = {"IN", "OUT", "ADJUSTMENT"}


class InventoryTransactionService:
    """Records and queries inventory movements without owning later business rules."""

    def __init__(self, repository: InventoryTransactionRepository | None = None) -> None:
        self.repository = repository or InventoryTransactionRepository()

    def get_transaction(self, db: Session, company_id: UUID | None, transaction_id: UUID):
        return self.repository.get(db, company_id, transaction_id)

    def list_transactions(
        self,
        db: Session,
        company_id: UUID | None,
        inventory_item_id: UUID | None = None,
        transaction_type: str | None = None,
    ):
        return self.repository.list(db, company_id, inventory_item_id, transaction_type)

    def create_transaction(
        self,
        db: Session,
        company_id: UUID | None,
        data: dict,
    ):
        transaction_type = str(data.get("transaction_type", "")).strip().upper()
        if transaction_type not in ALLOWED_TRANSACTION_TYPES:
            raise ValueError(
                "transaction_type must be one of: IN, OUT, ADJUSTMENT"
            )
        data = {**data, "transaction_type": transaction_type}
        if int(data.get("quantity", 0)) <= 0:
            raise ValueError("quantity must be greater than zero")
        return self.repository.create(db, company_id, data)
