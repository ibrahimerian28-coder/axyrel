"""OD-22 synthetic-only rehearsal of accepted mapping and persistence behavior."""
import unittest
from decimal import Decimal
from uuid import uuid4

import test_task60_tracked_migrations as fixture
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.migrations.inventory_data import map_legacy_inventory_row
from backend.models.inventory_item import InventoryItem
from backend.models.inventory_transaction import InventoryTransaction
from backend.schemas.inventory import InventoryItemCreate
from backend.services.inventory import InventoryService


class Task62MigrationRehearsalTests(unittest.TestCase):
    setUp = fixture.Task60TrackedMigrationTests.setUp
    _drop = fixture.Task60TrackedMigrationTests._drop
    _apply = fixture.Task60TrackedMigrationTests._apply
    _rows = fixture.Task60TrackedMigrationTests._rows

    def _build(self):
        self._apply(fixture.ROOT / 'migrations')
        return InventoryService()

    def _mapped(self, row):
        return InventoryItemCreate(**map_legacy_inventory_row(row)).model_dump()

    def test_valid_mapping_roundtrip_and_generated_identifier(self):
        service = self._build()
        row = dict(item_name='  Synthetic Filter  ', quantity='7', min_limit='2',
                   ideal_stock='12', cost_price='15.25')
        mapped = self._mapped(row)
        self.assertEqual(mapped, self._mapped(row))
        self.assertEqual(row['item_name'], '  Synthetic Filter  ')
        company = uuid4()
        with Session(self.engine) as db, db.begin():
            item = service.create_item(db, company, mapped)
            identifier = item.id
        with Session(self.engine) as db:
            item = service.get_item(db, company, identifier)
            self.assertEqual((item.item_name, item.quantity, item.min_limit, item.ideal_stock,
                              item.cost_price, item.status),
                             ('Synthetic Filter', 7, 2, 12, Decimal('15.25'), 'Active'))
            self.assertIsNotNone(identifier)

    def test_existing_coercions_are_preserved_not_new_rejection_policy(self):
        self._build()
        row = dict(item_name='Synthetic', quantity='3.9', min_limit=-2,
                   ideal_stock='bad', cost_price='bad', id=str(uuid4()), status='Deleted')
        mapped = self._mapped(row)
        self.assertEqual((mapped['quantity'], mapped['min_limit'], mapped['ideal_stock'],
                          mapped['cost_price'], mapped['status']), (3, 0, 0, Decimal('0'), 'Active'))
        self.assertNotIn('id', mapped)
        self.assertEqual(self._mapped({'item_name': 'Synthetic'})['quantity'], 0)

    def test_tenant_scoped_reads_and_same_name_across_companies(self):
        service = self._build()
        company, other = uuid4(), uuid4()
        with Session(self.engine) as db, db.begin():
            first = service.create_item(db, company, self._mapped({'item_name': 'Synthetic'}))
            identifier = first.id
            service.create_item(db, other, self._mapped({'item_name': 'Synthetic'}))
        with Session(self.engine) as db:
            self.assertIsNone(service.get_item(db, other, identifier))
            self.assertEqual(len(service.list_items(db, company)), 1)
            self.assertEqual(len(service.list_items(db, other)), 1)
            with self.assertRaises(ValueError):
                service.list_items(db, None)

    def test_duplicate_detection_rolls_back_entire_synthetic_batch(self):
        service = self._build()
        company = uuid4()
        with Session(self.engine) as db:
            with self.assertRaises(IntegrityError) as failure:
                with db.begin():
                    service.create_item(db, company, self._mapped({'item_name': 'Synthetic'}))
                    service.create_item(db, company, self._mapped({'item_name': ' Synthetic '}))
            self.assertEqual(failure.exception.orig.sqlstate, '23505')
            self.assertEqual(failure.exception.orig.diag.constraint_name,
                             'uq_inventory_items_company_item_name')
            self.assertEqual(db.scalar(select(func.count()).select_from(InventoryItem)), 0)

    def test_existing_invalid_input_rejection(self):
        self._build()
        with self.assertRaises(ValueError):
            self._mapped({'item_name': '  '})
        with self.assertRaises(ValidationError):
            self._mapped({'item_name': 'x' * 201})
        with self.assertRaises(ValidationError):
            InventoryItemCreate(item_name='Synthetic', quantity=-1)
        # Existing mapper does not support non-finite quantities; no new fallback.
        with self.assertRaises(OverflowError):
            self._mapped({'item_name': 'Synthetic', 'quantity': 'inf'})

    def test_mapping_failure_after_insert_rolls_back_batch(self):
        service = self._build()
        with Session(self.engine) as db:
            with self.assertRaises(ValueError):
                with db.begin():
                    service.create_item(db, uuid4(), self._mapped({'item_name': 'Synthetic'}))
                    self._mapped({'item_name': ''})
            self.assertEqual(db.scalar(select(func.count()).select_from(InventoryItem)), 0)

    def test_generated_reference_and_missing_reference_database_integrity(self):
        service = self._build()
        company = uuid4()
        with Session(self.engine) as db, db.begin():
            item = service.create_item(db, company, self._mapped({'item_name': 'Synthetic'}))
            # Synthetic relational fixture only, not a historical movement import policy.
            db.add(InventoryTransaction(company_id=company, inventory_item_id=item.id,
                                        transaction_type='IN', quantity=1))
            db.flush()
        with Session(self.engine) as db:
            with self.assertRaises(IntegrityError) as failure:
                with db.begin():
                    db.add(InventoryTransaction(company_id=company, inventory_item_id=uuid4(),
                                                transaction_type='IN', quantity=1))
                    db.flush()
            self.assertEqual(failure.exception.orig.sqlstate, '23503')
            self.assertEqual(db.scalar(select(func.count()).select_from(InventoryTransaction)), 1)

    def test_rehearsal_leaves_verified_migration_history_unchanged(self):
        service = self._build()
        before = self._rows()
        with Session(self.engine) as db, db.begin():
            service.create_item(db, uuid4(), self._mapped({'item_name': 'Synthetic'}))
        self.assertEqual(self._apply(fixture.ROOT / 'migrations').count('SKIP:'), 14)
        self.assertEqual(self._rows(), before)


if __name__ == '__main__':
    unittest.main()
