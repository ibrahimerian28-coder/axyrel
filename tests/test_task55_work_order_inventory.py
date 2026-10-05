"""Work Order inventory integration through the accepted Service Visit workflow."""
import unittest
from unittest.mock import patch
from uuid import UUID, uuid4

import test_task46_service_visit as visit_fixture
from sqlalchemy import select
from backend.models.inventory_item import InventoryItem
from backend.models.inventory_transaction import InventoryTransaction
from backend.models.service_visit import ServiceVisit
from backend.models.technician_stock import TechnicianStock
from backend.models.work_order import WorkOrder
from backend.models.company import Company
from backend.models.customer import Customer


class Task55WorkOrderInventoryTests(visit_fixture.Task46ServiceVisitTests):
    """Retain six accepted lifecycle tests and extend order-level stock coverage."""

    def _stock_setup(self):
        headers = self._auth()
        item = self.client.post("/api/v1/inventory", headers=headers,
                                json={"item_name": "Service part", "quantity": 20, "cost_price": 5})
        self.assertEqual(item.status_code, 201, item.text)
        item_id = item.json()["id"]
        stock = self.client.post("/api/v1/technician-stock", headers=headers,
                                 json={"technician_id": str(self.technician_id), "inventory_item_id": item_id, "quantity": 8})
        self.assertEqual(stock.status_code, 201, stock.text)
        order = self._create_work_order(headers)
        return headers, item_id, order

    def _install(self, headers, visit, item_id, quantity):
        return self.client.post(f"/api/v1/service-visits/{visit['id']}/parts", headers=headers,
                                json={"inventory_item_id": item_id, "quantity": quantity})

    def _state(self, item_id, order_id):
        with self.Session() as db:
            item = db.get(InventoryItem, UUID(item_id))
            stocks = db.scalars(select(TechnicianStock).where(TechnicianStock.inventory_item_id == UUID(item_id))).all()
            visits = db.scalars(select(ServiceVisit).where(ServiceVisit.work_order_id == UUID(order_id))).all()
            transactions = db.scalars(select(InventoryTransaction).where(InventoryTransaction.inventory_item_id == UUID(item_id))).all()
            return (item.quantity, {str(s.technician_id): s.quantity for s in stocks},
                    db.get(WorkOrder, UUID(order_id)).status, {str(v.id): v.status for v in visits},
                    {(str(t.id), t.reference_type, t.reference_id, t.quantity) for t in transactions})

    def test_order_cancel_restores_multiple_visits_once_with_reference_integrity(self):
        headers, item, order = self._stock_setup()
        first = self._create_visit(headers, order["id"], status="In Progress")
        second = self._create_visit(headers, order["id"], status="In Progress")
        warehouse_before = self._state(item, order["id"])[0]
        for visit, quantity in ((first, 2), (second, 3)):
            response = self._install(headers, visit, item, quantity)
            self.assertEqual(response.status_code, 200, response.text)
        consumed = self._state(item, order["id"])
        self.assertEqual(consumed[1][str(self.technician_id)], 3)
        response = self.client.patch(f"/api/v1/work-orders/{order['id']}", headers=headers, json={"status": "Cancelled"})
        self.assertEqual(response.status_code, 200, response.text)
        restored = self._state(item, order["id"])
        self.assertEqual(restored[0], warehouse_before)
        self.assertEqual(restored[1][str(self.technician_id)], 8)
        self.assertEqual(restored[2], "Cancelled")
        self.assertEqual(set(restored[3].values()), {"Cancelled"})
        installs = {(ref, quantity) for _, kind, ref, quantity in restored[4] if kind == "SERVICE_VISIT_INSTALL"}
        reversals = {(ref, quantity) for _, kind, ref, quantity in restored[4] if kind == "SERVICE_VISIT_REVERSAL"}
        self.assertEqual(installs, {(first["id"], 2), (second["id"], 3)})
        self.assertEqual(reversals, installs)
        response = self.client.patch(f"/api/v1/work-orders/{order['id']}", headers=headers, json={"status": "Cancelled"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self._state(item, order["id"]), restored)

    def test_order_delete_restores_stock_and_repeated_delete_is_safe(self):
        headers, item, order = self._stock_setup()
        visit = self._create_visit(headers, order["id"], status="In Progress")
        response = self._install(headers, visit, item, 2)
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.delete(f"/api/v1/work-orders/{order['id']}", headers=headers)
        self.assertEqual(response.status_code, 204, response.text)
        restored = self._state(item, order["id"])
        self.assertEqual(restored[1][str(self.technician_id)], 8)
        self.assertEqual(restored[2], "Deleted")
        self.assertEqual(restored[3][visit["id"]], "Cancelled")
        response = self.client.delete(f"/api/v1/work-orders/{order['id']}", headers=headers)
        # Existing tenant-scoped soft_delete intentionally remains repeatable.
        self.assertEqual(response.status_code, 204, response.text)
        self.assertEqual(self._state(item, order["id"]), restored)

    def test_insufficient_stock_rejects_install_without_mutation(self):
        headers, item, order = self._stock_setup()
        visit = self._create_visit(headers, order["id"], status="In Progress")
        before = self._state(item, order["id"])
        response = self._install(headers, visit, item, 9)
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(self._state(item, order["id"]), before)

    def test_cancel_failure_rolls_back_order_visits_stock_and_transactions(self):
        headers, item, order = self._stock_setup()
        visits = [self._create_visit(headers, order["id"], status="In Progress") for _ in range(2)]
        for visit in visits:
            response = self._install(headers, visit, item, 2)
            self.assertEqual(response.status_code, 200, response.text)
        before = self._state(item, order["id"])
        from backend.api.v1.work_orders import service
        original_restore = service.visit_service.inventory_rules.restore_technician_stock
        calls = []

        def fail_after_first_restore(*args, **kwargs):
            calls.append(1)
            if len(calls) == 2:
                raise ValueError("Bounded test restoration failure")
            return original_restore(*args, **kwargs)

        with patch.object(service.visit_service.inventory_rules, "restore_technician_stock", side_effect=fail_after_first_restore):
            response = self.client.patch(f"/api/v1/work-orders/{order['id']}", headers=headers, json={"status": "Cancelled"})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(len(calls), 2)
        self.assertEqual(self._state(item, order["id"]), before)

    def test_completed_order_cancellation_restores_its_consumed_stock(self):
        headers, item, order = self._stock_setup()
        visit = self._create_visit(headers, order["id"], status="In Progress")
        response = self._install(headers, visit, item, 2)
        self.assertEqual(response.status_code, 200, response.text)
        completed = self.client.patch(f"/api/v1/service-visits/{visit['id']}", headers=headers, json={"status": "Completed"})
        self.assertEqual(completed.status_code, 200, completed.text)
        self.assertEqual(self._state(item, order["id"])[2], "Open")
        finished = self.client.patch(f"/api/v1/work-orders/{order['id']}", headers=headers, json={"status": "Completed"})
        self.assertEqual(finished.status_code, 200, finished.text)
        cancelled = self.client.patch(f"/api/v1/work-orders/{order['id']}", headers=headers, json={"status": "Cancelled"})
        self.assertEqual(cancelled.status_code, 200, cancelled.text)
        self.assertEqual(self._state(item, order["id"])[1][str(self.technician_id)], 8)

    def test_order_cancel_skips_already_reversed_visit(self):
        headers, item, order = self._stock_setup()
        first = self._create_visit(headers, order["id"], status="In Progress")
        second = self._create_visit(headers, order["id"], status="In Progress")
        for visit in (first, second):
            installed = self._install(headers, visit, item, 2)
            self.assertEqual(installed.status_code, 200, installed.text)
        cancelled = self.client.patch(f"/api/v1/service-visits/{first['id']}", headers=headers, json={"status": "Cancelled"})
        self.assertEqual(cancelled.status_code, 200, cancelled.text)
        response = self.client.patch(f"/api/v1/work-orders/{order['id']}", headers=headers, json={"status": "Cancelled"})
        self.assertEqual(response.status_code, 200, response.text)
        state = self._state(item, order["id"])
        self.assertEqual(state[1][str(self.technician_id)], 8)
        self.assertEqual(len([row for row in state[4] if row[1] == "SERVICE_VISIT_REVERSAL"]), 2)

    def test_foreign_and_missing_order_operations_leave_inventory_unchanged(self):
        headers, item, order = self._stock_setup()
        foreign_company, foreign_customer, foreign_order = [uuid4() for _ in range(3)]
        with self.Session() as db:
            db.add(Company(id=foreign_company, name="Foreign", status="active"))
            db.flush()
            db.add(Customer(id=foreign_customer, company_id=foreign_company, name="Foreign"))
            db.flush()
            db.add(WorkOrder(id=foreign_order, company_id=foreign_company, customer_id=foreign_customer, title="Foreign"))
            db.commit()
        before = self._state(item, order["id"])
        for target in (foreign_order, uuid4()):
            response = self.client.patch(f"/api/v1/work-orders/{target}", headers=headers, json={"status": "Cancelled"})
            self.assertEqual(response.status_code, 404, response.text)
            response = self.client.delete(f"/api/v1/work-orders/{target}", headers=headers)
            self.assertEqual(response.status_code, 404, response.text)
            self.assertEqual(self._state(item, order["id"]), before)


if __name__ == "__main__":
    unittest.main()
