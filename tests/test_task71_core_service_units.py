"""Accepted core rules with isolated repositories; no database or HTTP access."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from uuid import uuid4

from backend.services.asset import AssetService
from backend.services.customer import CustomerService
from backend.services.inventory import InventoryService
from backend.services.inventory_rules import InventoryBusinessRules
from backend.services.profitability import ProfitabilityService
from backend.services.service_contract import ServiceContractService
from backend.services.status_lifecycle import (derive_work_order_status,
    ensure_work_order_transition, ensure_service_visit_transition)


class Task71CoreServiceUnits(unittest.TestCase):
    def test_work_order_terminal_state_refuses_reopening(self):
        self.assertEqual(ensure_work_order_transition(' Open ', ' In Progress '), 'In Progress')
        self.assertEqual(ensure_work_order_transition('Completed', 'Cancelled'), 'Cancelled')
        for current, target in [('Completed', 'Open'), ('Cancelled', 'Completed'), ('Open', 'Unknown')]:
            with self.subTest(current=current, target=target), self.assertRaises(ValueError):
                ensure_work_order_transition(current, target)

    def test_visit_lifecycle_refuses_backwards_or_unsupported_transition(self):
        self.assertEqual(ensure_service_visit_transition('Planned', 'Completed'), 'Completed')
        for current, target in [('In Progress', 'Planned'), ('Cancelled', 'In Progress'), ('Planned', '')]:
            with self.subTest(current=current, target=target), self.assertRaises(ValueError):
                ensure_service_visit_transition(current, target)

    def test_work_order_aggregation_priority_and_deleted_filter(self):
        cases = [([], None), (['Deleted'], None), (['Completed', 'In Progress'], 'In Progress'),
                 (['Planned', 'Completed'], 'Open'), (['Cancelled'], 'Cancelled'),
                 (['Cancelled', 'Completed', 'Deleted'], 'Completed')]
        for statuses, expected in cases:
            with self.subTest(statuses=statuses):
                self.assertEqual(derive_work_order_status(statuses), expected)

    def test_asset_missing_customer_prevents_repository_mutation(self):
        repository, customers = Mock(), Mock()
        customers.get.return_value = None
        service = AssetService(repository, customers)
        company, customer, db = uuid4(), uuid4(), object()
        with self.assertRaisesRegex(ValueError, 'Customer not found'):
            service.create_asset(db, company, {'customer_id': customer})
        customers.get.assert_called_once_with(db, company, customer)
        repository.create.assert_not_called()

    def test_asset_missing_record_short_circuits_patch_reference_lookup(self):
        repository, customers = Mock(), Mock()
        repository.get.return_value = None
        service = AssetService(repository, customers)
        self.assertIsNone(service.update_asset(object(), uuid4(), uuid4(), {'customer_id': uuid4()}))
        customers.get.assert_not_called()
        repository.update.assert_not_called()

    def test_asset_patch_without_customer_keeps_explicit_payload(self):
        repository, customers = Mock(), Mock()
        service = AssetService(repository, customers)
        db, company, identifier, payload = object(), uuid4(), uuid4(), {'notes': 'Synthetic'}
        service.update_asset(db, company, identifier, payload)
        customers.get.assert_not_called()
        repository.update.assert_called_once_with(db, company, identifier, payload)

    def test_profitability_exact_decimal_negative_profit_and_margin(self):
        repository = Mock()
        repository.revenue_totals.return_value = (Decimal('3.00'), Decimal('1.25'), 1)
        repository.expense_totals.return_value = (Decimal('4.00'), 2)
        db, company, start, end = object(), uuid4(), date(2026, 1, 1), date(2026, 1, 31)
        result = ProfitabilityService(repository).summary(db, company, start, end)
        self.assertEqual((result.net_profit, result.cash_net_profit, result.profit_margin_percent),
                         (Decimal('-1.00'), Decimal('-2.75'), Decimal('-33.33')))
        repository.revenue_totals.assert_called_once_with(db, company, start, end)
        repository.expense_totals.assert_called_once_with(db, company, start, end)

    def test_profitability_empty_aggregates_do_not_divide_by_zero(self):
        repository = Mock()
        repository.revenue_totals.return_value = (None, None, 0)
        repository.expense_totals.return_value = (None, 0)
        result = ProfitabilityService(repository).summary(object(), uuid4())
        self.assertEqual((result.net_profit, result.cash_net_profit, result.profit_margin_percent),
                         (Decimal('0'), Decimal('0'), Decimal('0.00')))

    def test_contract_partial_dates_validate_effective_state_before_write(self):
        repository = Mock()
        repository.get.return_value = SimpleNamespace(start_date=date(2026, 1, 10), end_date=date(2026, 1, 20))
        service = ServiceContractService(repository)
        for payload in ({'end_date': date(2026, 1, 9)}, {'start_date': date(2026, 1, 21)}):
            with self.subTest(payload=payload), self.assertRaisesRegex(ValueError, 'end_date must be on or after start_date'):
                service.update_contract(object(), uuid4(), uuid4(), payload)
        repository.update.assert_not_called()

    def test_contract_explicit_null_end_preserves_open_ended_patch(self):
        repository = Mock()
        repository.get.return_value = SimpleNamespace(start_date=date(2026, 1, 10), end_date=date(2026, 1, 20))
        db, company, identifier, payload = object(), uuid4(), uuid4(), {'end_date': None}
        ServiceContractService(repository).update_contract(db, company, identifier, payload)
        repository.update.assert_called_once_with(db, company, identifier, payload)

    def test_create_normalization_copies_input_and_patch_stays_authoritative(self):
        for service_type, create, update, key, error in [
            (CustomerService, 'create_customer', 'update_customer', 'name', 'Name is required.'),
            (InventoryService, 'create_item', 'update_item', 'item_name', 'Item name is required.')]:
            with self.subTest(service=service_type.__name__):
                repository = Mock()
                service, db, company = service_type(repository), object(), uuid4()
                payload = {key: '  Synthetic  '}
                getattr(service, create)(db, company, payload)
                self.assertEqual(payload[key], '  Synthetic  ')
                repository.create.assert_called_once_with(db, company, {key: 'Synthetic'})
                with self.assertRaises(ValueError) as failure:
                    getattr(service, create)(db, company, {key: '  '})
                self.assertEqual(str(failure.exception), error)
                identifier = uuid4()
                getattr(service, update)(db, company, identifier, payload)
                repository.update.assert_called_once_with(db, company, identifier, payload)

    def test_stock_thresholds_and_exact_decimal_value(self):
        for quantity, minimum, ideal, status in [(2, 2, 10, 'CRITICAL'), (3, 2, 10, 'LOW'),
                                                  (5, 2, 10, 'GOOD'), (3, 2, 0, 'GOOD')]:
            with self.subTest(quantity=quantity, ideal=ideal):
                item = SimpleNamespace(quantity=quantity, min_limit=minimum, ideal_stock=ideal,
                                       cost_price=Decimal('0.10'))
                self.assertEqual(InventoryBusinessRules.stock_status(item).code, status)
                self.assertEqual(InventoryBusinessRules.item_value(item), Decimal(quantity) / 10)


if __name__ == '__main__':
    unittest.main()
