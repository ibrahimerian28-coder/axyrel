"""Verify that every ORM model table exists in PostgreSQL."""
from __future__ import annotations

from sqlalchemy import inspect

from backend.core.database import engine
import backend.models  # noqa: F401 - registers all ORM models


def main() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    expected = {
        "customers",
        "assets",
        "service_requests",
        "work_orders",
        "schedules",
        "service_visits",
        "service_history",
        "inventory_items",
        "inventory_transactions",
        "technician_stock",
        "invoices",
        "service_contracts",
        "expenses",
        "notifications",
        "audit_logs",
        "companies",
        "users",
    }

    missing = sorted(expected - tables)
    print("EXPECTED TABLES:", len(expected))
    print("FOUND TABLES:", len(expected & tables))
    if missing:
        print("MISSING TABLES:")
        for table in missing:
            print(f"  - {table}")
        raise SystemExit(1)

    print("DATABASE SCHEMA: OK")


if __name__ == "__main__":
    main()
