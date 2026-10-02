"""Current approved indexes/constraints, built and upgraded on isolated PostgreSQL."""
import shutil
import unittest
from uuid import uuid4

import test_task60_tracked_migrations as migration_fixture
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from backend.models.base import Base
import backend.models
from backend.scripts.init_database import apply_migrations

ROOT = migration_fixture.ROOT


class Task61IndexConstraintTests(unittest.TestCase):
    setUp = migration_fixture.Task60TrackedMigrationTests.setUp
    _drop = migration_fixture.Task60TrackedMigrationTests._drop
    _apply = migration_fixture.Task60TrackedMigrationTests._apply
    _rows = migration_fixture.Task60TrackedMigrationTests._rows

    def _build(self):
        self._apply(ROOT / "migrations")

    def test_every_current_model_index_has_equivalent_columns_and_uniqueness(self):
        self._build()
        inspector = inspect(self.engine)
        for table in Base.metadata.sorted_tables:
            actual = {(tuple(index["column_names"]), bool(index["unique"])) for index in inspector.get_indexes(table.name)}
            for index in table.indexes:
                self.assertIn((tuple(col.name for col in index.columns), bool(index.unique)), actual, index.name)

    def test_new_indexes_are_exact_nonunique_definitions(self):
        self._build()
        for table, name, column in (("users", "ix_users_email", "email"),
                                     ("audit_logs", "ix_audit_logs_company_id", "company_id"),
                                     ("audit_logs", "ix_audit_logs_actor_user_id", "actor_user_id")):
            indexes = {index["name"]: index for index in inspect(self.engine).get_indexes(table)}
            self.assertEqual(indexes[name]["column_names"], [column])
            self.assertFalse(indexes[name]["unique"])

    def test_tracked_upgrade_preserves_prior_migrations_and_rerun_skips(self):
        for path in (ROOT / "migrations").glob("*.sql"):
            if int(path.name.split("_")[0]) < 14:
                shutil.copyfile(path, self.directory / path.name)
        self._apply()
        before = self._rows()
        self.assertEqual(len(before), 12)
        shutil.copyfile(ROOT / "migrations/014_required_model_indexes.sql", self.directory / "014_required_model_indexes.sql")
        output = self._apply()
        self.assertEqual(output.count("SKIP:"), 12)
        self.assertEqual(output.count("  OK:"), 1)
        after = self._rows()
        self.assertEqual(after[:-1], before)
        self.assertEqual(after[-1].version, 14)
        self.assertEqual(self._apply().count("SKIP:"), 13)
        self.assertEqual(self._rows(), after)

    def test_existing_primary_and_foreign_key_contracts_are_preserved(self):
        self._build()
        inspector = inspect(self.engine)
        for table in Base.metadata.sorted_tables:
            self.assertEqual(inspector.get_pk_constraint(table.name)["constrained_columns"], [col.name for col in table.primary_key])
            actual = {(tuple(fk["constrained_columns"]), fk["referred_table"], tuple(fk["referred_columns"]))
                      for fk in inspector.get_foreign_keys(table.name)}
            for fk in table.foreign_key_constraints:
                self.assertIn((tuple(e.parent.name for e in fk.elements), fk.referred_table.name,
                               tuple(e.column.name for e in fk.elements)), actual)

    def test_accepted_named_unique_constraints_are_present(self):
        self._build()
        inspector = inspect(self.engine)
        for table, name in (("inventory_items", "uq_inventory_items_company_item_name"),
                             ("technician_stock", "uq_technician_stock_company_technician_item"),
                             ("invoices", "uq_invoices_company_number"),
                             ("service_contracts", "uq_service_contracts_company_number"),
                             ("users", "uq_users_email_lower")):
            names = {index["name"] for index in inspector.get_indexes(table) if index["unique"]}
            self.assertIn(name, names)

    def test_existing_inventory_checks_and_tenant_unique_rule_are_enforced(self):
        self._build()
        company, item = uuid4(), uuid4()
        with self.engine.begin() as db:
            db.execute(text("INSERT INTO inventory_items (id, company_id, item_name) VALUES (:id, :company, 'Part')"),
                       {"id": item, "company": company})
            with self.assertRaises(IntegrityError) as duplicate:
                with db.begin_nested():
                    db.execute(text("INSERT INTO inventory_items (id, company_id, item_name) VALUES (:id, :company, 'Part')"),
                               {"id": uuid4(), "company": company})
            self.assertEqual(duplicate.exception.orig.sqlstate, "23505")
            self.assertEqual(duplicate.exception.orig.diag.constraint_name, "uq_inventory_items_company_item_name")
            db.execute(text("INSERT INTO inventory_items (id, company_id, item_name) VALUES (:id, :company, 'Part')"),
                       {"id": uuid4(), "company": uuid4()})
            for field in ("quantity", "min_limit", "ideal_stock", "cost_price"):
                with self.assertRaises(IntegrityError) as invalid:
                    with db.begin_nested():
                        db.execute(text(f"UPDATE inventory_items SET {field}=-1 WHERE id=:id"), {"id": item})
                self.assertEqual(invalid.exception.orig.sqlstate, "23514")
            with self.assertRaises(IntegrityError) as invalid:
                with db.begin_nested():
                    db.execute(text("INSERT INTO inventory_transactions (id, company_id, inventory_item_id, transaction_type, quantity) "
                                    "VALUES (:id, :company, :item, 'OUT', 0)"), {"id": uuid4(), "company": company, "item": item})
            self.assertEqual(invalid.exception.orig.sqlstate, "23514")

    def test_index_migration_preserves_existing_rows(self):
        for path in (ROOT / "migrations").glob("*.sql"):
            if int(path.name.split("_")[0]) < 14:
                shutil.copyfile(path, self.directory / path.name)
        self._apply()
        audit = uuid4()
        with self.engine.begin() as db:
            db.execute(text("INSERT INTO audit_logs (id, company_id, action) VALUES (:id, :company, 'explicit')"),
                       {"id": audit, "company": uuid4()})
            before = db.execute(text("SELECT * FROM audit_logs WHERE id=:id"), {"id": audit}).one()
        shutil.copyfile(ROOT / "migrations/014_required_model_indexes.sql", self.directory / "014_required_model_indexes.sql")
        self._apply()
        with self.engine.connect() as db:
            self.assertEqual(db.execute(text("SELECT * FROM audit_logs WHERE id=:id"), {"id": audit}).one(), before)


if __name__ == "__main__":
    unittest.main()
