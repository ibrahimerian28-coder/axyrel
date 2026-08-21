"""Apply all numbered PostgreSQL migrations in order.

This script is intentionally small and idempotent: every migration in this
project uses CREATE TABLE/INDEX IF NOT EXISTS where appropriate.

Run from the project root:
    python -m backend.scripts.init_database

The database URL is loaded from the same .env/settings used by FastAPI.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from backend.core.config import settings


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    migrations_dir = root / "migrations"
    files = sorted(migrations_dir.glob("*.sql"))

    if not files:
        raise SystemExit(f"No SQL migrations found in {migrations_dir}")

    engine = create_engine(settings.database_url, pool_pre_ping=True)

    print(f"Database: {settings.database_url.split('@')[-1]}")
    print(f"Migrations: {len(files)}")

    with engine.begin() as conn:
        for path in files:
            print(f"Applying {path.name} ...")
            sql = path.read_text(encoding="utf-8")
            # PostgreSQL accepts a migration as a multi-statement SQL string.
            conn.execute(text(sql))
            print(f"  OK: {path.name}")

    print("DATABASE MIGRATIONS: OK")


if __name__ == "__main__":
    main()
