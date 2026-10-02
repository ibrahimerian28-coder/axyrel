"""Build the accepted SQL chain on a generated local database, never application data."""
import contextlib
import io
import unittest
from uuid import uuid4
from unittest.mock import patch

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from backend.core.config import get_settings
from backend.models.base import Base
import backend.models
from backend.scripts import init_database


class Task59DatabaseReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = make_url(get_settings().database_url)
        if url.get_backend_name() != "postgresql" or url.host not in {"localhost", "127.0.0.1", "::1"}:
            raise RuntimeError("Task 59 requires the configured local PostgreSQL test server")
        cls.database_name = "axyrel_task59_test_" + uuid4().hex
        cls.admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
        with cls.admin.connect() as db:
            db.exec_driver_sql(f'CREATE DATABASE "{cls.database_name}"')
        cls.addClassCleanup(cls._drop)
        cls.engine = create_engine(url.set(database=cls.database_name))
        cls.addClassCleanup(cls.engine.dispose)
        cls.target_url = url.set(database=cls.database_name).render_as_string(hide_password=False)
        cls.build_output = io.StringIO()
        # The public CLI's configuration is overridden only inside this test process.
        old_url = init_database.settings.database_url
        try:
            init_database.settings.database_url = cls.target_url
            with contextlib.redirect_stdout(cls.build_output), patch.object(init_database, "create_engine", return_value=cls.engine):
                init_database.main()
        finally:
            init_database.settings.database_url = old_url

    @classmethod
    def _drop(cls):
        if not cls.database_name.startswith("axyrel_task59_test_") or len(cls.database_name) != 51:
            raise RuntimeError("Refusing unexpected disposable database name")
        with cls.admin.connect() as db:
            db.exec_driver_sql(f'DROP DATABASE "{cls.database_name}"')
        cls.admin.dispose()

    def test_complete_migration_chain_succeeds_from_empty_database(self):
        self.assertIn("DATABASE MIGRATIONS: OK", self.build_output.getvalue())
        self.assertIn("OK: 013_service_visit_event_timezone.sql", self.build_output.getvalue())

    def test_all_accepted_model_tables_and_columns_exist(self):
        inspector = inspect(self.engine)
        self.assertEqual(set(inspector.get_table_names()), set(Base.metadata.tables))
        for table in Base.metadata.sorted_tables:
            self.assertEqual({col["name"] for col in inspector.get_columns(table.name)}, set(table.columns.keys()), table.name)

    def test_only_approved_event_columns_use_aware_datetime_types(self):
        inspector = inspect(self.engine)
        for table, fields in (("schedules", ("start_at", "end_at")),
                               ("service_visits", ("actual_start_at", "actual_end_at"))):
            columns = {col["name"]: col for col in inspector.get_columns(table)}
            for field in fields:
                self.assertTrue(columns[field]["type"].timezone)
                self.assertEqual(columns[field]["nullable"], table == "service_visits")
            self.assertFalse(columns["created_at"]["type"].timezone)

    def test_expected_foreign_keys_and_monetary_types(self):
        inspector = inspect(self.engine)
        for table in Base.metadata.sorted_tables:
            actual = {(tuple(row["constrained_columns"]), row["referred_table"], tuple(row["referred_columns"]))
                      for row in inspector.get_foreign_keys(table.name)}
            for fk in table.foreign_key_constraints:
                expected = (tuple(element.parent.name for element in fk.elements), fk.referred_table.name,
                            tuple(element.column.name for element in fk.elements))
                self.assertIn(expected, actual, table.name)
        for table, field in (("invoices", "total"), ("expenses", "amount"), ("inventory_items", "cost_price")):
            column = next(col for col in inspector.get_columns(table) if col["name"] == field)
            self.assertEqual((column["type"].precision, column["type"].scale), (12, 2))

    def test_schema_contains_no_seed_or_customer_data(self):
        with self.engine.connect() as db:
            for table in Base.metadata.sorted_tables:
                self.assertEqual(db.execute(text(f'SELECT count(*) FROM "{table.name}"')).scalar(), 0)

    def test_accepted_identity_inventory_uniqueness_and_checks_exist(self):
        inspector = inspect(self.engine)
        indexes = {row["name"]: row for row in inspector.get_indexes("users")}
        self.assertTrue(indexes["uq_users_email_lower"]["unique"])
        indexes = {row["name"]: row for row in inspector.get_indexes("inventory_items")}
        self.assertTrue(indexes["uq_inventory_items_company_item_name"]["unique"])
        unique = {row["name"] for row in inspector.get_unique_constraints("technician_stock")}
        self.assertIn("uq_technician_stock_company_technician_item", unique)
        for table in ("companies", "users", "inventory_items", "inventory_transactions", "technician_stock"):
            self.assertTrue(inspector.get_check_constraints(table), table)

    def test_orm_reads_and_existing_schema_verifier_work_on_migrated_database(self):
        from backend.scripts import verify_database_schema
        with self.engine.connect() as db:
            for table in Base.metadata.sorted_tables:
                self.assertEqual(db.execute(table.select()).fetchall(), [])
        output = io.StringIO()
        with patch.object(verify_database_schema, "engine", self.engine), contextlib.redirect_stdout(output):
            verify_database_schema.main()
        self.assertIn("DATABASE SCHEMA: OK", output.getvalue())


if __name__ == "__main__":
    unittest.main()
