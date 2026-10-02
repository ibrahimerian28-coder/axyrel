"""Task 52 / OD-14 integration, using a dedicated disposable PostgreSQL database.

The configured credentials must permit CREATE DATABASE on the local test server.
The configured application database is never connected to or changed by this suite.
"""
import os
from datetime import datetime, timezone
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
from backend.core.event_time import normalize_event_time
from backend.core.security import create_access_token, hash_password
from backend.main import app as application
from backend.models.base import Base
from backend.models.company import Company
from backend.models.customer import Customer
from backend.models.schedule import Schedule
from backend.models.user import User
from backend.models.work_order import WorkOrder
from backend.services.schedule import ScheduleService


def dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class Task52SchedulingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = make_url(get_settings().database_url)
        if url.get_backend_name() != "postgresql":
            raise RuntimeError("Task 52 migration verification requires local PostgreSQL")
        cls.database_name = "axyrel_task52_test_" + uuid4().hex
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
        if not cls.database_name.startswith("axyrel_task52_test_") or len(cls.database_name) != 51:
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
                                 start_at=dt("2026-01-15T08:00Z"), end_at=dt("2026-01-15T10:00Z")),
                        Schedule(id=self.foreign_schedule, company_id=self.other_company,
                                 work_order_id=self.foreign_order, start_at=dt("2026-01-15T08:00Z"),
                                 end_at=dt("2026-01-15T10:00Z"))])
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
        return self.client.post("/api/v1/schedules", headers=self.headers,
                                json={"work_order_id": str(self.order), "start_at": "2026-01-15T10:00:00",
                                      "end_at": "2026-01-15T12:00:00", **data})

    def _patch(self, data, schedule_id=None):
        return self.client.patch(f"/api/v1/schedules/{schedule_id or self.schedule}",
                                 headers=self.headers, json=data)

    def _read(self):
        with self.Session() as db:
            record = db.get(Schedule, self.schedule)
            return record.start_at, record.end_at, record.work_order_id, record.notes

    def _count(self):
        with self.Session() as db:
            return db.scalar(select(func.count()).select_from(Schedule))

    def test_aware_input_respects_offset(self):
        self.assertEqual(normalize_event_time(dt("2026-01-15T12:00+04:00")), dt("2026-01-15T08:00Z"))

    def test_naive_winter_input_is_cairo_not_utc(self):
        self.assertEqual(normalize_event_time(dt("2026-01-15T10:00")), dt("2026-01-15T08:00Z"))

    def test_naive_summer_input_uses_cairo_dst(self):
        self.assertEqual(normalize_event_time(dt("2026-07-15T10:00")), dt("2026-07-15T07:00Z"))

    def test_ambiguous_naive_input_requires_offset(self):
        with self.assertRaisesRegex(ValueError, "explicit UTC offset"):
            normalize_event_time(dt("2026-10-29T23:30"))

    def test_nonexistent_naive_input_requires_offset(self):
        with self.assertRaisesRegex(ValueError, "explicit UTC offset"):
            normalize_event_time(dt("2026-04-24T00:30"))

    def test_explicit_offsets_disambiguate_overlap(self):
        early = normalize_event_time(dt("2026-10-29T23:30+03:00"))
        late = normalize_event_time(dt("2026-10-29T23:30+02:00"))
        self.assertEqual((late - early).total_seconds(), 3600)

    def test_api_naive_creation_read_filter_and_utc_output(self):
        response = self._create()
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(dt(response.json()["start_at"]), dt("2026-01-15T08:00Z"))
        self.assertTrue(response.json()["start_at"].endswith(("Z", "+00:00")))
        fetched = self.client.get(f'/api/v1/schedules/{response.json()["id"]}', headers=self.headers)
        self.assertEqual(fetched.json(), response.json())
        listed = self.client.get("/api/v1/schedules", headers=self.headers,
                                 params={"work_order_id": str(self.order), "start_from": "2026-01-15T10:00",
                                         "start_to": "2026-01-15T08:00Z"})
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertIn(response.json()["id"], [record["id"] for record in listed.json()])

    def test_work_order_api_creation_to_schedule_integration(self):
        order = self.client.post("/api/v1/work-orders", headers=self.headers,
                                 json={"customer_id": str(self.customer), "title": "API order"})
        self.assertEqual(order.status_code, 201, order.text)
        schedule = self._create(work_order_id=order.json()["id"])
        self.assertEqual(schedule.status_code, 201, schedule.text)
        self.assertEqual(schedule.json()["work_order_id"], order.json()["id"])
        listed = self.client.get("/api/v1/schedules", headers=self.headers,
                                 params={"work_order_id": order.json()["id"]})
        self.assertEqual([row["id"] for row in listed.json()], [schedule.json()["id"]])

    def test_create_compares_instants_not_local_clock_order(self):
        response = self._create(start_at="2026-01-15T12:00+04:00", end_at="2026-01-15T11:00")
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(dt(response.json()["end_at"]), dt("2026-01-15T09:00Z"))

    def test_create_invalid_effective_range_is_rejected(self):
        before = self._count()
        response = self._create(start_at="2026-01-15T10:00Z", end_at="2026-01-15T11:00")
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self._count(), before)

    def test_create_gap_and_overlap_rejected_without_persistence(self):
        for value in ("2026-04-24T00:30", "2026-10-29T23:30"):
            with self.subTest(value=value):
                before = self._count()
                response = self._create(start_at=value)
                self.assertEqual(response.status_code, 422, response.text)
                self.assertEqual(self._count(), before)

    def test_postgres_reload_preserves_instant_independent_of_session_timezone(self):
        created = self._create(start_at="2026-01-15T12:00+04:00")
        self.assertEqual(created.status_code, 201, created.text)
        with self.Session() as db:
            db.execute(text("SET LOCAL TIME ZONE 'America/New_York'"))
            record = db.get(Schedule, created.json()["id"])
            self.assertIsNotNone(record.start_at.utcoffset())
            self.assertEqual(record.start_at, dt("2026-01-15T08:00Z"))

    def test_direct_service_normalizes_and_rejects_invalid_range(self):
        with self.Session() as db:
            service = ScheduleService()
            record = service.create_schedule(db, self.company, {"work_order_id": self.order,
                                              "start_at": dt("2026-01-15T10:00"),
                                              "end_at": dt("2026-01-15T11:00")})
            self.assertEqual(record.start_at, dt("2026-01-15T08:00Z"))
            before = db.scalar(select(func.count()).select_from(Schedule))
            with self.assertRaisesRegex(ValueError, "later than"):
                service.create_schedule(db, self.company, {"work_order_id": self.order,
                                         "start_at": dt("2026-01-15T10:00Z"), "end_at": dt("2026-01-15T11:00")})
            self.assertEqual(db.scalar(select(func.count()).select_from(Schedule)), before)

    def test_patch_end_compares_persisted_start_without_partial_mutation(self):
        before = self._read()
        response = self._patch({"end_at": "2026-01-15T09:00", "notes": "Must not persist"})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(self._read(), before)

    def test_patch_start_compares_persisted_end(self):
        before = self._read()
        response = self._patch({"start_at": "2026-01-15T13:00"})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(self._read(), before)

    def test_patch_one_naive_timestamp_preserves_aware_counterpart(self):
        response = self._patch({"start_at": "2026-01-15T11:00"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self._read()[:2], (dt("2026-01-15T09:00Z"), dt("2026-01-15T10:00Z")))

    def test_patch_both_mixed_timestamps_and_notes_only_remain_valid(self):
        response = self._patch({"start_at": "2026-01-15T12:00+04:00", "end_at": "2026-01-15T11:00"})
        self.assertEqual(response.status_code, 200, response.text)
        before = self._read()[:2]
        response = self._patch({"notes": "Notes only"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self._read()[:2], before)

    def test_patch_equal_instants_rejected(self):
        response = self._patch({"end_at": "2026-01-15T10:00+02:00"})
        self.assertEqual(response.status_code, 400, response.text)

    def test_direct_service_patch_rejects_gap_before_mutation(self):
        with self.Session() as db:
            record = db.get(Schedule, self.schedule)
            with self.assertRaisesRegex(ValueError, "explicit UTC offset"):
                ScheduleService().update_schedule(db, self.company, self.schedule,
                                                  {"start_at": dt("2026-04-24T00:30"), "notes": "No"})
            self.assertIsNone(record.notes)

    def test_missing_foreign_deleted_work_orders_rejected_on_create(self):
        for order in (uuid4(), self.foreign_order, self.deleted_order):
            with self.subTest(order=order):
                before = self._count()
                response = self._create(work_order_id=str(order))
                self.assertEqual(response.status_code, 400, response.text)
                self.assertEqual(response.json(), {"detail": "Work order not found."})
                self.assertEqual(self._count(), before)

    def test_direct_service_rejects_foreign_parent_before_persistence(self):
        with self.Session() as db:
            before = db.scalar(select(func.count()).select_from(Schedule))
            with self.assertRaisesRegex(ValueError, "Work order not found"):
                ScheduleService().create_schedule(db, self.company, {"work_order_id": self.foreign_order,
                                                  "start_at": dt("2026-01-15T10:00"),
                                                  "end_at": dt("2026-01-15T12:00")})
            self.assertEqual(db.scalar(select(func.count()).select_from(Schedule)), before)

    def test_invalid_reassignment_prevents_partial_mutation(self):
        before = self._read()
        for order in (uuid4(), self.foreign_order, self.deleted_order):
            response = self._patch({"work_order_id": str(order), "notes": "Must not persist"})
            self.assertEqual(response.status_code, 400, response.text)
            self.assertEqual(self._read(), before)

    def test_valid_reassignment_preserves_explicit_technician_without_inheritance(self):
        response = self._patch({"work_order_id": str(self.other_order), "technician_id": str(self.technician)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["work_order_id"], str(self.other_order))
        self.assertEqual(response.json()["technician_id"], str(self.technician))
        created = self._create(work_order_id=str(self.other_order))
        self.assertEqual(created.status_code, 201, created.text)
        self.assertIsNone(created.json()["technician_id"])

    def test_missing_hidden_schedule_preserves_404_precedence(self):
        for schedule in (uuid4(), self.foreign_schedule):
            response = self._patch({"work_order_id": str(uuid4()), "end_at": "2026-01-01T00:00Z"}, schedule)
            self.assertEqual(response.status_code, 404, response.text)

    def test_tenant_get_list_and_delete_isolation(self):
        listed = self.client.get("/api/v1/schedules", headers=self.headers)
        self.assertEqual([record["id"] for record in listed.json()], [str(self.schedule)])
        response = self.client.get(f"/api/v1/schedules/{self.foreign_schedule}", headers=self.headers)
        self.assertEqual(response.status_code, 404, response.text)
        response = self.client.delete(f"/api/v1/schedules/{self.foreign_schedule}", headers=self.headers)
        self.assertEqual(response.status_code, 404, response.text)

    def test_query_gap_rejected_and_authentication_still_required(self):
        response = self.client.get("/api/v1/schedules", headers=self.headers,
                                   params={"start_from": "2026-04-24T00:30"})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(self.client.get("/api/v1/schedules").status_code, 401)

    def _historical_migration(self, start, end):
        connection = self.engine.raw_connection()
        connection.driver_connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute("CREATE SCHEMA history")
        cursor.execute("SET search_path TO history")
        cursor.execute("CREATE TABLE schedules (start_at TIMESTAMP NOT NULL, end_at TIMESTAMP NOT NULL, created_at TIMESTAMP)")
        cursor.execute("INSERT INTO schedules VALUES (%s, %s, %s)", (dt(start), dt(end), dt("2026-01-01T01:02")))
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
        return (Path(__file__).resolve().parents[1] / "migrations/012_schedule_event_timezone.sql").read_text()

    def test_historical_migration_preserves_cairo_meaning_and_other_columns(self):
        _, cursor = self._historical_migration("2026-01-15T10:00", "2026-07-15T10:00")
        cursor.execute("SET TIME ZONE 'America/New_York'")
        cursor.execute(self._migration_sql(), prepare=False)
        cursor.execute("SELECT start_at, end_at, created_at FROM schedules")
        start, end, created = cursor.fetchone()
        self.assertEqual(start, dt("2026-01-15T08:00Z"))
        self.assertEqual(end, dt("2026-07-15T07:00Z"))
        self.assertEqual(created, dt("2026-01-01T01:02"))
        cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='history' ORDER BY column_name")
        self.assertEqual(dict(cursor.fetchall()), {"created_at": "timestamp without time zone",
                         "start_at": "timestamp with time zone", "end_at": "timestamp with time zone"})

    def _assert_migration_rejected(self, start, end, message):
        _, cursor = self._historical_migration(start, end)
        with self.assertRaisesRegex(Exception, message):
            cursor.execute(self._migration_sql(), prepare=False)
        cursor.execute("ROLLBACK")
        cursor.execute("SELECT start_at FROM schedules")
        self.assertEqual(cursor.fetchone()[0], dt(start))
        cursor.execute("SELECT data_type FROM information_schema.columns WHERE table_schema='history' AND column_name='start_at'")
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
        cursor.execute("SELECT start_at FROM schedules")
        self.assertEqual(cursor.fetchone()[0], dt("2026-01-15T08:00Z"))

    def test_empty_historical_table_migrates(self):
        _, cursor = self._historical_migration("2026-01-15T10:00", "2026-01-15T12:00")
        cursor.execute("DELETE FROM schedules")
        cursor.execute(self._migration_sql(), prepare=False)
        cursor.execute("SELECT count(*) FROM schedules")
        self.assertEqual(cursor.fetchone()[0], 0)
        cursor.execute("SELECT data_type FROM information_schema.columns WHERE table_schema='history' AND column_name='end_at'")
        self.assertEqual(cursor.fetchone()[0], "timestamp with time zone")


if __name__ == "__main__":
    unittest.main()
