"""Task 53 / OD-14 integration, using a dedicated disposable PostgreSQL database.

The configured credentials must permit CREATE DATABASE on the local test server.
The configured application database is never connected to or changed by this suite.
"""
import os
from datetime import datetime
from pathlib import Path
import unittest
from uuid import uuid4

os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes-123456"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import backend.models
from backend.api.v1 import router
from backend.core.config import get_settings
from backend.core.database import get_db
from backend.core.security import create_access_token, hash_password
from backend.main import app as application
from backend.models.base import Base
from backend.models.company import Company
from backend.models.customer import Customer
from backend.models.schedule import Schedule
from backend.models.user import User
from backend.models.work_order import WorkOrder
from backend.services.service_visit import ServiceVisitService
from backend.models.service_visit import ServiceVisit


def dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class Task53ServiceVisitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = make_url(get_settings().database_url)
        if url.get_backend_name() != "postgresql":
            raise RuntimeError("Task 53 migration verification requires local PostgreSQL")
        cls.database_name = "axyrel_task53_test_" + uuid4().hex
        cls.admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
        with cls.admin_engine.connect() as db:
            db.exec_driver_sql(f'CREATE DATABASE "{cls.database_name}"')
        cls.addClassCleanup(cls._drop_database)
        cls.engine = create_engine(url.set(database=cls.database_name))
        cls.addClassCleanup(cls.engine.dispose)
        cls.Session = sessionmaker(bind=cls.engine, autoflush=False)
        Base.metadata.create_all(cls.engine)
        cls.password_hash = hash_password("Password123!")

    @classmethod
    def _drop_database(cls):
        # This name is generated above, never derived from the configured application DB.
        if not cls.database_name.startswith("axyrel_task53_test_") or len(cls.database_name) != 51:
            raise RuntimeError("Refusing unexpected disposable database name")
        with cls.admin_engine.connect() as db:
            db.exec_driver_sql(f'DROP DATABASE "{cls.database_name}"')
        cls.admin_engine.dispose()

    def setUp(self):
        self.company, self.other_company, self.customer, self.foreign_customer = [uuid4() for _ in range(4)]
        self.order, self.other_order, self.foreign_order, self.deleted_order = [uuid4() for _ in range(4)]
        self.schedule, self.foreign_schedule, self.admin, self.technician = [uuid4() for _ in range(4)]
        with self.Session() as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            db.add_all([Company(id=self.company, name="A", status="active"),
                        Company(id=self.other_company, name="B", status="active")])
            db.flush()
            db.add_all([Customer(id=self.customer, company_id=self.company, name="A"),
                        Customer(id=self.foreign_customer, company_id=self.other_company, name="B"),
                        User(id=self.admin, company_id=self.company, email="admin@example.com", full_name="Admin",
                             role="admin", password_hash=self.password_hash)])
            db.flush()
            db.add_all([WorkOrder(id=self.order, company_id=self.company, customer_id=self.customer, title="Order"),
                        WorkOrder(id=self.other_order, company_id=self.company, customer_id=self.customer,
                                  title="Other", assigned_technician_id=uuid4()),
                        WorkOrder(id=self.foreign_order, company_id=self.other_company,
                                  customer_id=self.foreign_customer, title="Foreign"),
                        WorkOrder(id=self.deleted_order, company_id=self.company, customer_id=self.customer,
                                  title="Deleted", status="Deleted")])
            db.flush()
            db.add_all([Schedule(id=self.schedule, company_id=self.company, work_order_id=self.order,
                                 technician_id=uuid4(),
                                 start_at=dt("2026-01-15T08:00Z"), end_at=dt("2026-01-15T10:00Z")),
                        Schedule(id=self.foreign_schedule, company_id=self.other_company,
                                 work_order_id=self.foreign_order, start_at=dt("2026-01-15T08:00Z"),
                                 end_at=dt("2026-01-15T10:00Z"))])
            db.commit()
        self.visit, self.foreign_visit, self.deleted_schedule = [uuid4() for _ in range(3)]
        with self.Session() as db:
            db.add(Schedule(id=self.deleted_schedule, company_id=self.company, work_order_id=self.order,
                            start_at=dt("2026-01-15T08:00Z"), end_at=dt("2026-01-15T10:00Z"), status="Deleted"))
            db.flush()
            db.add_all([ServiceVisit(id=self.visit, company_id=self.company, work_order_id=self.order,
                                     customer_id=self.customer, schedule_id=self.schedule,
                                     actual_start_at=dt("2026-01-15T08:00Z"), actual_end_at=dt("2026-01-15T10:00Z")),
                        ServiceVisit(id=self.foreign_visit, company_id=self.other_company,
                                     work_order_id=self.foreign_order, customer_id=self.foreign_customer)])
            db.commit()
        app = FastAPI()
        app.exception_handlers.update(application.exception_handlers)
        app.include_router(router, prefix="/api/v1")

        def disposable_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = disposable_db
        self.client = TestClient(app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)
        self.headers = {"Authorization": f"Bearer {create_access_token(str(self.admin))}"}


    def _create(self, **data):
        return self.client.post("/api/v1/service-visits", headers=self.headers,
                                json={"work_order_id": str(self.order), "customer_id": str(self.customer),
                                      "schedule_id": str(self.schedule), "actual_start_at": "2026-01-15T10:00",
                                      "actual_end_at": "2026-01-15T12:00", **data})

    def _patch(self, data, visit_id=None):
        return self.client.patch(f"/api/v1/service-visits/{visit_id or self.visit}",
                                 headers=self.headers, json=data)

    def _read(self):
        with self.Session() as db:
            record = db.get(ServiceVisit, self.visit)
            return (record.actual_start_at, record.actual_end_at, record.schedule_id, record.notes, record.status)

    def _count(self):
        with self.Session() as db:
            return db.scalar(select(func.count()).select_from(ServiceVisit))

    def test_schedule_api_creation_to_visit_read_and_filter(self):
        schedule = self.client.post("/api/v1/schedules", headers=self.headers,
                                    json={"work_order_id": str(self.order), "start_at": "2026-01-15T10:00",
                                          "end_at": "2026-01-15T12:00"})
        self.assertEqual(schedule.status_code, 201, schedule.text)
        visit = self._create(schedule_id=schedule.json()["id"])
        self.assertEqual(visit.status_code, 201, visit.text)
        fetched = self.client.get(f'/api/v1/service-visits/{visit.json()["id"]}', headers=self.headers)
        self.assertEqual(fetched.json(), visit.json())
        listed = self.client.get("/api/v1/service-visits", headers=self.headers,
                                 params={"schedule_id": schedule.json()["id"]})
        self.assertEqual([row["id"] for row in listed.json()], [visit.json()["id"]])

    def test_missing_foreign_deleted_schedule_rejected_before_create(self):
        for schedule in (uuid4(), self.foreign_schedule, self.deleted_schedule):
            with self.subTest(schedule=schedule):
                before = self._count()
                response = self._create(schedule_id=str(schedule))
                self.assertEqual(response.status_code, 400, response.text)
                self.assertEqual(response.json(), {"detail": "Schedule not found."})
                self.assertEqual(self._count(), before)

    def test_invalid_patch_link_does_not_mutate_or_cancel_work_order(self):
        before = self._read()
        for schedule in (uuid4(), self.foreign_schedule, self.deleted_schedule):
            response = self._patch({"schedule_id": str(schedule), "notes": "No", "status": "Cancelled"})
            self.assertEqual(response.status_code, 400, response.text)
            self.assertEqual(self._read(), before)
            with self.Session() as db:
                self.assertEqual(db.get(WorkOrder, self.order).status, "Open")

    def test_schedule_and_visit_must_belong_to_same_work_order(self):
        before = self._count()
        created = self._create(work_order_id=str(self.other_order))
        self.assertEqual(created.status_code, 400, created.text)
        self.assertEqual(self._count(), before)
        patched = self._patch({"work_order_id": str(self.other_order)})
        self.assertEqual(patched.status_code, 400, patched.text)
        # Explicitly detach the appointment before administrative reassignment.
        patched = self._patch({"work_order_id": str(self.other_order), "schedule_id": None})
        self.assertEqual(patched.status_code, 200, patched.text)

    def test_optional_link_omission_null_detachment_and_reassignment(self):
        linked = self._create(technician_id=None, actual_start_at=None, actual_end_at=None)
        self.assertEqual(linked.status_code, 201, linked.text)
        self.assertIsNone(linked.json()["technician_id"])
        self.assertIsNone(linked.json()["actual_start_at"])
        for payload in ({"schedule_id": None}, {}):
            values = {"work_order_id": str(self.order), "customer_id": str(self.customer), **payload}
            response = self.client.post("/api/v1/service-visits", headers=self.headers, json=values)
            self.assertEqual(response.status_code, 201, response.text)
            self.assertIsNone(response.json()["schedule_id"])
            self.assertIsNone(response.json()["actual_start_at"])
            self.assertIsNone(response.json()["technician_id"])
        response = self._patch({"notes": "Keep link"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["schedule_id"], str(self.schedule))
        response = self._patch({"schedule_id": None})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["schedule_id"])
        response = self._patch({"schedule_id": str(self.schedule)})
        self.assertEqual(response.status_code, 200, response.text)

    def test_missing_hidden_visit_retains_404_precedence(self):
        for visit in (uuid4(), self.foreign_visit):
            response = self._patch({"schedule_id": str(uuid4()), "actual_end_at": "2026-01-01T00:00Z"}, visit)
            self.assertEqual(response.status_code, 404, response.text)

    def test_direct_service_link_and_range_validation_before_mutation(self):
        with self.Session() as db:
            service = ServiceVisitService()
            data = {"work_order_id": self.order, "customer_id": self.customer,
                    "schedule_id": self.foreign_schedule}
            with self.assertRaisesRegex(ValueError, "Schedule not found"):
                service.create_visit(db, self.company, data)
            before = db.scalar(select(func.count()).select_from(ServiceVisit))
            with self.assertRaisesRegex(ValueError, "later than or equal"):
                service.create_visit(db, self.company, {**data, "schedule_id": self.schedule,
                                     "actual_start_at": dt("2026-01-15T12:00Z"),
                                     "actual_end_at": dt("2026-01-15T12:00")})
            self.assertEqual(db.scalar(select(func.count()).select_from(ServiceVisit)), before)
            with self.assertRaisesRegex(ValueError, "Schedule not found"):
                service.update_visit(db, self.company, self.visit,
                                     {"schedule_id": self.foreign_schedule, "status": "Cancelled"})
            with self.assertRaisesRegex(ValueError, "later than or equal"):
                service.update_visit(db, self.company, self.visit,
                                     {"actual_end_at": dt("2026-01-15T09:00"), "notes": "No"})
            self.assertIsNone(db.get(ServiceVisit, self.visit).notes)
            created = service.create_visit(db, self.company, {"work_order_id": self.order,
                                            "customer_id": self.customer, "actual_start_at": dt("2026-01-15T10:00")})
            self.assertEqual(created.actual_start_at, dt("2026-01-15T08:00Z"))

    def test_naive_cairo_aware_offsets_and_mixed_ranges(self):
        for start, end, expected in (("2026-01-15T10:00", "2026-01-15T12:00", "2026-01-15T08:00Z"),
                                     ("2026-07-15T10:00", "2026-07-15T11:00", "2026-07-15T07:00Z"),
                                     ("2026-01-15T12:00+04:00", "2026-01-15T11:00", "2026-01-15T08:00Z")):
            response = self._create(actual_start_at=start, actual_end_at=end)
            self.assertEqual(response.status_code, 201, response.text)
            self.assertEqual(dt(response.json()["actual_start_at"]), dt(expected))
            self.assertTrue(response.json()["actual_start_at"].endswith(("Z", "+00:00")))

    def test_invalid_create_range_and_dst_rejected_without_persistence(self):
        for start, end in (("2026-01-15T10:00Z", "2026-01-15T11:00"),
                           ("2026-04-24T00:30", None), ("2026-10-29T23:30", None)):
            before = self._count()
            response = self._create(actual_start_at=start, actual_end_at=end)
            self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(self._count(), before)

    def test_explicit_dst_offsets_and_equal_instants_are_allowed(self):
        for start, end in (("2026-10-29T23:30+03:00", "2026-10-29T23:30+02:00"),
                           ("2026-01-15T10:00+02:00", "2026-01-15T08:00Z")):
            response = self._create(actual_start_at=start, actual_end_at=end)
            self.assertEqual(response.status_code, 201, response.text)
        response = self._patch({"actual_end_at": "2026-01-15T10:00+02:00"})
        self.assertEqual(response.status_code, 200, response.text)

    def test_effective_patch_ranges_rejected_without_partial_mutation(self):
        before = self._read()
        for payload in ({"actual_end_at": "2026-01-15T09:00", "notes": "No"},
                         {"actual_start_at": "2026-01-15T13:00", "status": "Cancelled"}):
            response = self._patch(payload)
            self.assertEqual(response.status_code, 400, response.text)
            self.assertEqual(self._read(), before)

    def test_patch_null_time_and_one_timestamp_and_notes_preserve_contract(self):
        response = self._patch({"actual_start_at": "2026-01-15T11:00"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self._read()[:2], (dt("2026-01-15T09:00Z"), dt("2026-01-15T10:00Z")))
        response = self._patch({"actual_start_at": None, "notes": "Clear"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["actual_start_at"])
        self.assertEqual(dt(response.json()["actual_end_at"]), dt("2026-01-15T10:00Z"))

    def test_direct_service_and_patch_dst_validation(self):
        for value in ("2026-04-24T00:30", "2026-10-29T23:30"):
            response = self._patch({"actual_start_at": value})
            self.assertEqual(response.status_code, 422, response.text)
            with self.Session() as db:
                with self.assertRaisesRegex(ValueError, "explicit UTC offset"):
                    ServiceVisitService().update_visit(db, self.company, self.visit,
                                                       {"actual_start_at": dt(value), "notes": "No"})
                self.assertIsNone(db.get(ServiceVisit, self.visit).notes)

    def test_query_time_policy_auth_and_tenant_isolation(self):
        listed = self.client.get("/api/v1/service-visits", headers=self.headers,
                                 params={"start_from": "2026-01-15T10:00", "start_to": "2026-01-15T08:00Z"})
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual([row["id"] for row in listed.json()], [str(self.visit)])
        bad = self.client.get("/api/v1/service-visits", headers=self.headers,
                              params={"start_from": "2026-04-24T00:30"})
        self.assertEqual(bad.status_code, 400, bad.text)
        self.assertEqual(self.client.get("/api/v1/service-visits").status_code, 401)
        for method in (self.client.get, self.client.delete):
            response = method(f"/api/v1/service-visits/{self.foreign_visit}", headers=self.headers)
            self.assertEqual(response.status_code, 404, response.text)

    def test_postgres_reload_preserves_instant_under_other_timezone(self):
        created = self._create(actual_start_at="2026-01-15T12:00+04:00")
        self.assertEqual(created.status_code, 201, created.text)
        with self.Session() as db:
            db.execute(text("SET LOCAL TIME ZONE 'America/New_York'"))
            record = db.get(ServiceVisit, created.json()["id"])
            self.assertIsNotNone(record.actual_start_at.utcoffset())
            self.assertEqual(record.actual_start_at, dt("2026-01-15T08:00Z"))

    def test_historical_nullable_and_equal_range_migrate(self):
        _, cursor = self._historical_migration("2026-01-15T10:00", "2026-01-15T10:00")
        cursor.execute("INSERT INTO service_visits VALUES (NULL, NULL, NULL), (NULL, '2026-07-15 10:00', NULL)")
        cursor.execute(self._migration_sql(), prepare=False)
        cursor.execute("SELECT actual_start_at, actual_end_at FROM service_visits ORDER BY actual_end_at NULLS FIRST")
        self.assertEqual(cursor.fetchall(), [(None, None), (dt("2026-01-15T08:00Z"), dt("2026-01-15T08:00Z")),
                                             (None, dt("2026-07-15T07:00Z"))])
        cursor.execute("SELECT is_nullable FROM information_schema.columns WHERE table_schema='history' "
                       "AND column_name IN ('actual_start_at', 'actual_end_at')")
        self.assertEqual(cursor.fetchall(), [("YES",), ("YES",)])

    def _historical_migration(self, start, end):
        connection = self.engine.raw_connection()
        connection.driver_connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute("CREATE SCHEMA history")
        cursor.execute("SET search_path TO history")
        cursor.execute("CREATE TABLE service_visits (actual_start_at TIMESTAMP NULL, actual_end_at TIMESTAMP NULL, created_at TIMESTAMP)")
        cursor.execute("INSERT INTO service_visits VALUES (%s, %s, %s)", (dt(start), dt(end), dt("2026-01-01T01:02")))
        self.addCleanup(self._cleanup_history, connection, cursor)
        return connection, cursor

    @staticmethod
    def _cleanup_history(connection, cursor):
        cursor.execute("ROLLBACK")
        cursor.execute("SET search_path TO public")
        cursor.execute("RESET TIME ZONE")
        cursor.execute("DROP SCHEMA history CASCADE")
        cursor.close()
        connection.close()

    def _migration_sql(self):
        return (Path(__file__).resolve().parents[1] / "migrations/013_service_visit_event_timezone.sql").read_text()

    def test_historical_migration_preserves_cairo_meaning_and_other_columns(self):
        _, cursor = self._historical_migration("2026-01-15T10:00", "2026-07-15T10:00")
        cursor.execute("SET TIME ZONE 'America/New_York'")
        cursor.execute(self._migration_sql(), prepare=False)
        cursor.execute("SELECT actual_start_at, actual_end_at, created_at FROM service_visits")
        start, end, created = cursor.fetchone()
        self.assertEqual(start, dt("2026-01-15T08:00Z"))
        self.assertEqual(end, dt("2026-07-15T07:00Z"))
        self.assertEqual(created, dt("2026-01-01T01:02"))
        cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='history' ORDER BY column_name")
        self.assertEqual(dict(cursor.fetchall()), {"created_at": "timestamp without time zone",
                         "actual_start_at": "timestamp with time zone", "actual_end_at": "timestamp with time zone"})

    def _assert_migration_rejected(self, start, end, message):
        _, cursor = self._historical_migration(start, end)
        with self.assertRaisesRegex(Exception, message):
            cursor.execute(self._migration_sql(), prepare=False)
        cursor.execute("ROLLBACK")
        cursor.execute("SELECT actual_start_at FROM service_visits")
        self.assertEqual(cursor.fetchone()[0], dt(start))
        cursor.execute("SELECT data_type FROM information_schema.columns WHERE table_schema='history' AND column_name='actual_start_at'")
        self.assertEqual(cursor.fetchone()[0], "timestamp without time zone")

    def test_historical_migration_rejects_gap_atomically(self):
        self._assert_migration_rejected("2026-04-24T00:30", "2026-04-24T02:00", "Unresolved Cairo")

    def test_historical_migration_rejects_overlap_atomically(self):
        self._assert_migration_rejected("2026-10-29T23:30", "2026-10-30T02:00", "Unresolved Cairo")

    def test_historical_migration_rejects_invalid_range_atomically(self):
        self._assert_migration_rejected("2026-01-15T12:00", "2026-01-15T10:00", "Invalid historical")

    def test_historical_migration_refuses_second_conversion(self):
        _, cursor = self._historical_migration("2026-01-15T10:00", "2026-01-15T12:00")
        cursor.execute(self._migration_sql(), prepare=False)
        with self.assertRaisesRegex(Exception, "Expected two naive"):
            cursor.execute(self._migration_sql(), prepare=False)
        cursor.execute("ROLLBACK")
        cursor.execute("SELECT actual_start_at FROM service_visits")
        self.assertEqual(cursor.fetchone()[0], dt("2026-01-15T08:00Z"))

    def test_empty_historical_table_migrates(self):
        _, cursor = self._historical_migration("2026-01-15T10:00", "2026-01-15T12:00")
        cursor.execute("DELETE FROM service_visits")
        cursor.execute(self._migration_sql(), prepare=False)
        cursor.execute("SELECT count(*) FROM service_visits")
        self.assertEqual(cursor.fetchone()[0], 0)
        cursor.execute("SELECT data_type FROM information_schema.columns WHERE table_schema='history' AND column_name='actual_end_at'")
        self.assertEqual(cursor.fetchone()[0], "timestamp with time zone")


if __name__ == "__main__":
    unittest.main()
