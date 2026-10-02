"""Accepted financial API semantics on disposable migrated PostgreSQL only."""
from decimal import Decimal
import unittest
from uuid import uuid4
import test_task73_postgresql_repositories as fixture
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.api.v1 import router
from backend.core.database import get_db
from backend.core.security import create_access_token, hash_password
from backend.main import app as accepted_app
from backend.models.company import Company
from backend.models.user import User


class Task76PostgreSQLFinancial(unittest.TestCase):
    _drop = fixture.Task73PostgreSQLRepositories._drop
    _apply = fixture.Task73PostgreSQLRepositories._apply
    _rows = fixture.Task73PostgreSQLRepositories._rows

    def setUp(self):
        fixture.Task73PostgreSQLRepositories.setUp(self)
        password_hash = hash_password('Synthetic-financial-password-123!')
        identities = []
        with Session(self.engine) as db, db.begin():
            for company, label in [(self.company, 'A'), (self.other, 'B')]:
                organization = Company(id=company, name='Synthetic ' + label, status='active')
                user = User(id=uuid4(), company=organization, email='synthetic-' + label + '@example.invalid',
                            full_name='Synthetic', password_hash=password_hash, role='admin')
                db.add_all([organization, user])
                identities.append(user.id)
        application = FastAPI()
        application.exception_handlers.update(accepted_app.exception_handlers)
        application.include_router(router, prefix='/api/v1')
        def override_db():
            with Session(self.engine) as db:
                yield db
        application.dependency_overrides[get_db] = override_db
        self.client = TestClient(application, raise_server_exceptions=False)
        self.addCleanup(self.client.close)
        self.headers, self.other_headers = [{'Authorization': 'Bearer ' + create_access_token(str(user))} for user in identities]
        self.customer = self._post('customers', {'name': 'Synthetic Customer'})['id']

    def _post(self, resource, data, headers=None):
        response = self.client.post('/api/v1/' + resource, headers=headers or self.headers, json=data)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _get(self, resource, headers=None, **params):
        response = self.client.get('/api/v1/' + resource, headers=headers or self.headers, params=params)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def _invoice(self, number, **values):
        return self._post('invoices', {'customer_id': self.customer, 'invoice_number': number,
                                     'issue_date': '2026-01-15', **values})

    def test_invoice_absent_explicit_zero_floor_and_patch_totals(self):
        calculated = self._invoice('SYN-CALC', subtotal='0.30', discount='0.10', tax='0.20')
        self.assertEqual(Decimal(calculated['total']), Decimal('0.40'))
        explicit = self._invoice('SYN-ZERO', subtotal='100', total='0')
        self.assertEqual(Decimal(explicit['total']), Decimal('0'))
        floored = self._invoice('SYN-FLOOR', subtotal='1', discount='2')
        self.assertEqual(Decimal(floored['total']), Decimal('0'))
        response = self.client.patch('/api/v1/invoices/' + calculated['id'], headers=self.headers, json={'subtotal': '100'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(Decimal(response.json()['total']), Decimal('0.40'))

    def test_reporting_status_populations_and_inclusive_dates(self):
        for status, amount in [('Sent', '10'), ('Paid', '20'), ('Overdue', '30'),
                               ('Draft', '40'), ('Cancelled', '50'), ('Deleted', '60')]:
            self._invoice('SYN-' + status, status=status, total=amount, paid_amount='1')
        for status, amount in [('Active', '10'), ('Inactive', '20'), ('Cancelled', '30'), ('Deleted', '40')]:
            self._post('expenses', {'category': 'Synthetic', 'amount': amount, 'status': status, 'expense_date': '2026-01-15'})
        report = self._get('profitability/summary', start_date='2026-01-15', end_date='2026-01-15')
        self.assertEqual((Decimal(report['invoiced_revenue']), Decimal(report['collected_revenue']),
                          Decimal(report['expenses']), Decimal(report['net_profit']), Decimal(report['cash_net_profit'])),
                         (Decimal('60'), Decimal('3'), Decimal('10'), Decimal('50'), Decimal('-7')))
        self.assertEqual((report['invoice_count'], report['expense_count']), (3, 1))
        self.assertEqual(Decimal(self._get('expenses/summary')['total_amount']), Decimal('60'))
        breakdown = self._get('profitability/expenses')
        self.assertEqual([(row['category'], Decimal(row['amount'])) for row in breakdown], [('Synthetic', Decimal('10'))])
        empty = self._get('profitability/summary', start_date='2026-01-16')
        self.assertEqual((empty['invoice_count'], empty['expense_count'], Decimal(empty['net_profit'])), (0, 0, Decimal('0')))

    def test_foreign_financial_mutations_and_reports_remain_isolated(self):
        invoice = self._invoice('SYN-OWN', status='Sent', total='10')
        expense = self._post('expenses', {'category': 'Synthetic', 'amount': '2', 'expense_date': '2026-01-15'})
        for resource, row in [('invoices', invoice), ('expenses', expense)]:
            for method, kwargs in [('get', {}), ('patch', {'json': {'notes': 'Denied'}}), ('delete', {})]:
                with self.subTest(resource=resource, method=method):
                    response = getattr(self.client, method)('/api/v1/' + resource + '/' + row['id'],
                                                           headers=self.other_headers, **kwargs)
                    self.assertEqual(response.status_code, 404, response.text)
        report = self._get('profitability/summary', self.other_headers)
        self.assertEqual((report['invoice_count'], report['expense_count']), (0, 0))
        self.assertEqual(Decimal(self._get('profitability/summary')['net_profit']), Decimal('8'))

    def test_real_invoice_duplicate_is_409_and_following_write_succeeds(self):
        self._invoice('SYN-DUPLICATE')
        response = self.client.post('/api/v1/invoices', headers=self.headers,
            json={'customer_id': self.customer, 'invoice_number': 'SYN-DUPLICATE', 'issue_date': '2026-01-15'})
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json(), {'detail': 'An invoice with this number already exists.'})
        self._invoice('SYN-FOLLOWING')
        self.assertEqual(len(self._get('invoices')), 2)

    def test_invalid_expense_patch_is_rejected_without_data_or_ledger_change(self):
        row = self._post('expenses', {'category': 'Synthetic', 'amount': '1.25', 'expense_date': '2026-01-15'})
        history = self._rows()
        response = self.client.patch('/api/v1/expenses/' + row['id'], headers=self.headers, json={'amount': '-1'})
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(Decimal(self._get('expenses/' + row['id'])['amount']), Decimal('1.25'))
        self.assertEqual(self._rows(), history)


if __name__ == '__main__':
    unittest.main()
