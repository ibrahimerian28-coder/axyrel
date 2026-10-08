"""OD-21 migration tracking against generated local PostgreSQL databases only."""
import contextlib
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import io
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from backend.core.config import get_settings
from backend.scripts.init_database import apply_migrations, discover_migrations, MigrationError, LEDGER

ROOT = Path(__file__).resolve().parents[1]


class Task60TrackedMigrationTests(unittest.TestCase):
    def setUp(self):
        url = make_url(get_settings().database_url)
        if url.get_backend_name() != "postgresql" or url.host not in {"localhost", "127.0.0.1", "::1"}:
            raise RuntimeError("Task 60 requires the configured local PostgreSQL test server")
        self.database_name = "axyrel_task60_test_" + uuid4().hex
        self.admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
        with self.admin.connect() as db:
            db.exec_driver_sql(f'CREATE DATABASE "{self.database_name}"')
        self.addCleanup(self._drop)
        self.engine = create_engine(url.set(database=self.database_name))
        self.addCleanup(self.engine.dispose)
        directory = tempfile.TemporaryDirectory(prefix="axyrel_task60_")
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def _drop(self):
        if not self.database_name.startswith("axyrel_task60_test_") or len(self.database_name) != 51:
            raise RuntimeError("Refusing unexpected disposable database name")
        with self.admin.connect() as db:
            db.exec_driver_sql(f'DROP DATABASE "{self.database_name}"')
        self.admin.dispose()

    def _write(self, name, sql):
        path = self.directory / name
        path.write_text(sql, encoding="utf-8")
        return path

    def _apply(self, directory=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            apply_migrations(self.engine, directory or self.directory)
        return output.getvalue()

    def _rows(self):
        with self.engine.connect() as db:
            return db.execute(text(f"SELECT version, filename, checksum, applied_at FROM {LEDGER} ORDER BY version")).all()

    def test_fresh_complete_chain_ledger_and_verified_rerun(self):
        files = ROOT / "migrations"
        self._apply(files)
        before = self._rows()
        expected = discover_migrations(files)
        self.assertEqual(len(before), len(expected))
        for row, migration in zip(before, expected):
            self.assertEqual(tuple(row[:3]), (migration.version, migration.filename, migration.checksum))
            self.assertEqual(row.checksum, sha256((files / migration.filename).read_bytes()).hexdigest())
            self.assertIsNotNone(row.applied_at.utcoffset())
        output = self._apply(files)
        self.assertEqual(output.count("SKIP:"), len(expected))
        self.assertNotIn("Applying", output)
        self.assertEqual(self._rows(), before)
        self.assertTrue(next(c for c in inspect(self.engine).get_columns("schedules") if c["name"] == "start_at")["type"].timezone)

    def test_numeric_order_differs_from_filename_order(self):
        self._write("10_later.sql", "INSERT INTO ordered VALUES (10);")
        self._write("2_first.sql", "CREATE TABLE ordered (version integer); INSERT INTO ordered VALUES (2);")
        self._apply()
        self.assertEqual([row.version for row in self._rows()], [2, 10])
        with self.engine.connect() as db:
            self.assertEqual(db.execute(text("SELECT version FROM ordered ORDER BY ctid")).scalars().all(), [2, 10])

    def test_checksum_change_blocks_all_pending_work_without_history_mutation(self):
        path = self._write("001_first.sql", "CREATE TABLE first_table (id integer);")
        self._apply()
        before = self._rows()
        path.write_text(path.read_text() + "\n-- changed accepted file", encoding="utf-8")
        self._write("002_pending.sql", "CREATE TABLE must_not_exist (id integer);")
        with self.assertRaisesRegex(MigrationError, "checksum mismatch"):
            self._apply()
        self.assertEqual(self._rows(), before)
        self.assertNotIn("must_not_exist", inspect(self.engine).get_table_names())

    def test_recorded_filename_change_refused(self):
        path = self._write("001_original.sql", "SELECT 1;")
        self._apply()
        before = self._rows()
        path.rename(self.directory / "001_renamed.sql")
        with self.assertRaises(MigrationError):
            self._apply()
        self.assertEqual(self._rows(), before)

    def test_missing_recorded_file_refused(self):
        path = self._write("001_first.sql", "SELECT 1;")
        self._apply()
        path.unlink()
        self._write("002_other.sql", "SELECT 2;")
        with self.assertRaises(MigrationError):
            self._apply()

    def test_failed_migration_rolls_back_ddl_and_has_no_success_record(self):
        self._write("001_failed.sql", "CREATE TABLE rolled_back (id integer); SELECT 1/0;")
        with self.assertRaises(Exception):
            self._apply()
        self.assertEqual(self._rows(), [])
        self.assertNotIn("rolled_back", inspect(self.engine).get_table_names())

    def test_wrapped_failure_dollar_block_and_success_record_are_atomic(self):
        self._write("001_wrapped.sql", "-- original wrapper\nBEGIN; DO $$ BEGIN PERFORM 1; END $$; "
                    "CREATE TABLE rolled_back (id integer); SELECT 1/0; COMMIT;")
        with self.assertRaises(Exception):
            self._apply()
        self.assertEqual(self._rows(), [])
        self.assertNotIn("rolled_back", inspect(self.engine).get_table_names())

    def test_successful_prefix_remains_and_failed_pending_can_be_repaired(self):
        self._write("001_first.sql", "CREATE TABLE kept (id integer);")
        failed = self._write("003_pending.sql", "CREATE TABLE rolled_back (id integer); SELECT 1/0;")
        with self.assertRaises(Exception):
            self._apply()
        before = self._rows()
        self.assertEqual([row.version for row in before], [1])
        failed.write_text("CREATE TABLE repaired (id integer);", encoding="utf-8")
        self._apply()
        self.assertEqual(self._rows()[0], before[0])
        self.assertEqual([row.version for row in self._rows()], [1, 3])

    def test_existing_untracked_axyrel_schema_is_not_baselined(self):
        with self.engine.begin() as db:
            db.execute(text("CREATE TABLE customers (id uuid PRIMARY KEY)"))
        self._write("001_first.sql", "SELECT 1;")
        with self.assertRaisesRegex(MigrationError, "baseline/reconciliation"):
            self._apply()
        self.assertEqual(inspect(self.engine).get_table_names(), ["customers"])

    def test_empty_ledger_cannot_hide_untracked_schema(self):
        self._write("001_first.sql", "SELECT 1/0;")
        with self.assertRaises(Exception):
            self._apply()
        with self.engine.begin() as db:
            db.execute(text("CREATE TABLE customers (id uuid PRIMARY KEY)"))
        with self.assertRaisesRegex(MigrationError, "reconciliation"):
            self._apply()
        self.assertEqual(self._rows(), [])

    def test_duplicate_versions_refused_before_database_changes(self):
        self._write("01_first.sql", "SELECT 1;")
        self._write("1_duplicate.sql", "SELECT 1;")
        with self.assertRaises(MigrationError):
            self._apply()
        self.assertEqual(inspect(self.engine).get_table_names(), [])

    def test_unknown_transaction_control_refused_before_database_changes(self):
        self._write("001_first.sql", "CREATE TABLE unsafe (id integer); COMMIT; SELECT 1/0;")
        with self.assertRaisesRegex(MigrationError, "transaction control"):
            self._apply()
        self.assertEqual(inspect(self.engine).get_table_names(), [])

    def test_ambiguous_escaped_sql_literal_requires_review(self):
        self._write("001_first.sql", "SELECT E'backslash" + chr(92) + "value';")
        with self.assertRaisesRegex(MigrationError, "syntax requires migration review"):
            self._apply()
        self.assertEqual(inspect(self.engine).get_table_names(), [])

    def test_new_earlier_version_does_not_change_verified_history(self):
        self._write("003_first.sql", "SELECT 1;")
        self._apply()
        before = self._rows()
        self._write("002_earlier.sql", "SELECT 2;")
        with self.assertRaises(MigrationError):
            self._apply()
        self.assertEqual(self._rows(), before)

    def test_cooperative_concurrent_runners_record_once(self):
        self._write("001_first.sql", "CREATE TABLE once_only (id integer);")
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: apply_migrations(self.engine, self.directory), range(2)))
        self.assertEqual(results, [None, None])
        self.assertEqual(len(self._rows()), 1)

    def test_runner_restores_connection_transaction_mode(self):
        self._write("001_first.sql", "SELECT 1;")
        self._apply()
        with self.engine.connect() as db:
            self.assertFalse(db.connection.driver_connection.autocommit)
            db.execute(text("CREATE TABLE rolled_back (id integer)"))
            db.rollback()
        self.assertNotIn("rolled_back", inspect(self.engine).get_table_names())

    def test_ledger_record_failure_rolls_back_successful_sql(self):
        self._write("001_first.sql", "SELECT 1;")
        self._apply()
        before = self._rows()
        with self.engine.begin() as db:
            db.exec_driver_sql("CREATE FUNCTION refuse_record() RETURNS trigger LANGUAGE plpgsql AS $$ "
                               "BEGIN RAISE EXCEPTION 'injected ledger failure'; END $$")
            db.exec_driver_sql(f"CREATE TRIGGER refuse_record BEFORE INSERT ON {LEDGER} "
                               "FOR EACH ROW EXECUTE FUNCTION refuse_record()")
        self._write("002_pending.sql", "CREATE TABLE rolled_back (id integer);")
        with self.assertRaises(Exception):
            self._apply()
        self.assertEqual(self._rows(), before)
        self.assertNotIn("rolled_back", inspect(self.engine).get_table_names())


if __name__ == "__main__":
    unittest.main()
