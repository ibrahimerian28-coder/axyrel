"""Business rules for warehouse and technician inventory stock."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from backend.models.inventory_item import InventoryItem
from backend.models.inventory_transaction import InventoryTransaction
from backend.models.technician_stock import TechnicianStock
from backend.repositories.inventory import InventoryRepository
from backend.repositories.inventory_transactions import InventoryTransactionRepository
from backend.repositories.technician_stock import TechnicianStockRepository


@dataclass(frozen=True)
class InventoryStockStatus:
    """Normalized stock status derived from the legacy inventory rules."""

    code: str
    quantity: int
    minimum: int
    ideal: int


class InventoryBusinessRules:
    """Central business rules for stock movement and stock levels.

    The class deliberately sits above repositories so UI/API layers do not
    duplicate inventory calculations or movement rules.
    """

    def __init__(
        self,
        inventory_repository: InventoryRepository | None = None,
        transaction_repository: InventoryTransactionRepository | None = None,
        technician_stock_repository: TechnicianStockRepository | None = None,
    ) -> None:
        self.inventory_repository = inventory_repository or InventoryRepository()
        self.transaction_repository = (
            transaction_repository or InventoryTransactionRepository()
        )
        self.technician_stock_repository = (
            technician_stock_repository or TechnicianStockRepository()
        )

    @staticmethod
    def stock_status(item: InventoryItem) -> InventoryStockStatus:
        """Return Good/Low/Critical using the existing inventory thresholds."""
        quantity = int(item.quantity)
        minimum = int(item.min_limit)
        ideal = int(item.ideal_stock)

        if quantity <= minimum:
            code = "CRITICAL"
        elif ideal > 0 and quantity < ideal * 0.5:
            code = "LOW"
        else:
            code = "GOOD"

        return InventoryStockStatus(code, quantity, minimum, ideal)

    @staticmethod
    def item_value(item: InventoryItem) -> Decimal:
        """Return current stock value using quantity multiplied by unit cost."""
        return Decimal(int(item.quantity)) * Decimal(item.cost_price)

    def add_stock(
        self,
        db: Session,
        company_id: UUID | None,
        item_id: UUID,
        quantity: int,
        *,
        reference_type: str | None = None,
        reference_id: str | None = None,
        notes: str | None = None,
    ) -> InventoryItem:
        """Add warehouse stock and record one IN movement."""
        quantity = self._positive_quantity(quantity)
        item = self._required_item(db, company_id, item_id)
        item.quantity += quantity
        self.transaction_repository.create(
            db,
            company_id,
            {
                "inventory_item_id": item.id,
                "transaction_type": "IN",
                "quantity": quantity,
                "reference_type": reference_type,
                "reference_id": reference_id,
                "notes": notes,
            },
        )
        db.flush()
        return item

    def remove_stock(
        self,
        db: Session,
        company_id: UUID | None,
        item_id: UUID,
        quantity: int,
        *,
        reference_type: str | None = None,
        reference_id: str | None = None,
        notes: str | None = None,
    ) -> InventoryItem:
        """Remove warehouse stock without ever allowing a negative balance."""
        quantity = self._positive_quantity(quantity)
        item = self._required_item(db, company_id, item_id)
        if int(item.quantity) < quantity:
            raise ValueError("Insufficient warehouse inventory")

        item.quantity -= quantity
        self.transaction_repository.create(
            db,
            company_id,
            {
                "inventory_item_id": item.id,
                "transaction_type": "OUT",
                "quantity": quantity,
                "reference_type": reference_type,
                "reference_id": reference_id,
                "notes": notes,
            },
        )
        db.flush()
        return item

    def adjust_stock(
        self,
        db: Session,
        company_id: UUID | None,
        item_id: UUID,
        target_quantity: int,
        *,
        reference_type: str | None = "INVENTORY_ADJUSTMENT",
        reference_id: str | None = None,
        notes: str | None = None,
    ) -> InventoryItem:
        """Set warehouse stock to a non-negative target and record adjustment."""
        if target_quantity < 0:
            raise ValueError("target_quantity must be non-negative")

        item = self._required_item(db, company_id, item_id)
        item.quantity = target_quantity
        self.transaction_repository.create(
            db,
            company_id,
            {
                "inventory_item_id": item.id,
                "transaction_type": "ADJUSTMENT",
                "quantity": max(target_quantity, 1),
                "reference_type": reference_type,
                "reference_id": reference_id,
                "notes": notes,
            },
        )
        db.flush()
        return item

    def transfer_to_technician(
        self,
        db: Session,
        company_id: UUID | None,
        technician_id: UUID,
        item_id: UUID,
        quantity: int,
        *,
        reference_id: str | None = None,
        notes: str | None = None,
    ) -> TechnicianStock:
        """Move stock from warehouse to a technician atomically in one session."""
        quantity = self._positive_quantity(quantity)
        item = self._required_item(db, company_id, item_id)
        if int(item.quantity) < quantity:
            raise ValueError("Insufficient warehouse inventory for technician transfer")

        item.quantity -= quantity
        stock = self.technician_stock_repository.get_for_technician_item(
            db, company_id, technician_id, item.id
        )
        if stock is None:
            stock = self.technician_stock_repository.create(
                db,
                company_id,
                {
                    "technician_id": technician_id,
                    "inventory_item_id": item.id,
                    "quantity": quantity,
                },
            )
        else:
            stock.quantity += quantity
            db.flush()

        self.transaction_repository.create(
            db,
            company_id,
            {
                "inventory_item_id": item.id,
                "transaction_type": "OUT",
                "quantity": quantity,
                "reference_type": "TECHNICIAN_TRANSFER",
                "reference_id": reference_id,
                "notes": notes,
            },
        )
        db.flush()
        return stock

    @staticmethod
    def _positive_quantity(quantity: int) -> int:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError("quantity must be greater than zero")
        return quantity

    def _required_item(
        self,
        db: Session,
        company_id: UUID | None,
        item_id: UUID,
    ) -> InventoryItem:
        item = self.inventory_repository.get(db, company_id, item_id)
        if item is None:
            raise ValueError("Inventory item not found")
        return item
