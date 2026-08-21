from datetime import date
from uuid import UUID, uuid4
from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.base import Base

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    display_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    phone_1: Mapped[str | None] = mapped_column(String(50))
    phone_2: Mapped[str | None] = mapped_column(String(50))
    phone_3: Mapped[str | None] = mapped_column(String(50))
    phone_4: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String(500))
    area: Mapped[str | None] = mapped_column(String(150))
    location_url: Mapped[str | None] = mapped_column(String(1000))
    install_date: Mapped[date | None] = mapped_column(Date)
    cycle: Mapped[str | None] = mapped_column(String(50))
    device_type: Mapped[str | None] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(30), default="Active")
