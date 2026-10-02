"""Synthetic operator first-use of existing UI against the actual local API/PG."""
from decimal import Decimal
import shutil
import unittest
from uuid import uuid4
from sqlalchemy.orm import Session
import test_task86_deployment_rehearsal as rehearsal
from backend.core.security import hash_password
from backend.models.company import Company
from backend.models.user import User


class Task89FirstUse(unittest.TestCase):
    setUp = rehearsal.Task86DeploymentRehearsal.setUp
    _drop = rehearsal.Task86DeploymentRehearsal._drop
    _rows = rehearsal.Task86DeploymentRehearsal._rows
    _command = rehearsal.Task86DeploymentRehearsal._command
    _migrate = rehearsal.Task86DeploymentRehearsal._migrate
    _start = rehearsal.Task86DeploymentRehearsal._start

    def test_synthetic_operator_navigation_entry_logout_and_reentry(self):
        self.assertEqual(self._migrate().count('  OK:'), 13)
        before = self._rows()
        with Session(self.engine) as db, db.begin():
            company = Company(id=uuid4(), name='Synthetic First Use', status='active')
            user = User(id=uuid4(), company=company, email='first-use@example.invalid',
                full_name='Synthetic Operator', password_hash=hash_password('synthetic-first-use-password'), role='admin')
            db.add_all([company, user])
        base, process, output, stop = self._start(1)
        logo = self.directory / 'assets/images/logo.png'
        logo.parent.mkdir(parents=True)
        shutil.copyfile(rehearsal.fixture.ROOT / 'assets/images/logo.png', logo)
        ui = self._command(['-c', '''
import os
from pathlib import Path
from streamlit.testing.v1 import AppTest
app = AppTest.from_file(str(Path(os.environ['PYTHONPATH']) / 'app.py')).run(timeout=20)
def field(kind, label):
    return next(widget for widget in getattr(app, kind) if widget.label == label)
def submit(label):
    field('button', label).click().run(timeout=20)
    assert not app.exception, 'Unexpected UI exception'
def page(name):
    app.sidebar.radio[0].set_value(name).run(timeout=20)
    assert not app.exception, 'Module failed: ' + name
    assert not app.error, 'API/UI error: ' + name
def login():
    app.text_input[0].set_value('first-use@example.invalid')
    app.text_input[1].set_value('synthetic-first-use-password')
    submit('Login')
    assert app.session_state['user_type'] == 'admin'
login()
expected = ['Dashboard', 'Customers', 'Maintenance', 'Inventory', 'Expenses', 'Invoices', 'Profitability', 'Store']
assert list(app.sidebar.radio[0].options) == expected
for name in expected:
    page(name)
page('Customers')
submit('Save Customer')
assert any(error.value == 'Name is required.' for error in app.error)
field('text_input', 'Name *').set_value('Synthetic First Customer')
submit('Save Customer')
assert not app.error
page('Maintenance')
field('text_input', 'Title *').set_value('Synthetic First Order')
submit('Create')
assert not app.error
submit('Save visit')
assert not app.error
page('Inventory')
field('text_input', 'Item name *').set_value('Synthetic First Part')
field('number_input', 'Quantity').set_value(3)
field('number_input', 'Cost price').set_value(2.5)
submit('Save')
assert not app.error
page('Invoices')
field('text_input', 'Invoice number *').set_value('SYN-FIRST-USE')
field('number_input', 'Subtotal').set_value(10.0)
field('number_input', 'Discount').set_value(1.0)
field('number_input', 'Tax').set_value(2.0)
field('number_input', 'Paid amount').set_value(3.0)
submit('Save invoice')
assert not app.error
page('Expenses')
field('text_input', 'Category *').set_value('Synthetic Travel')
field('number_input', 'Amount').set_value(2.0)
submit('Save')
assert not app.error
for name in expected:
    page(name)
submit('Logout')
assert app.session_state['user_type'] is None
login()
page('Customers')
assert any(metric.label == 'Customers' and str(metric.value) == '1' for metric in app.metric)
page('Inventory')
assert any(metric.label == 'Items' and str(metric.value) == '1' for metric in app.metric)
print('FIRST_USE_PASSED')
'''], {**self.environment, 'AXYREL_API_BASE_URL': base})
        self.assertEqual(ui.returncode, 0, ui.stderr)
        self.assertIn('FIRST_USE_PASSED', ui.stdout)
        login = self.http.post(base + '/api/v1/auth/login',
            data={'username': 'first-use@example.invalid', 'password': 'synthetic-first-use-password'}, timeout=8)
        self.assertEqual(login.status_code, 200)
        headers = {'Authorization': 'Bearer ' + login.json()['access_token']}
        def read(resource):
            response = self.http.get(base + '/api/v1/' + resource, headers=headers, timeout=8)
            self.assertEqual(response.status_code, 200)
            return response.json()
        for resource in ['customers', 'work-orders', 'service-visits', 'inventory', 'invoices', 'expenses']:
            self.assertEqual(len(read(resource)), 1, resource)
        self.assertEqual(read('customers')[0]['name'], 'Synthetic First Customer')
        invoice = read('invoices')[0]
        self.assertEqual((invoice['status'], Decimal(invoice['total'])), ('Draft', Decimal('11')))
        self.assertEqual(Decimal(read('inventory/summary')['total_stock_value']), Decimal('7.50'))
        report = read('profitability/summary')
        self.assertEqual((Decimal(report['invoiced_revenue']), Decimal(report['expenses']), Decimal(report['net_profit'])),
                         (Decimal('0'), Decimal('2'), Decimal('-2')))
        self.assertEqual(read('notifications'), [])
        self.assertEqual(read('audit-logs'), [])
        self.assertEqual(self._rows(), before)
        stop()
        self.assertEqual(process.returncode, 0)


if __name__ == '__main__':
    unittest.main()
