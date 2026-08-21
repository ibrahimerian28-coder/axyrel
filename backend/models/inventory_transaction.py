"""Inventory transaction ORM model for the Axyrel inventory domain."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class InventoryTransaction(Base):
    """Immutable-style stock movement record owned by a company."""

    __tablename__ = "inventory_transactions"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_transactions_quantity_positive"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    inventory_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
