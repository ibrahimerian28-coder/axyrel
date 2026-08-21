"""Task 32 legacy Inventory -> PostgreSQL data mapping foundation.

This module intentionally does not perform a live Google Sheets import.
The production data transfer remains scheduled for Task 62.
"""

from decimal import Decimal, InvalidOperation
from typing import Any


LEGACY_INVENTORY_FIELDS = (
    "item_name",
    "quantity",
    "min_limit",
    "cost_price",
    "ideal_stock",
)


def _non_negative_int(value: Any) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return 0
    return max(number, 0)


def _non_negative_decimal(value: Any) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")
    return max(number, Decimal("0"))


def map_legacy_inventory_row(row: dict[str, Any]) -> dict[str, Any]:
    """Map one legacy Inventory row to the Task 32 PostgreSQL shape."""

    item_name = str(row.get("item_name", "")).strip()
    if not item_name:
        raise ValueError("item_name is required")

    return {
        "item_name": item_name,
        "quantity": _non_negative_int(row.get("quantity")),
        "min_limit": _non_negative_int(row.get("min_limit")),
        "cost_price": _non_negative_decimal(row.get("cost_price")),
        "ideal_stock": _non_negative_int(row.get("ideal_stock")),
        "status": "Active",
    }
