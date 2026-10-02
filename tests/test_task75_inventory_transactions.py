"""Accepted stock/movement semantics on migrated disposable PostgreSQL."""
import unittest
from unittest.mock import Mock
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
import test_task60_tracked_migrations as fixture
from backend.models.inventory_item import InventoryItem
from backend.models.inventory_transaction import InventoryTransaction
from backend.models.technician_stock import TechnicianStock
from backend.repositories.inventory import InventoryRepository
from backend.services.inventory_rules import InventoryBusinessRules
from backend.services.inventory_transactions import InventoryTransactionService


class Task75InventoryTransactions(unittest.TestCase):
    _drop = fixture.Task60TrackedMigrationTests._drop
    _apply = fixture.Task60TrackedMigrationTests._apply

    def setUp(self):
        fixture.Task60TrackedMigrationTests.setUp(self)
        self._apply(fixture.ROOT / 'migrations')
        self.company, self.other, self.technician = uuid4(), uuid4(), uuid4()
        with Session(self.engine) as db, db.begin():
            self.item = InventoryRepository().create(db, self.company,
                {'item_name': 'Synthetic Stock', 'quantity': 20}).id

    def test_warehouse_add_remove_persist_balances_and_movement_values(self):
        rules = InventoryBusinessRules()
        with Session(self.engine) as db, db.begin():
            rules.add_stock(db, self.company, self.item, 3, reference_type='SYNTHETIC', reference_id='add')
            rules.remove_stock(db, self.company, self.item, 5, reference_type='SYNTHETIC', reference_id='remove')
        with Session(self.engine) as db:
            self.assertEqual(db.get(InventoryItem, self.item).quantity, 18)
            movements = db.scalars(select(InventoryTransaction)).all()
            self.assertEqual({(m.transaction_type, m.quantity, m.reference_id) for m in movements},
                             {('IN', 3, 'add'), ('OUT', 5, 'remove')})

    def test_zero_adjustment_preserves_existing_positive_movement_encoding(self):
        with Session(self.engine) as db, db.begin():
            InventoryBusinessRules().adjust_stock(db, self.company, self.item, 0)
        with Session(self.engine) as db:
            self.assertEqual(db.get(InventoryItem, self.item).quantity, 0)
            movement = db.scalar(select(InventoryTransaction))
            self.assertEqual((movement.transaction_type, movement.quantity, movement.reference_type),
                             ('ADJUSTMENT', 1, 'INVENTORY_ADJUSTMENT'))

    def test_transfer_consume_restore_persist_existing_reference_semantics(self):
        rules = InventoryBusinessRules()
        with Session(self.engine) as db, db.begin():
            rules.transfer_to_technician(db, self.company, self.technician, self.item, 4, reference_id='synthetic-transfer')
            rules.consume_technician_stock(db, self.company, self.technician, self.item, 2,
                                           reference_type='SYNTHETIC', reference_id='consume')
            rules.restore_technician_stock(db, self.company, self.technician, self.item, 2,
                                           reference_type='SYNTHETIC', reference_id='restore')
        with Session(self.engine) as db:
            self.assertEqual(db.get(InventoryItem, self.item).quantity, 16)
            self.assertEqual(db.scalar(select(TechnicianStock)).quantity, 4)
            movements = db.scalars(select(InventoryTransaction)).all()
            self.assertEqual(len(movements), 3)
            self.assertEqual({(m.transaction_type, m.quantity, m.reference_id) for m in movements},
                             {('OUT', 4, 'synthetic-transfer'), ('OUT', 2, 'consume'), ('IN', 2, 'restore')})

    def test_invalid_quantity_insufficient_balance_and_foreign_item_leave_no_movements(self):
        rules = InventoryBusinessRules()
        with Session(self.engine) as db, db.begin():
            for company, quantity in [(self.company, 0), (self.company, -1), (self.company, 21), (self.other, 1)]:
                with self.subTest(company=company, quantity=quantity), self.assertRaises(ValueError):
                    rules.remove_stock(db, company, self.item, quantity)
            self.assertEqual(db.get(InventoryItem, self.item).quantity, 20)
            self.assertEqual(db.scalars(select(InventoryTransaction)).all(), [])

    def test_transfer_failure_rolls_back_flushed_balances_and_new_stock(self):
        transactions = Mock()
        transactions.create.side_effect = RuntimeError('Synthetic movement failure')
        rules = InventoryBusinessRules(transaction_repository=transactions)
        with Session(self.engine) as db:
            with self.assertRaisesRegex(RuntimeError, 'Synthetic movement failure'):
                with db.begin():
                    rules.transfer_to_technician(db, self.company, self.technician, self.item, 4)
            self.assertEqual(db.get(InventoryItem, self.item).quantity, 20)
            self.assertEqual(db.scalars(select(TechnicianStock)).all(), [])
            self.assertEqual(db.scalars(select(InventoryTransaction)).all(), [])

    def test_generic_record_normalization_does_not_change_balance_or_allow_reserved_refs(self):
        service, reference = InventoryTransactionService(), uuid4()
        with Session(self.engine) as db, db.begin():
            row = service.create_transaction(db, self.company, {'inventory_item_id': self.item,
                'transaction_type': ' in ', 'quantity': 1, 'reference_id': reference})
            self.assertEqual((row.transaction_type, row.reference_id), ('IN', str(reference)))
            for value in ['service_visit_install', ' SERVICE_VISIT_REVERSAL ']:
                with self.subTest(reference_type=value), self.assertRaisesRegex(ValueError, 'reserved'):
                    service.create_transaction(db, self.company, {'inventory_item_id': self.item,
                        'transaction_type': 'IN', 'quantity': 1, 'reference_type': value})
            for kind, quantity in [('INVALID', 1), ('IN', 0), ('OUT', -1)]:
                with self.subTest(kind=kind, quantity=quantity), self.assertRaises(ValueError):
                    service.create_transaction(db, self.company, {'inventory_item_id': self.item,
                        'transaction_type': kind, 'quantity': quantity})
        with Session(self.engine) as db:
            self.assertEqual(db.get(InventoryItem, self.item).quantity, 20)
            self.assertEqual(len(db.scalars(select(InventoryTransaction)).all()), 1)


if __name__ == '__main__':
    unittest.main()
