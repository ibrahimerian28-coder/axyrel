"""OD-23 independent expected outcomes for the OD-22 synthetic rehearsal."""
import unittest
from decimal import Decimal
from uuid import UUID

import test_task62_migration_rehearsal as rehearsal
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.models.inventory_transaction import InventoryTransaction


class Task63SyntheticValidationTests(unittest.TestCase):
    setUp = rehearsal.Task62MigrationRehearsalTests.setUp
    _drop = rehearsal.Task62MigrationRehearsalTests._drop
    _apply = rehearsal.Task62MigrationRehearsalTests._apply
    _rows = rehearsal.Task62MigrationRehearsalTests._rows
    _build = rehearsal.Task62MigrationRehearsalTests._build
    _mapped = rehearsal.Task62MigrationRehearsalTests._mapped

    def test_documented_source_to_target_outcomes_and_tenant_partition(self):
        service = self._build()
        company = UUID('10000000-0000-0000-0000-000000000001')
        other = UUID('10000000-0000-0000-0000-000000000002')
        rows = [
            (company, dict(item_name='  Synthetic Filter  ', quantity='7', min_limit='2',
                           ideal_stock='12', cost_price='15.25')),
            (company, dict(item_name='Synthetic Defaults')),
            (company, dict(item_name='Synthetic Coercions', quantity='3.9', min_limit=-2,
                           ideal_stock='bad', cost_price='bad', status='Deleted', id='legacy-id',
                           company_id=str(other))),
            (other, dict(item_name='Synthetic Filter', quantity=1, cost_price='2.00')),
        ]
        # Expected values are literals from the documented contract, not mapper output.
        expected = [
            (company, 'Synthetic Coercions', 3, 0, 0, Decimal('0.00'), 'Active'),
            (company, 'Synthetic Defaults', 0, 0, 0, Decimal('0.00'), 'Active'),
            (company, 'Synthetic Filter', 7, 2, 12, Decimal('15.25'), 'Active'),
            (other, 'Synthetic Filter', 1, 0, 0, Decimal('2.00'), 'Active'),
        ]
        with Session(self.engine) as db, db.begin():
            for tenant, row in rows:
                service.create_item(db, tenant, self._mapped(row))
        with self.engine.connect() as db:
            actual = db.execute(text('SELECT company_id, item_name, quantity, min_limit, '
                                     'ideal_stock, cost_price, status FROM inventory_items '
                                     'ORDER BY company_id, item_name')).all()
            self.assertEqual([tuple(row) for row in actual], expected)
        with Session(self.engine) as db:
            self.assertEqual(len(service.list_items(db, company)), 3)
            self.assertEqual(len(service.list_items(db, other)), 1)

    def test_repeat_rehearsal_preserves_values_but_generates_new_ids(self):
        service = self._build()
        row = dict(item_name=' Synthetic Repeat ', quantity='4', cost_price='3.50')
        results, identifiers = [], []
        with Session(self.engine) as db, db.begin():
            for suffix in (1, 2):
                company = UUID(f'20000000-0000-0000-0000-{suffix:012d}')
                item = service.create_item(db, company, self._mapped(row))
                identifiers.append(item.id)
                results.append((item.item_name, item.quantity, item.cost_price, item.status))
        self.assertEqual(results, [('Synthetic Repeat', 4, Decimal('3.50'), 'Active')] * 2)
        self.assertNotEqual(identifiers[0], identifiers[1])

    def test_reference_join_has_no_missing_or_cross_tenant_synthetic_links(self):
        service = self._build()
        company = UUID('30000000-0000-0000-0000-000000000001')
        with Session(self.engine) as db, db.begin():
            item = service.create_item(db, company, self._mapped({'item_name': 'Synthetic Link'}))
            db.add(InventoryTransaction(company_id=company, inventory_item_id=item.id,
                                        transaction_type='IN', quantity=1))
        with self.engine.connect() as db:
            rows = db.execute(text('SELECT t.company_id, i.company_id, i.item_name, t.quantity '
                                   'FROM inventory_transactions t JOIN inventory_items i '
                                   'ON i.id=t.inventory_item_id')).all()
            self.assertEqual([tuple(row) for row in rows], [(company, company, 'Synthetic Link', 1)])
            self.assertEqual(db.execute(text('SELECT count(*) FROM inventory_transactions t '
                                             'LEFT JOIN inventory_items i ON i.id=t.inventory_item_id '
                                             'WHERE i.id IS NULL')).scalar_one(), 0)
        # This validates fixture integrity, not a new cross-tenant SQL constraint.


if __name__ == '__main__':
    unittest.main()
