"""Technician stock ORM model for the Axyrel inventory domain."""
from uuid import UUID, uuid4
from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.base import Base

class TechnicianStock(Base):
    """Company-scoped quantity of an inventory item assigned to a technician."""
    __tablename__ = "technician_stock"
    __table_args__ = (
        UniqueConstraint("company_id", "technician_id", "inventory_item_id", name="uq_technician_stock_company_technician_item"),
        CheckConstraint("quantity >= 0", name="ck_technician_stock_quantity_non_negative"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    technician_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    inventory_item_id: Mapped[UUID] = mapped_column(ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(nullable=False, default=0)
