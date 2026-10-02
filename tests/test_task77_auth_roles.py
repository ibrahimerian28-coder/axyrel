"""Accepted database-role matrix on real API resources, not inferred JWT privileges."""
import unittest
import test_task49_authentication_context as fixture
from backend.core.security import create_access_token
from backend.models.user import User


class Task77AuthRoles(unittest.TestCase):
    setUpClass = classmethod(fixture.Task49AuthenticationContextTests.setUpClass.__func__)
    tearDownClass = classmethod(fixture.Task49AuthenticationContextTests.tearDownClass.__func__)
    setUp = fixture.Task49AuthenticationContextTests.setUp

    def _role(self, role):
        with self.Session() as db:
            db.get(User, self.user_id).role = role
            db.commit()

    def test_read_matrix_uses_database_role_despite_admin_claims(self):
        resources = ['customers', 'assets', 'work-orders', 'inventory', 'notifications',
                     'invoices', 'expenses', 'audit-logs', 'profitability/summary']
        technician_allowed = {'customers', 'assets', 'work-orders', 'inventory', 'notifications'}
        token = create_access_token(str(self.user_id), role='admin', permissions=['*'])
        for role in ['admin', 'manager', 'technician']:
            self._role(role)
            for resource in resources:
                with self.subTest(role=role, resource=resource):
                    response = self.client.get('/api/v1/' + resource, headers={'Authorization': 'Bearer ' + token})
                    expected = 200 if role != 'technician' or resource in technician_allowed else 403
                    self.assertEqual(response.status_code, expected, response.text)
                    if expected == 403:
                        self.assertEqual(response.json(), {'detail': 'Insufficient permissions'})
                        self.assertNotIn('www-authenticate', response.headers)

    def test_customer_inventory_write_matrix_and_denial_has_no_mutation(self):
        headers = {'Authorization': 'Bearer ' + self.token}
        for role in ['admin', 'manager', 'technician']:
            self._role(role)
            for resource, data in [('customers', {'name': 'Synthetic ' + role}),
                                   ('inventory', {'item_name': 'Synthetic ' + role, 'quantity': 1})]:
                with self.subTest(role=role, resource=resource):
                    before = self.client.get('/api/v1/' + resource, headers=headers).json()
                    response = self.client.post('/api/v1/' + resource, headers=headers, json=data)
                    expected = 403 if role == 'technician' else 201
                    self.assertEqual(response.status_code, expected, response.text)
                    after = self.client.get('/api/v1/' + resource, headers=headers).json()
                    self.assertEqual(len(after), len(before) + (expected == 201))
                    if expected == 403:
                        self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main()
