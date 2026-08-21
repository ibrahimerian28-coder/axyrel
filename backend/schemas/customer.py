from datetime import date
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class CustomerBase(BaseModel):
    name: str
    phone: str | None = None
    phone_1: str | None = None
    phone_2: str | None = None
    phone_3: str | None = None
    phone_4: str | None = None
    address: str | None = None
    area: str | None = None
    location_url: str | None = None
    install_date: date | None = None
    cycle: str | None = None
    device_type: str | None = None
    status: str = "Active"

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(CustomerBase):
    pass

class CustomerRead(CustomerBase):
    id: UUID
    company_id: UUID
    display_id: int | None = None
    model_config = ConfigDict(from_attributes=True)
