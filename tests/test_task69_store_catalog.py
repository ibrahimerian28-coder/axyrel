"""Accepted inventory-backed Store catalog, without legacy product source."""
import unittest
from unittest.mock import MagicMock, patch
from modules import store
from utils.api_client import APIClientError


class Task69StoreCatalogTests(unittest.TestCase):
    def test_catalog_reads_inventory_and_preserves_display_fields(self):
        with patch.object(store, 'st', MagicMock()) as ui, \
                patch.object(store, 'list_records', return_value=[{
                    'id': 'synthetic', 'item_name': 'Synthetic Filter', 'quantity': 2,
                    'cost_price': '15.25', 'status': 'Active'}]) as api:
            store.app()
            api.assert_called_once_with('inventory')
            frame = ui.dataframe.call_args.args[0]
            self.assertEqual(list(frame.columns), ['item_name', 'quantity', 'cost_price', 'status'])
            self.assertEqual(frame.iloc[0]['cost_price'], '15.25 EGP')

    def test_empty_catalog_keeps_existing_message(self):
        with patch.object(store, 'st', MagicMock()) as ui, \
                patch.object(store, 'list_records', return_value=[]) as api:
            store.app()
            api.assert_called_once_with('inventory')
            ui.info.assert_called_once_with('No catalog items yet. Add items from Inventory.')
            ui.dataframe.assert_not_called()

    def test_api_failure_uses_existing_error_boundary_without_fallback(self):
        with patch.object(store, 'st', MagicMock()) as ui, \
                patch('utils.ui.st.error') as error, \
                patch.object(store, 'list_records', side_effect=APIClientError('Synthetic failure')) as api, \
                patch('requests.post', side_effect=AssertionError('External fallback')):
            store.app()
            api.assert_called_once_with('inventory')
            error.assert_called_once_with('Synthetic failure')
            ui.dataframe.assert_not_called()


if __name__ == '__main__':
    unittest.main()
