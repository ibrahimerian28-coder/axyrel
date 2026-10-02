"""Task 64: obsolete callers never reach Google Sheets or Apps Script."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from utils import data_service as facade
from utils.api_client import APIClientError


class Task64RemoveSheetsTests(unittest.TestCase):
    def setUp(self):
        self.session = patch.object(facade, 'st', SimpleNamespace(session_state={
            'SHEETS': {'Customers': '0', 'Inventory': '1', 'Expenses': '2'}}))
        self.session.start()
        self.addCleanup(self.session.stop)
        # Any accidental external fallback fails the test, without network access.
        self.network = patch('requests.post', side_effect=AssertionError('External write'))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.csv = patch.object(facade.pd, 'read_csv', side_effect=AssertionError('External read'))
        self.csv.start()
        self.addCleanup(self.csv.stop)

    def test_disabled_mode_never_reads_or_writes_external_source(self):
        with patch.object(facade, 'api_enabled', return_value=False):
            with self.assertRaises(APIClientError):
                facade.load_sheet('0')
            self.assertFalse(facade.add_row('Customers', {'name': 'Synthetic'}))
            self.assertFalse(facade.update_row('Customers', 'synthetic-id', {}))
            self.assertFalse(facade.delete_row_by_uuid('Customers', 'synthetic-id'))

    def test_unsupported_source_never_falls_back(self):
        with patch.object(facade, 'api_enabled', return_value=True):
            with self.assertRaises(APIClientError):
                facade.load_sheet('unknown')
            self.assertFalse(facade.add_row('Inventory_History', {}))

    def test_supported_read_preserves_api_adapter_columns(self):
        with patch.object(facade, 'api_enabled', return_value=True), \
                patch.object(facade, 'list_records', return_value=[{'id': 'synthetic-id', 'name': 'Synthetic'}]) as api:
            frame = facade.load_sheet('0')
            api.assert_called_once_with('customers')
            self.assertEqual(frame.iloc[0]['uuid'], 'synthetic-id')

    def test_supported_write_actions_preserve_api_dispatch(self):
        with patch.object(facade, 'api_enabled', return_value=True), \
                patch.object(facade, 'create_record') as create, \
                patch.object(facade, 'update_record') as update, \
                patch.object(facade, 'delete_record') as delete:
            self.assertTrue(facade.add_row('Customers', {'name': 'Synthetic', 'uuid': 'ignored'}))
            create.assert_called_once_with('customers', {'name': 'Synthetic'})
            self.assertTrue(facade.update_row('Customers', 'synthetic-id', {'name': 'Changed'}))
            update.assert_called_once_with('customers', 'synthetic-id', {'name': 'Changed'})
            self.assertTrue(facade.delete_row_by_uuid('Customers', 'synthetic-id'))
            delete.assert_called_once_with('customers', 'synthetic-id')

    def test_api_write_failure_and_unknown_action_remain_false(self):
        with patch.object(facade, 'api_enabled', return_value=True), \
                patch.object(facade, 'create_record', side_effect=APIClientError('Synthetic failure')):
            self.assertFalse(facade.add_row('Customers', {'name': 'Synthetic'}))
            self.assertFalse(facade.call_api('unknown', 'Customers'))


if __name__ == '__main__':
    unittest.main()
