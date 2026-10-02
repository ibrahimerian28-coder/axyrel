"""OD-27 real local HTTP smoke, synthetic tenants and tracked disposable PostgreSQL."""
from decimal import Decimal
from pathlib import Path
import shutil
import unittest
from uuid import uuid4
from sqlalchemy.orm import Session
import test_task86_deployment_rehearsal as rehearsal
from backend.core.security import hash_password
from backend.models.company import Company
from backend.models.user import User


class Task87ProductionSmoke(unittest.TestCase):
    setUp = rehearsal.Task86DeploymentRehearsal.setUp
    _drop = rehearsal.Task86DeploymentRehearsal._drop
    _rows = rehearsal.Task86DeploymentRehearsal._rows
    _command = rehearsal.Task86DeploymentRehearsal._command
    _migrate = rehearsal.Task86DeploymentRehearsal._migrate
    _start = rehearsal.Task86DeploymentRehearsal._start
    test_security_configuration_refuses_startup = rehearsal.Task86DeploymentRehearsal.test_invalid_production_configuration_prevents_deployment_startup

    def _request(self, method, resource, expected=200, headers=None, **kwargs):
        response = self.http.request(method, self.base + '/api/v1/' + resource,
            headers=headers or self.headers, timeout=8, **kwargs)
        self.assertEqual(response.status_code, expected, resource)
        return response.json()

    def _post(self, resource, data):
        return self._request('POST', resource, 201, json=data)

    def _login(self, label):
        response = self.http.post(self.base + '/api/v1/auth/login',
            data={'username': 'smoke-' + label + '@example.invalid', 'password': 'synthetic-smoke-password'}, timeout=8)
        self.assertEqual(response.status_code, 200)
        return {'Authorization': 'Bearer ' + response.json()['access_token']}

    def test_ui_api_workflows_tenants_and_restart_persistence(self):
        self.assertEqual(self._migrate().count('  OK:'), 13)
        history = self._rows()
        identities = {}
        password_hash = hash_password('synthetic-smoke-password')
        with Session(self.engine) as db, db.begin():
            for label in ['owner', 'other']:
                company = Company(id=uuid4(), name='Synthetic Smoke ' + label, status='active')
                user = User(id=uuid4(), company=company, email='smoke-' + label + '@example.invalid',
                    full_name='Synthetic Smoke', password_hash=password_hash, role='admin')
                db.add_all([company, user])
                identities[label] = str(user.id)
        self.base, process, output, stop = self._start(1)
        self.assertEqual(self.http.get(self.base + '/api/v1/customers', timeout=8).status_code, 401)
        invalid = self.http.post(self.base + '/api/v1/auth/login',
            data={'username': 'smoke-owner@example.invalid', 'password': 'wrong-synthetic-password'}, timeout=8)
        self.assertEqual(invalid.status_code, 401)
        self.headers, other_headers = self._login('owner'), self._login('other')
        self.assertEqual(self._request('GET', 'auth/me')['id'], identities['owner'])
        customer = self._post('customers', {'name': 'Synthetic Smoke Customer'})
        asset = self._post('assets', {'customer_id': customer['id'], 'asset_type': 'Synthetic Filter'})
        request = self._post('service-requests', {'customer_id': customer['id'], 'asset_id': asset['id'], 'title': 'Synthetic Request'})
        order = self._post('work-orders', {'customer_id': customer['id'], 'asset_id': asset['id'],
            'service_request_id': request['id'], 'title': 'Synthetic Order'})
        schedule = self._post('schedules', {'work_order_id': order['id'],
            'start_at': '2026-01-15T10:00:00+02:00', 'end_at': '2026-01-15T11:00:00+02:00'})
        visit = self._post('service-visits', {'work_order_id': order['id'], 'customer_id': customer['id'],
            'asset_id': asset['id'], 'schedule_id': schedule['id']})
        self._request('PATCH', 'service-visits/' + visit['id'], json={'status': 'Completed',
            'actual_start_at': '2026-01-15T10:05:00+02:00', 'actual_end_at': '2026-01-15T10:45:00+02:00'})
        self.assertEqual(self._request('GET', 'work-orders/' + order['id'])['status'], 'Completed')
        history_row = self._post('service-history', {'customer_id': customer['id'], 'asset_id': asset['id'],
            'work_order_id': order['id'], 'service_visit_id': visit['id'], 'service_type': 'Synthetic',
            'service_date': '2026-01-15T10:45:00', 'summary': 'Explicit synthetic history'})
        item = self._post('inventory', {'item_name': 'Synthetic Smoke Part', 'quantity': 3, 'cost_price': '2.50'})
        movement = self._post('inventory-transactions', {'inventory_item_id': item['id'],
            'transaction_type': 'IN', 'quantity': 2, 'reference_type': 'SYNTHETIC'})
        self.assertEqual(self._request('GET', 'inventory/' + item['id'])['quantity'], 3)
        self.assertEqual(Decimal(self._request('GET', 'inventory/summary')['total_stock_value']), Decimal('7.50'))
        invoice = self._post('invoices', {'customer_id': customer['id'], 'work_order_id': order['id'],
            'invoice_number': 'SYN-SMOKE', 'issue_date': '2026-01-15', 'status': 'Sent',
            'subtotal': '100.25', 'discount': '10', 'tax': '5', 'paid_amount': '20'})
        self.assertEqual(Decimal(invoice['total']), Decimal('95.25'))
        expense = self._post('expenses', {'category': 'Synthetic Travel', 'amount': '5.25', 'expense_date': '2026-01-15'})
        summary = self._request('GET', 'profitability/summary')
        self.assertEqual((Decimal(summary['net_profit']), Decimal(summary['cash_net_profit'])),
                         (Decimal('90.00'), Decimal('14.75')))
        owned = [('customers', customer), ('assets', asset), ('work-orders', order),
                 ('schedules', schedule), ('service-visits', visit), ('service-history', history_row),
                 ('inventory', item), ('inventory-transactions', movement), ('invoices', invoice), ('expenses', expense)]
        for resource, row in owned:
            self.assertEqual(self._request('GET', resource, headers=other_headers), [])
            self._request('GET', resource + '/' + row['id'], 404, headers=other_headers)
        self._request('PATCH', 'customers/' + customer['id'], 404, headers=other_headers, json={'name': 'Denied'})
        self.assertEqual(self._request('GET', 'customers/' + customer['id'])['name'], 'Synthetic Smoke Customer')
        self.assertEqual(self._request('GET', 'notifications'), [])
        self.assertEqual(self._request('GET', 'audit-logs'), [])
        # Preserve the accepted UI's relative asset path in the isolated working directory.
        logo = self.directory / 'assets/images/logo.png'
        logo.parent.mkdir(parents=True)
        shutil.copyfile(rehearsal.fixture.ROOT / 'assets/images/logo.png', logo)
        ui = self._command(['-c', '''
import os
from pathlib import Path
from streamlit.testing.v1 import AppTest
app = AppTest.from_file(str(Path(os.environ['PYTHONPATH']) / 'app.py')).run(timeout=20)
app.text_input[0].set_value('smoke-owner@example.invalid')
app.text_input[1].set_value('synthetic-smoke-password')
app.button[0].click().run(timeout=20)
assert not app.exception, 'UI login/render failed'
assert app.session_state['user_type'] == 'admin', 'UI authentication missing'
print('UI_LOGIN_OK')
'''], {**self.environment, 'AXYREL_API_BASE_URL': self.base})
        self.assertEqual(ui.returncode, 0, 'Synthetic UI login smoke failed')
        self.assertIn('UI_LOGIN_OK', ui.stdout)
        stop()
        self.assertEqual(process.returncode, 0)
        self.assertEqual(self._migrate().count('SKIP:'), 13)
        self.base, process, output, stop = self._start(2)
        self.headers = self._login('owner')
        for resource, row in owned:
            self.assertEqual(self._request('GET', resource + '/' + row['id'])['id'], row['id'])
        self.assertEqual(self._request('GET', 'profitability/summary'), summary)
        self.assertEqual(self._request('GET', 'service-visits/' + visit['id'])['status'], 'Completed')
        self.assertEqual(self._request('GET', 'inventory/' + item['id'])['quantity'], 3)
        stop()
        self.assertEqual(process.returncode, 0)
        output.seek(0)
        logs = output.read()
        self.assertIn('ORDERLY_SHUTDOWN', logs)
        self.assertNotIn(self.environment['SECRET_KEY'], logs)
        self.assertNotIn(self.environment['DATABASE_URL'], logs)
        self.assertEqual(self._rows(), history)


if __name__ == '__main__':
    unittest.main()
