"""Canonical phone records without overwriting any legacy phone values."""
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat

LEGACY_FIELDS = ["phone", "phone_1", "phone_2", "phone_3", "phone_4"]

def normalized_phone(country, number):
    if country not in phonenumbers.SUPPORTED_REGIONS:
        raise ValueError("Select a supported country for each phone number.")
    try:
        parsed = phonenumbers.parse(number, country)
        if parsed.extension or not phonenumbers.is_valid_number(parsed):
            raise ValueError("Enter a valid phone number without an extension.")
        if not phonenumbers.is_valid_number_for_region(parsed, country):
            raise ValueError("Phone number does not match the selected country.")
        return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    except NumberParseException:
        raise ValueError("Enter a valid phone number for the selected country.") from None

def legacy_phones(customer):
    records = []
    for key in LEGACY_FIELDS:
        number = getattr(customer, key, None)
        if number:
            country = None
            normalized = None
            # Explicit international legacy values can be recognized safely.
            if number.strip().startswith("+"):
                try:
                    parsed = phonenumbers.parse(number, None)
                    country = phonenumbers.region_code_for_number(parsed)
                    normalized = normalized_phone(country, number)
                except (ValueError, NumberParseException):
                    country = None
            records.append(dict(country=country, number=number, label="Primary" if key == "phone" else "Legacy " + key.replace("_", " "), normalized=normalized))
    return records

def prepare_phones(data, customer=None):
    if "phones" not in data:
        return data
    if data["phones"] is None:
        raise ValueError("Use an empty phone collection to remove phone records.")
    old = (getattr(customer, "phones", None) or legacy_phones(customer)) if customer else []
    preserved = {r["number"] for r in old if not r.get("country")}
    records = []
    for record in data["phones"]:
        country, number = record.get("country", "EG"), record["number"]
        if not country and number in preserved:
            country = None
            normalized = None  # Keep unresolved legacy values, never guess their country.
        else:
            normalized = normalized_phone(country, number)
        records.append(dict(country=country, number=number, label=record.get("label") or "Other", normalized=normalized))
    return {**data, "phones":records}
