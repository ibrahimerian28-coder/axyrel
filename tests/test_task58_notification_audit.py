"""OD-19 explicit Notification/Audit acceptance on a disposable API database."""
import unittest
from uuid import UUID, uuid4

import test_task56_order_billing_integration as billing_fixture
from sqlalchemy import select, func
from backend.models.notification import Notification
from backend.models.audit_log import AuditLog
from backend.models.user import User
from backend.repositories.audit_log import AuditLogRepository
from backend.services.audit_log import AuditLogService
from backend.services.notification import NotificationService


class Task58NotificationAuditTests(unittest.TestCase):
    setUpClass = classmethod(billing_fixture.Task56OrderBillingTests.setUpClass.__func__)
    tearDownClass = classmethod(billing_fixture.Task56OrderBillingTests.tearDownClass.__func__)
    setUp = billing_fixture.Task56OrderBillingTests.setUp

    def _notification(self, **data):
        response = self.client.post("/api/v1/notifications", headers=self.headers,
                                    json={"notification_type": "explicit", "title": "Notice", "message": "Explicit notice", **data})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _audit(self, **data):
        response = self.client.post("/api/v1/audit-logs", headers=self.headers,
                                    json={"action": "explicit.record", "entity_type": "work_order",
                                          "entity_id": str(self.order), **data})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _get(self, path):
        response = self.client.get(path, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def _counts(self):
        with self.Session() as db:
            return (db.scalar(select(func.count()).select_from(Notification)),
                    db.scalar(select(func.count()).select_from(AuditLog)))

    def _foreign_records(self):
        with self.Session() as db:
            notification = NotificationService().create_notification(db, self.foreign_company,
                          {"notification_type": "foreign", "title": "Foreign", "message": "Foreign notice"})
            audit = AuditLogService().create_audit_log(db, self.foreign_company, {"action": "foreign.record"})
            ids = notification.id, audit.id
            db.commit()
        return ids

    def test_notification_create_read_list_and_defaults(self):
        record = self._notification()
        self.assertEqual(record["company_id"], str(self.company))
        self.assertEqual(record["status"], "unread")
        self.assertEqual(record["priority"], "normal")
        self.assertIsNone(record["read_at"])
        self.assertIsNone(record["recipient_user_id"])
        self.assertEqual(self._get(f"/api/v1/notifications/{record['id']}"), record)
        self.assertEqual(self._get("/api/v1/notifications"), [record])

    def test_mark_read_and_repeat_mark_read_preserve_existing_state(self):
        record = self._notification()
        for _ in range(2):
            response = self.client.post(f"/api/v1/notifications/{record['id']}/read", headers=self.headers)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["status"], "read")
            self.assertIsNotNone(response.json()["read_at"])
        fetched = self._get(f"/api/v1/notifications/{record['id']}")
        self.assertEqual(fetched, response.json())
        self.assertEqual(self._counts(), (1, 0))

    def test_notification_patch_read_unread_and_explicit_read_at(self):
        record = self._notification()
        response = self.client.patch(f"/api/v1/notifications/{record['id']}", headers=self.headers,
                                     json={"status": "read", "read_at": "2026-10-02T12:00:00"})
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.patch(f"/api/v1/notifications/{record['id']}", headers=self.headers, json={"status": "unread"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "unread")
        self.assertEqual(response.json()["read_at"], "2026-10-02T12:00:00")
        response = self.client.patch(f"/api/v1/notifications/{record['id']}", headers=self.headers, json={"read_at": None})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["read_at"])

    def test_expiration_list_filter_does_not_change_existing_get_contract(self):
        expired = self._notification(expires_at="2000-01-01T00:00:00")
        future = self._notification(expires_at="2100-01-01T00:00:00")
        self.assertEqual([row["id"] for row in self._get("/api/v1/notifications")], [future["id"]])
        self.assertEqual(self._get(f"/api/v1/notifications/{expired['id']}"), expired)
        with self.Session() as db:
            rows = NotificationService().list_notifications(db, self.company, include_expired=True)
            self.assertEqual({str(row.id) for row in rows}, {expired["id"], future["id"]})

    def test_notification_existing_service_filters_and_explicit_metadata(self):
        entity = str(uuid4())
        record = self._notification(recipient_user_id=str(self.admin), entity_type="explicit", entity_id=entity,
                                     action_url="/explicit", priority="high")
        self._notification(notification_type="other")
        self.assertEqual(record["entity_id"], entity)
        self.assertEqual(record["action_url"], "/explicit")
        with self.Session() as db:
            rows = NotificationService().list_notifications(db, self.company, recipient_user_id=self.admin,
                                                             notification_type="explicit", status="unread")
            self.assertEqual([str(row.id) for row in rows], [record["id"]])

    def test_notification_tenant_isolation_on_all_existing_operations(self):
        foreign, _ = self._foreign_records()
        own = self._notification()
        self.assertEqual(self._get("/api/v1/notifications"), [own])
        for target in (foreign, uuid4()):
            self.assertEqual(self.client.get(f"/api/v1/notifications/{target}", headers=self.headers).status_code, 404)
            self.assertEqual(self.client.patch(f"/api/v1/notifications/{target}", headers=self.headers,
                                               json={"status": "read"}).status_code, 404)
            self.assertEqual(self.client.post(f"/api/v1/notifications/{target}/read", headers=self.headers).status_code, 404)
        with self.Session() as db:
            self.assertEqual(db.get(Notification, foreign).status, "unread")
            self.assertIsNone(db.get(Notification, foreign).read_at)

    def test_notification_validation_has_no_partial_update(self):
        own = self._notification()
        before = self._counts()
        response = self.client.post("/api/v1/notifications", headers=self.headers,
                                    json={"notification_type": "explicit", "title": "", "message": "Notice"})
        self.assertEqual(response.status_code, 422, response.text)
        response = self.client.patch(f"/api/v1/notifications/{own['id']}", headers=self.headers,
                                     json={"status": "", "read_at": "2026-10-02T12:00:00"})
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self._get(f"/api/v1/notifications/{own['id']}"), own)
        self.assertEqual(self._counts(), before)

    def test_audit_create_read_list_and_explicit_content(self):
        metadata = {"source": "explicit test", "change": {"old": "Open", "new": "Completed"}}
        record = self._audit(actor_user_id=str(self.admin), description="Explicit activity", event_metadata=metadata,
                             ip_address="127.0.0.1", user_agent="test-client")
        self.assertEqual(record["company_id"], str(self.company))
        self.assertEqual(record["actor_user_id"], str(self.admin))
        self.assertEqual(record["event_metadata"], metadata)
        self.assertEqual(self._get(f"/api/v1/audit-logs/{record['id']}"), record)
        self.assertEqual(self._get("/api/v1/audit-logs"), [record])

    def test_audit_optional_actor_preserved_without_inheritance(self):
        record = self._audit()
        self.assertIsNone(record["actor_user_id"])
        self.assertIsNone(record["description"])
        self.assertIsNone(record["event_metadata"])

    def test_audit_api_and_service_expose_no_update_delete_operations(self):
        record = self._audit(event_metadata={"original": True})
        for method in (self.client.patch, self.client.put):
            response = method(f"/api/v1/audit-logs/{record['id']}", headers=self.headers, json={"action": "modified"})
            self.assertEqual(response.status_code, 405, response.text)
        response = self.client.delete(f"/api/v1/audit-logs/{record['id']}", headers=self.headers)
        self.assertEqual(response.status_code, 405, response.text)
        self.assertEqual(self._get(f"/api/v1/audit-logs/{record['id']}"), record)
        for target, names in ((AuditLogService(), ("update_audit_log", "delete_audit_log")),
                               (AuditLogRepository(), ("update", "delete", "soft_delete"))):
            for name in names:
                self.assertFalse(hasattr(target, name))

    def test_audit_tenant_isolation_and_missing_record(self):
        _, foreign = self._foreign_records()
        own = self._audit()
        self.assertEqual(self._get("/api/v1/audit-logs"), [own])
        for target in (foreign, uuid4()):
            self.assertEqual(self.client.get(f"/api/v1/audit-logs/{target}", headers=self.headers).status_code, 404)
        with self.Session() as db:
            self.assertIsNone(AuditLogService().get_audit_log(db, self.company, foreign))

    def test_audit_existing_service_filters_and_inclusive_time_bounds(self):
        own = self._audit(actor_user_id=str(self.admin))
        self._audit(action="other.record")
        with self.Session() as db:
            created = db.get(AuditLog, UUID(own["id"])).created_at
            rows = AuditLogService().list_audit_logs(db, self.company, actor_user_id=self.admin,
                         action="explicit.record", entity_type="work_order", entity_id=self.order,
                         start_at=created, end_at=created)
            self.assertEqual([str(row.id) for row in rows], [own["id"]])

    def test_audit_schema_rejects_invalid_content_without_record(self):
        before = self._counts()
        response = self.client.post("/api/v1/audit-logs", headers=self.headers, json={"action": ""})
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self._counts(), before)

    def test_company_scope_is_authoritative_for_explicit_api_writes(self):
        notification = self._notification(company_id=str(self.foreign_company))
        audit = self._audit(company_id=str(self.foreign_company))
        self.assertEqual(notification["company_id"], str(self.company))
        self.assertEqual(audit["company_id"], str(self.company))

    def test_authentication_and_existing_role_permissions(self):
        for route in ("notifications", "audit-logs"):
            self.assertEqual(self.client.get(f"/api/v1/{route}").status_code, 401)
            self.assertEqual(self.client.post(f"/api/v1/{route}", json={}).status_code, 401)
        with self.Session() as db:
            db.get(User, self.admin).role = "technician"
            db.commit()
        self.assertEqual(self.client.get("/api/v1/audit-logs", headers=self.headers).status_code, 403)
        self.assertEqual(self.client.post("/api/v1/audit-logs", headers=self.headers,
                                          json={"action": "explicit"}).status_code, 403)
        self._notification()

    def test_business_writes_do_not_generate_unapproved_automatic_events(self):
        before = self._counts()
        response = self.client.post("/api/v1/work-orders", headers=self.headers,
                                    json={"customer_id": str(self.customer), "title": "Explicit order"})
        self.assertEqual(response.status_code, 201, response.text)
        response = self.client.post("/api/v1/expenses", headers=self.headers,
                                    json={"category": "Travel", "amount": "5", "expense_date": "2026-10-02"})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(self._counts(), before)


if __name__ == "__main__":
    unittest.main()
