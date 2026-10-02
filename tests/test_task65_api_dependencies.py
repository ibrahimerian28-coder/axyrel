"""Active presentation modules remain independent of removed legacy persistence."""
import ast
import importlib
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REMOVED = {'utils.data_service', 'utils.inventory_service', 'utils.inventory_history_service',
           'components.customers.customer_actions', 'components.customers.customer_add_form',
           'components.customers.customer_summary', 'utils.helpers'}


class Task65APIDependencyTests(unittest.TestCase):
    def test_no_runtime_import_targets_removed_dependency_group(self):
        for directory in ('modules', 'components', 'utils', 'backend'):
            for path in (ROOT / directory).rglob('*.py'):
                tree = ast.parse(path.read_text(encoding='utf-8-sig'))
                for node in ast.walk(tree):
                    names = ([node.module] if isinstance(node, ast.ImportFrom) else
                             [alias.name for alias in node.names] if isinstance(node, ast.Import) else [])
                    self.assertFalse(REMOVED.intersection(names), str(path))

    def test_all_routed_modules_import_without_http_or_legacy_facade(self):
        with patch('requests.request', side_effect=AssertionError('Unexpected HTTP')), \
                patch('requests.post', side_effect=AssertionError('Unexpected HTTP')):
            for name in ('dashboard', 'customers', 'maintenance', 'inventory', 'expenses',
                         'invoices', 'profits', 'store'):
                module = importlib.import_module('modules.' + name)
                self.assertTrue(callable(module.app), name)

    def test_router_dispatches_to_existing_api_module(self):
        from utils.router import route
        from modules import customers
        with patch.object(customers, 'app') as app:
            route('Customers')
            app.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
