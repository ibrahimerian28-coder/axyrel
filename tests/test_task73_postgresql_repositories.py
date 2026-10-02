"""Repository and real conflict behavior on tracked disposable PostgreSQL."""
from datetime import date
from decimal import Decimal
import unittest
from uuid import uuid4

import test_task60_tracked_migrations as fixture
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import create_access_token, hash_password
from backend.api.v1 import router
from backend.main import app as accepted_app
from backend.models.company import Company
from backend.models.user import User
from backend.models.inventory_item import InventoryItem
from backend.repositories.inventory import InventoryRepository
from backend.repositories.customer import CustomerRepository
from backend.repositories.invoice import InvoiceRepository
from backend.repositories.expense import ExpenseRepository
from backend.repositories.profitability import ProfitabilityRepository
from backend.repositories.notification import NotificationRepository
from backend.services.expense import ExpenseService


class Task73PostgreSQLRepositories(unittest.TestCase):
    _drop = fixture.Task60TrackedMigrationTests._drop
    _apply = fixture.Task60TrackedMigrationTests._apply
    _rows = fixture.Task60TrackedMigrationTests._rows

    def setUp(self):
        fixture.Task60TrackedMigrationTests.setUp(self)
        self._apply(fixture.ROOT / 'migrations')
        self.company, self.other = uuid4(), uuid4()

    def test_inventory_scope_mutation_and_soft_delete(self):
        repository = InventoryRepository()
        with Session(self.engine) as db, db.begin():
            item = repository.create(db, self.company, {'item_name': 'Synthetic', 'quantity': 3})
            identifier = item.id
        with Session(self.engine) as db, db.begin():
            self.assertIsNone(repository.get(db, self.other, identifier))
            self.assertIsNone(repository.update(db, self.other, identifier, {'quantity': 99}))
            self.assertIsNone(repository.soft_delete(db, self.other, identifier))
            self.assertEqual(repository.get(db, self.company, identifier).quantity, 3)
            repository.soft_delete(db, self.company, identifier)
            self.assertIsNone(repository.get(db, self.company, identifier))
            self.assertEqual(repository.list(db, self.company), [])

    def test_missing_scope_fails_before_reads_or_writes(self):
        with Session(self.engine) as db:
            for repository in [InventoryRepository(), CustomerRepository(), InvoiceRepository(),
                               ExpenseRepository(), NotificationRepository()]:
                with self.subTest(repository=type(repository).__name__):
                    with self.assertRaises(ValueError):
                        repository.list(db, None)
                    with self.assertRaises(ValueError):
                        repository.create(db, None, {})
            self.assertEqual(db.scalar(select(func.count()).select_from(InventoryItem)), 0)

    def test_customer_display_ids_are_allocated_within_company(self):
        repository = CustomerRepository()
        with Session(self.engine) as db, db.begin():
            first = repository.create(db, self.company, {'name': 'Synthetic First'})
            second = repository.create(db, self.company, {'name': 'Synthetic Second'})
            other = repository.create(db, self.other, {'name': 'Synthetic Other'})
            self.assertEqual((first.display_id, second.display_id, other.display_id), (1001, 1002, 1001))
            self.assertEqual([c.name for c in repository.list(db, self.company, search='second')], ['Synthetic Second'])

    def test_invoice_decimal_persistence_and_company_number_uniqueness(self):
        invoices, customers = InvoiceRepository(), CustomerRepository()
        with Session(self.engine) as db, db.begin():
            customer = customers.create(db, self.company, {'name': 'Synthetic'})
            other_customer = customers.create(db, self.other, {'name': 'Other Synthetic'})
            payload = dict(customer_id=customer.id, invoice_number='SYN-1', issue_date=date(2026, 1, 1),
                           total=Decimal('0.30'), paid_amount=Decimal('0.10'), status='Sent')
            record = invoices.create(db, self.company, payload)
            identifier = record.id
            with self.assertRaises(IntegrityError) as duplicate:
                with db.begin_nested():
                    invoices.create(db, self.company, payload)
            self.assertEqual(duplicate.exception.orig.sqlstate, '23505')
            self.assertEqual(duplicate.exception.orig.diag.constraint_name, 'uq_invoices_company_number')
            invoices.create(db, self.other, {**payload, 'customer_id': other_customer.id})
        with Session(self.engine) as db:
            record = invoices.get(db, self.company, identifier)
            self.assertEqual((record.total, record.paid_amount), (Decimal('0.30'), Decimal('0.10')))
            self.assertIsNone(invoices.get(db, self.other, identifier))

    def test_reporting_preserves_distinct_expense_populations_and_date_bounds(self):
        expenses, profitability = ExpenseRepository(), ProfitabilityRepository()
        day = date(2026, 1, 15)
        with Session(self.engine) as db, db.begin():
            for status, amount in [('Active', '10.25'), ('Inactive', '20.00'), ('Deleted', '30.00')]:
                expenses.create(db, self.company, dict(category='Synthetic', amount=Decimal(amount),
                                                       expense_date=day, status=status))
            expenses.create(db, self.other, dict(category='Synthetic', amount=Decimal('100.00'),
                                                 expense_date=day, status='Active'))
        with Session(self.engine) as db:
            self.assertEqual(tuple(profitability.expense_totals(db, self.company, day, day)), (Decimal('10.25'), 1))
            self.assertEqual(tuple(profitability.expense_totals(db, self.company, date(2026, 1, 16))), (Decimal('0'), 0))
            self.assertEqual(ExpenseService(expenses).get_summary(db, self.company).total_amount, Decimal('30.25'))

    def test_notification_read_state_and_tenant_guard_persist(self):
        repository = NotificationRepository()
        with Session(self.engine) as db, db.begin():
            record = repository.create(db, self.company, dict(notification_type='Synthetic', title='Synthetic', message='Synthetic'))
            identifier = record.id
            self.assertIsNone(repository.mark_read(db, self.other, identifier))
            self.assertEqual(record.status, 'unread')
            repository.mark_read(db, self.company, identifier)
        with Session(self.engine) as db:
            record = repository.get(db, self.company, identifier)
            self.assertEqual(record.status, 'read')
            self.assertIsNotNone(record.read_at)

    def test_failed_reference_rolls_back_and_ledger_is_unchanged(self):
        before = self._rows()
        with Session(self.engine) as db:
            with self.assertRaises(IntegrityError) as failure:
                with db.begin():
                    InventoryRepository().create(db, self.company, {'item_name': 'Rollback Synthetic'})
                    InvoiceRepository().create(db, self.company, dict(customer_id=uuid4(), invoice_number='SYN-BAD',
                                                                       issue_date=date(2026, 1, 1)))
            self.assertEqual(failure.exception.orig.sqlstate, '23503')
            self.assertEqual(db.scalar(select(func.count()).select_from(InventoryItem)), 0)
        self.assertEqual(self._rows(), before)

    def test_real_postgresql_unique_error_reaches_api_409_and_next_request_succeeds(self):
        with Session(self.engine) as db, db.begin():
            company = Company(id=self.company, name='Synthetic PostgreSQL', status='active')
            user = User(id=uuid4(), company=company, email='synthetic-pg@example.invalid', full_name='Synthetic',
                        password_hash=hash_password('Synthetic-password-123!'), role='admin')
            db.add_all([company, user])
            identifier = user.id
        application = FastAPI()
        application.exception_handlers.update(accepted_app.exception_handlers)
        application.include_router(router, prefix='/api/v1')
        def override_db():
            with Session(self.engine) as db:
                yield db
        application.dependency_overrides[get_db] = override_db
        headers = {'Authorization': 'Bearer ' + create_access_token(str(identifier))}
        with TestClient(application, raise_server_exceptions=False) as client:
            first = client.post('/api/v1/inventory', headers=headers, json={'item_name': 'Synthetic Duplicate'})
            self.assertEqual(first.status_code, 201, first.text)
            duplicate = client.post('/api/v1/inventory', headers=headers, json={'item_name': 'Synthetic Duplicate'})
            self.assertEqual(duplicate.status_code, 409, duplicate.text)
            self.assertEqual(duplicate.json(), {'detail': 'An inventory item with this name already exists.'})
            following = client.post('/api/v1/inventory', headers=headers, json={'item_name': 'Synthetic Following'})
            self.assertEqual(following.status_code, 201, following.text)
            listed = client.get('/api/v1/inventory', headers=headers)
            self.assertEqual(len(listed.json()), 2)


if __name__ == '__main__':
    unittest.main()
