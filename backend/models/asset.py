"""Asset ORM model for the Axyrel service domain."""

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class Asset(Base):
    """A customer-owned serviceable asset/equipment record."""

    __tablename__ = "assets"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    display_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    asset_type: Mapped[str] = mapped_column(String(150), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(150), index=True)
    model: Mapped[str | None] = mapped_column(String(150))
    manufacturer: Mapped[str | None] = mapped_column(String(150))

    installation_date: Mapped[date | None] = mapped_column(Date)
    warranty_start: Mapped[date | None] = mapped_column(Date)
    warranty_end: Mapped[date | None] = mapped_column(Date)

    status: Mapped[str] = mapped_column(String(30), default="Active")
    notes: Mapped[str | None] = mapped_column(String(1000))
