from datetime import date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

class PhoneRecord(BaseModel):
    country: str | None = "EG"
    number: str = Field(max_length=100)
    label: str = Field(default="Primary", max_length=100)
    normalized: str | None = None

class CustomerBase(BaseModel):
    name: str
    phone: str | None = None
    phone_1: str | None = None
    phone_2: str | None = None
    phone_3: str | None = None
    phone_4: str | None = None
    phones: list[PhoneRecord] | None = Field(default=None, max_length=100)
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

    @model_validator(mode="before")
    @classmethod
    def expose_legacy_phones(cls, value):
        if not isinstance(value, dict) and getattr(value, "phones", None) is None:
            from backend.services.customer_phones import legacy_phones
            result = {key: getattr(value, key, None) for key in cls.model_fields}
            result["phones"] = legacy_phones(value)
            return result
        return value
