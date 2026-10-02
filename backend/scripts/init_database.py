"""Checksum-verified numbered PostgreSQL migrations; untracked schemas require approval."""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from hashlib import sha256
import re

from sqlalchemy import create_engine

from backend.core.config import settings


LEDGER = "axyrel_schema_migrations"


class MigrationError(RuntimeError):
    """A migration plan or history cannot be verified safely."""


@dataclass(frozen=True)
class Migration:
    version: int
    filename: str
    checksum: str
    sql: str


def discover_migrations(directory: Path) -> list[Migration]:
    migrations = []
    for path in directory.glob("*.sql"):
        match = re.fullmatch(r"(\d+)_[A-Za-z0-9_]+\.sql", path.name)
        if match is None:
            raise MigrationError("Invalid numbered migration filename.")
        content = path.read_bytes()
        migrations.append(Migration(int(match[1]), path.name, sha256(content).hexdigest(), content.decode("utf-8")))
    migrations.sort(key=lambda migration: migration.version)
    if not migrations or len({m.version for m in migrations}) != len(migrations):
        raise MigrationError("Migrations must have distinct numeric versions and cannot be empty.")
    return migrations


def migration_body(sql: str) -> str:
    """Remove paired outer BEGIN/COMMIT in memory, without changing source files.

    Quoted literals/identifiers, dollar bodies and comments are masked when
    locating top-level statements. Nested block comments require review.
    """
    pattern = re.compile(r"--[^\n]*(?:\n|$)|/\*.*?\*/|'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"|"
                         r"(?P<tag>\$(?:[A-Za-z_]\w*)?\$).*?(?P=tag)", re.DOTALL)
    masked = list(sql)
    for match in pattern.finditer(sql):
        if match[0].startswith("/*") and "/*" in match[0][2:]:
            raise MigrationError("Nested SQL comments require migration review.")
        if match[0].startswith("'") and "\\" in match[0]:
            raise MigrationError("Escaped SQL string syntax requires migration review.")
        masked[match.start():match.end()] = " " * (match.end() - match.start())
    visible = "".join(masked)
    statements = []
    start = 0
    for end in [m.start() for m in re.finditer(";", visible)] + [len(sql)]:
        words = visible[start:end].strip().upper().split()
        if words:
            statements.append((start, end, words))
        start = end + 1
    if not statements:
        raise MigrationError("Empty migration SQL.")
    body_start, body_end = 0, len(sql)
    if statements[0][2] == ["BEGIN"] and statements[-1][2] == ["COMMIT"]:
        body_start, body_end = statements[0][1] + 1, statements[-1][0]
        statements = statements[1:-1]
    for _, _, words in statements:
        if words[0] in {"BEGIN", "COMMIT", "ROLLBACK", "ABORT", "END", "SAVEPOINT", "RELEASE"} or (
            words[:2] in (["START", "TRANSACTION"], ["PREPARE", "TRANSACTION"], ["SET", "TRANSACTION"])):
            raise MigrationError("Unsupported SQL transaction control; review migration before execution.")
    return sql[body_start:body_end]


def apply_migrations(engine, directory: Path) -> None:
    migrations = discover_migrations(directory)
    bodies = {m.version: migration_body(m.sql) for m in migrations}
    raw = engine.raw_connection()
    connection = raw.driver_connection
    original_autocommit = connection.autocommit
    locked = False
    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_schema()")
            schema = cursor.fetchone()[0]
            if schema is None:
                raise MigrationError("No target schema selected; review search_path.")
            ledger_name = '"' + schema.replace('"', '""') + '"."' + LEDGER + '"'
            # Session lock serializes cooperative runners across migration commits.
            cursor.execute("SELECT pg_advisory_lock(hashtext(current_database()), "
                           "hashtext(%s))", (schema + ":axyrel_migrations",))
            locked = True
            cursor.execute("SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                           "WHERE n.nspname=current_schema() AND c.relkind IN ('r','p','v','m','S','f')")
            objects = {row[0] for row in cursor.fetchall()}
            if LEDGER not in objects:
                if objects:
                    raise MigrationError("Untracked non-empty schema: owner-approved baseline/reconciliation required.")
                with connection.transaction():
                    cursor.execute(f"CREATE TABLE {ledger_name} ("
                                   "version BIGINT PRIMARY KEY, filename TEXT NOT NULL UNIQUE, "
                                   "checksum VARCHAR(64) NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            cursor.execute(f"SELECT version, filename, checksum, applied_at FROM {ledger_name} ORDER BY version")
            recorded = cursor.fetchall()
            if not recorded and objects - {LEDGER}:
                raise MigrationError("Empty ledger with existing schema: owner-approved reconciliation required.")
            if len(recorded) > len(migrations):
                raise MigrationError("Ledger history is not present in the current migration files.")
            for row, migration in zip(recorded, migrations):
                if row[:3] != (migration.version, migration.filename, migration.checksum) or row[3] is None:
                    raise MigrationError("Migration history identity/checksum mismatch; reconciliation required.")
            print(f"Migrations: {len(migrations)}")
            for index, migration in enumerate(migrations):
                if index < len(recorded):
                    print(f"  SKIP: {migration.filename} (verified)")
                    continue
                print(f"Applying {migration.filename} ...")
                # Migration effects and its success record commit atomically.
                with connection.transaction():
                    cursor.execute(bodies[migration.version], prepare=False)
                    cursor.execute(f"INSERT INTO {ledger_name} (version, filename, checksum) VALUES (%s, %s, %s)",
                                   (migration.version, migration.filename, migration.checksum))
                print(f"  OK: {migration.filename}")
        print("DATABASE MIGRATIONS: OK")
    finally:
        try:
            if locked:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_unlock(hashtext(current_database()), "
                                   "hashtext(%s))", (schema + ":axyrel_migrations",))
        finally:
            try:
                connection.autocommit = original_autocommit
            finally:
                raw.close()


def main() -> None:
    engine = None
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        apply_migrations(engine, Path(__file__).resolve().parents[2] / "migrations")
    except MigrationError as exc:
        raise SystemExit(str(exc)) from None
    except Exception:
        raise SystemExit("Migration failed; inspect the approved target and migration state before retrying.") from None
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    main()
