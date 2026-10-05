"""Synthetic API journeys through accepted linked domains, without new semantics."""
from decimal import Decimal
import unittest
from uuid import uuid4
import test_task49_authentication_context as fixture
from backend.core.security import create_access_token
from backend.models.user import User


class Task74CoreWorkflows(unittest.TestCase):
    setUpClass = classmethod(fixture.Task49AuthenticationContextTests.setUpClass.__func__)
    tearDownClass = classmethod(fixture.Task49AuthenticationContextTests.tearDownClass.__func__)
    setUp = fixture.Task49AuthenticationContextTests.setUp

    def _post(self, resource, data):
        response = self.client.post('/api/v1/' + resource,
            headers={'Authorization': 'Bearer ' + self.token}, json=data)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _get(self, resource, token=None):
        response = self.client.get('/api/v1/' + resource,
            headers={'Authorization': 'Bearer ' + (token or self.token)})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def _journey(self):
        customer = self._post('customers', {'name': 'Synthetic Journey'})
        asset = self._post('assets', {'customer_id': customer['id'], 'asset_type': 'Synthetic Filter'})
        request = self._post('service-requests', {'customer_id': customer['id'], 'asset_id': asset['id'], 'title': 'Synthetic Request'})
        order = self._post('work-orders', {'customer_id': customer['id'], 'asset_id': asset['id'],
                                           'service_request_id': request['id'], 'title': 'Synthetic Order'})
        schedule = self._post('schedules', {'work_order_id': order['id'], 'start_at': '2026-01-15T10:00:00+02:00',
                                           'end_at': '2026-01-15T11:00:00+02:00'})
        visit = self._post('service-visits', {'work_order_id': order['id'], 'customer_id': customer['id'],
                                            'asset_id': asset['id'], 'schedule_id': schedule['id']})
        return customer, asset, request, order, schedule, visit

    def test_complete_service_and_billing_journey_has_explicit_history_and_reporting(self):
        customer, asset, request, order, schedule, visit = self._journey()
        response = self.client.patch('/api/v1/service-visits/' + visit['id'],
            headers={'Authorization': 'Bearer ' + self.token}, json={'status': 'Completed',
                'actual_start_at': '2026-01-15T10:05:00+02:00', 'actual_end_at': '2026-01-15T10:45:00+02:00'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self._get('work-orders/' + order['id'])['status'], 'Open')
        self.assertEqual(len([h for h in self._get('service-history') if h['service_visit_id'] == visit['id']]), 1)
        response = self.client.patch('/api/v1/work-orders/' + order['id'],
            headers={'Authorization': 'Bearer ' + self.token}, json={'status': 'Completed'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self._get('work-orders/' + order['id'])['status'], 'Completed')
        history = self._post('service-history', {'customer_id': customer['id'], 'asset_id': asset['id'],
            'work_order_id': order['id'], 'service_visit_id': visit['id'], 'service_type': 'Synthetic Service',
            'service_date': '2026-01-15T10:45:00', 'summary': 'Explicit synthetic history'})
        invoice = self._post('invoices', {'customer_id': customer['id'], 'work_order_id': order['id'],
            'invoice_number': 'SYN-JOURNEY', 'issue_date': '2026-01-15', 'status': 'Sent',
            'subtotal': '100.25', 'discount': '10.00', 'tax': '5.00', 'paid_amount': '20.00'})
        self.assertEqual(Decimal(invoice['total']), Decimal('95.25'))
        self._post('expenses', {'category': 'Synthetic Travel', 'amount': '5.25', 'expense_date': '2026-01-15'})
        report = self._get('profitability/summary')
        self.assertEqual((Decimal(report['net_profit']), Decimal(report['cash_net_profit'])),
                         (Decimal('90.00'), Decimal('14.75')))
        self.assertEqual(self._get('service-history/' + history['id'])['service_visit_id'], visit['id'])
        self.assertEqual(self._get('service-visits/' + visit['id'])['schedule_id'], schedule['id'])
        self.assertEqual(self._get('work-orders/' + order['id'])['service_request_id'], request['id'])
        self.assertEqual(self._get('notifications'), [])
        self.assertEqual(self._get('audit-logs'), [])

    def test_invalid_schedule_link_creates_no_partial_visit_and_existing_journey_survives(self):
        customer, _, _, order, _, visit = self._journey()
        before = self._get('service-visits')
        response = self.client.post('/api/v1/service-visits', headers={'Authorization': 'Bearer ' + self.token},
            json={'customer_id': customer['id'], 'work_order_id': order['id'], 'schedule_id': str(uuid4())})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json(), {'detail': 'Schedule not found.'})
        self.assertEqual(self._get('service-visits'), before)
        self.assertEqual(self._get('work-orders/' + order['id'])['status'], 'Open')
        self.assertEqual(self._get('service-visits/' + visit['id'])['status'], 'Planned')

    def test_linked_journey_is_invisible_to_other_tenant(self):
        rows = self._journey()
        with self.Session() as db:
            db.get(User, self.other_user_id).role = 'admin'
            db.commit()
        other = create_access_token(str(self.other_user_id))
        for resource, row in zip(['customers', 'assets', 'service-requests', 'work-orders', 'schedules', 'service-visits'], rows):
            with self.subTest(resource=resource):
                self.assertEqual(self._get(resource, other), [])
                response = self.client.get('/api/v1/' + resource + '/' + row['id'],
                                           headers={'Authorization': 'Bearer ' + other})
                self.assertEqual(response.status_code, 404, response.text)


if __name__ == '__main__':
    unittest.main()
