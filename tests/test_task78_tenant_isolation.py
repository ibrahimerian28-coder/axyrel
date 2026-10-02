"""Synthetic two-admin tenant boundary across accepted migrated API resources."""
import unittest
from uuid import uuid4
import test_task76_postgresql_financial as fixture


class Task78TenantIsolation(unittest.TestCase):
    _drop = fixture.Task76PostgreSQLFinancial._drop
    _apply = fixture.Task76PostgreSQLFinancial._apply
    _rows = fixture.Task76PostgreSQLFinancial._rows
    _post = fixture.Task76PostgreSQLFinancial._post
    _get = fixture.Task76PostgreSQLFinancial._get
    setUp = fixture.Task76PostgreSQLFinancial.setUp

    def _resources(self):
        rows = {'customers': self._get('customers/' + self.customer)}
        def create(resource, payload):
            rows[resource] = self._post(resource, payload)
            return rows[resource]['id']
        asset = create('assets', {'customer_id': self.customer, 'asset_type': 'Synthetic'})
        request = create('service-requests', {'customer_id': self.customer, 'asset_id': asset, 'title': 'Synthetic'})
        order = create('work-orders', {'customer_id': self.customer, 'asset_id': asset, 'service_request_id': request, 'title': 'Synthetic'})
        schedule = create('schedules', {'work_order_id': order, 'start_at': '2026-01-15T08:00:00Z', 'end_at': '2026-01-15T09:00:00Z'})
        visit = create('service-visits', {'customer_id': self.customer, 'work_order_id': order, 'schedule_id': schedule})
        create('service-history', {'customer_id': self.customer, 'service_visit_id': visit,
            'work_order_id': order, 'service_type': 'Synthetic', 'service_date': '2026-01-15T09:00:00', 'summary': 'Synthetic'})
        item = create('inventory', {'item_name': 'Synthetic', 'quantity': 10})
        create('technician-stock', {'technician_id': str(uuid4()), 'inventory_item_id': item, 'quantity': 2})
        create('inventory-transactions', {'inventory_item_id': item, 'transaction_type': 'IN', 'quantity': 1})
        create('invoices', {'customer_id': self.customer, 'work_order_id': order,
                           'invoice_number': 'SYN-TENANT', 'issue_date': '2026-01-15'})
        create('service-contracts', {'customer_id': self.customer, 'contract_number': 'SYN-TENANT', 'start_date': '2026-01-15'})
        create('expenses', {'category': 'Synthetic', 'amount': '1.25', 'expense_date': '2026-01-15'})
        create('notifications', {'notification_type': 'Synthetic', 'title': 'Synthetic', 'message': 'Synthetic'})
        create('audit-logs', {'action': 'Synthetic explicit audit'})
        return rows

    def test_all_resources_ignore_tenant_header_query_override_on_foreign_reads(self):
        for resource, row in self._resources().items():
            with self.subTest(resource=resource):
                headers = {**self.other_headers, 'X-Company-ID': str(self.company)}
                response = self.client.get('/api/v1/' + resource, headers=headers, params={'company_id': str(self.company)})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json(), [])
                response = self.client.get('/api/v1/' + resource + '/' + row['id'], headers=headers)
                self.assertEqual(response.status_code, 404, response.text)

    def test_foreign_supported_mutations_leave_every_owned_resource_unchanged(self):
        rows = self._resources()
        before = {resource: self._get(resource + '/' + row['id']) for resource, row in rows.items()}
        read_only = {'audit-logs', 'inventory-transactions'}
        no_delete = read_only | {'notifications', 'technician-stock'}
        for resource, row in rows.items():
            path = '/api/v1/' + resource + '/' + row['id']
            if resource not in read_only:
                payload = {'quantity': 99} if resource in {'inventory', 'technician-stock'} else \
                          {'name': 'Denied'} if resource == 'customers' else \
                          {'title': 'Denied'} if resource == 'notifications' else {'notes': 'Denied'}
                with self.subTest(resource=resource, operation='patch'):
                    response = self.client.patch(path, headers=self.other_headers, json=payload)
                    self.assertEqual(response.status_code, 404, response.text)
            if resource not in no_delete:
                with self.subTest(resource=resource, operation='delete'):
                    response = self.client.delete(path, headers=self.other_headers)
                    self.assertEqual(response.status_code, 404, response.text)
        after = {resource: self._get(resource + '/' + row['id']) for resource, row in rows.items()}
        self.assertEqual(after, before)

    def test_explicit_payload_company_does_not_override_authenticated_write_scope(self):
        for resource, payload in [('inventory', {'item_name': 'Synthetic Other Tenant'}),
                                  ('expenses', {'category': 'Synthetic', 'amount': '2', 'expense_date': '2026-01-15'})]:
            with self.subTest(resource=resource):
                row = self._post(resource, {**payload, 'company_id': str(self.company)}, self.other_headers)
                self.assertEqual(row['company_id'], str(self.other))
                self.assertEqual(self._get(resource), [])
                self.assertEqual(len(self._get(resource, self.other_headers)), 1)


if __name__ == '__main__':
    unittest.main()
