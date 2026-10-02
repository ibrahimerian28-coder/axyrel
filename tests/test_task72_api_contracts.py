"""Accepted API boundaries using the disposable Task 49 application fixture."""
import unittest
from uuid import uuid4
import test_task49_authentication_context as fixture
from backend.core.security import create_access_token
from backend.models.user import User


class Task72APIContracts(unittest.TestCase):
    setUpClass = classmethod(fixture.Task49AuthenticationContextTests.setUpClass.__func__)
    tearDownClass = classmethod(fixture.Task49AuthenticationContextTests.tearDownClass.__func__)
    setUp = fixture.Task49AuthenticationContextTests.setUp

    def headers(self, token=None):
        return {'Authorization': 'Bearer ' + (token or self.token)}

    def test_resource_lists_require_bearer_authentication(self):
        resources = ['customers', 'assets', 'service-requests', 'work-orders', 'schedules',
                     'service-visits', 'service-history', 'inventory', 'inventory-transactions',
                     'technician-stock', 'invoices', 'service-contracts', 'expenses',
                     'notifications', 'audit-logs']
        for resource in resources:
            with self.subTest(resource=resource):
                response = self.client.get('/api/v1/' + resource)
                self.assertEqual(response.status_code, 401, response.text)
                self.assertEqual(response.headers.get('www-authenticate'), 'Bearer')

    def test_inventory_crud_tenant_isolation_and_deleted_visibility(self):
        with self.Session() as db:
            db.get(User, self.other_user_id).role = 'admin'
            db.commit()
        other = self.headers(create_access_token(str(self.other_user_id)))
        own = self.headers()
        response = self.client.post('/api/v1/inventory', headers=own,
                                    json={'item_name': '  Synthetic API Part  ', 'quantity': 4, 'cost_price': '0.10'})
        self.assertEqual(response.status_code, 201, response.text)
        row = response.json()
        self.assertEqual(row['item_name'], 'Synthetic API Part')
        self.assertEqual(row['company_id'], str(self.company_id))
        path = '/api/v1/inventory/' + row['id']
        self.assertEqual(self.client.get('/api/v1/inventory', headers=other).json(), [])
        for method, payload in [('get', {}), ('patch', {'json': {'quantity': 0}}), ('delete', {})]:
            with self.subTest(method=method):
                response = getattr(self.client, method)(path, headers=other, **payload)
                self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(self.client.get(path, headers=own).json()['quantity'], 4)
        patched = self.client.patch(path, headers=own, json={'quantity': 5})
        self.assertEqual(patched.status_code, 200, patched.text)
        self.assertEqual(patched.json()['quantity'], 5)
        summary = self.client.get('/api/v1/inventory/summary', headers=own)
        self.assertEqual(summary.status_code, 200, summary.text)
        self.assertEqual(summary.json()['item_count'], 1)
        self.assertEqual(self.client.delete(path, headers=own).status_code, 204)
        self.assertEqual(self.client.get(path, headers=own).status_code, 404)
        self.assertEqual(self.client.get('/api/v1/inventory', headers=own).json(), [])

    def test_authenticated_invalid_identifiers_are_validation_errors(self):
        for resource in ['customers', 'assets', 'work-orders', 'service-visits', 'inventory',
                         'invoices', 'expenses', 'notifications', 'audit-logs']:
            with self.subTest(resource=resource):
                response = self.client.get('/api/v1/' + resource + '/not-a-uuid', headers=self.headers())
                self.assertEqual(response.status_code, 422, response.text)
                self.assertIsInstance(response.json()['detail'], list)

    def test_audit_mutation_methods_are_absent(self):
        path = '/api/v1/audit-logs/' + str(uuid4())
        for method in ['patch', 'put', 'delete']:
            with self.subTest(method=method):
                response = getattr(self.client, method)(path, headers=self.headers())
                self.assertEqual(response.status_code, 405, response.text)


if __name__ == '__main__':
    unittest.main()
