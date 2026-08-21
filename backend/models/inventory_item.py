"""Inventory item ORM model for the Axyrel inventory domain."""

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class InventoryItem(Base):
    """Company-owned inventory item migrated from the legacy Inventory data."""

    __tablename__ = "inventory_items"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_inventory_items_quantity_non_negative"),
        CheckConstraint("min_limit >= 0", name="ck_inventory_items_min_limit_non_negative"),
        CheckConstraint("ideal_stock >= 0", name="ck_inventory_items_ideal_stock_non_negative"),
        CheckConstraint("cost_price >= 0", name="ck_inventory_items_cost_price_non_negative"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False, default=0)
    min_limit: Mapped[int] = mapped_column(nullable=False, default=0)
    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    ideal_stock: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Active")
