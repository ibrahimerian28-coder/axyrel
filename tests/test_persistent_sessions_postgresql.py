"""Apply the additive migration and restart real backends on a generated DB."""
import contextlib
import os
import signal
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from uuid import uuid4

import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.security import hash_password
from backend.models.company import Company
from backend.models.user import User
from backend.scripts.init_database import apply_migrations

ROOT = Path(__file__).resolve().parents[1]


class PostgreSQLPersistentSessionTests(unittest.TestCase):
    def test_migration_time_passage_process_restart_and_revocation(self):
        url = make_url(get_settings().database_url)
        self.assertIn(url.host, {"localhost", "127.0.0.1", "::1"})
        self.assertEqual(url.get_backend_name(), "postgresql")
        name = "axyrel_task60_test_" + uuid4().hex
        admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
        with admin.connect() as db:
            db.exec_driver_sql(f'CREATE DATABASE "{name}"')
        # Retain disposable DB for review; never touch the configured operational DB.
        admin.dispose()
        test_url = url.set(database=name)
        engine = create_engine(test_url)
        self.addCleanup(engine.dispose)
        with contextlib.redirect_stdout(__import__("io").StringIO()):
            apply_migrations(engine, ROOT / "migrations")
        with Session(engine) as db:
            company = Company(id=uuid4(), name="Disposable Sessions", status="active")
            db.add(company); db.flush()
            db.add(User(id=uuid4(), company_id=company.id, email="restart@example.test", full_name="Restart", role="admin", password_hash=hash_password("synthetic-password")))
            db.commit()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
        with tempfile.TemporaryDirectory(prefix="axyrel-session-restart-") as folder:
            env = {**os.environ, "DATABASE_URL": test_url.render_as_string(hide_password=False), "AXYREL_ENV": "test", "SECRET_KEY": "synthetic-restart-only-secret-at-least-32-bytes", "PYTHONPATH": str(ROOT)}
            def start():
                marker = Path(folder) / ("server-pid-" + uuid4().hex)
                child_env = {**env, "AXYREL_RESTART_PID_FILE": str(marker), "AXYREL_RESTART_PORT": str(port)}
                bootstrap = "import os; from pathlib import Path; Path(os.environ['AXYREL_RESTART_PID_FILE']).write_text(str(os.getpid())); import uvicorn; uvicorn.run('backend.main:app', host='127.0.0.1', port=int(os.environ['AXYREL_RESTART_PORT']), access_log=False)"
                process = subprocess.Popen([sys.executable, "-B", "-c", bootstrap], cwd=folder, env=child_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.pid_marker = marker
                deadline = time.monotonic() + 45
                while time.monotonic() < deadline:
                    try:
                        if httpx.get(f"http://127.0.0.1:{port}/health", timeout=1).status_code == 200:
                            return process
                    except httpx.HTTPError:
                        pass
                    if process.poll() is not None: self.fail("Disposable backend failed to start")
                    time.sleep(.2)
                stop(process)
                self.fail("Disposable backend startup timed out")
            def stop(process):
                # Windows venv python.exe can be a launcher with a different child
                # PID. The bootstrap records the PID that actually runs uvicorn.
                if process.pid_marker.exists():
                    actual_pid = int(process.pid_marker.read_text())
                    try:
                        os.kill(actual_pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                elif process.poll() is None:
                    process.terminate()
                process.wait(timeout=10)
            base = f"http://127.0.0.1:{port}/api/v1"
            process = start()
            try:
                response = httpx.post(base + "/auth/sessions", data={"username": "restart@example.test", "password": "synthetic-password"}, timeout=30)
                self.assertEqual(response.status_code, 200)
                credential = response.json()["access_token"]
                headers = {"Authorization": "Bearer " + credential}
                with engine.begin() as db:
                    db.execute(text("UPDATE auth_sessions SET created_at = '1990-01-01T00:00:00Z'"))
                first_pid = int(process.pid_marker.read_text())
                stop(process)
                # A fresh process and a changed JWT signing key must preserve opaque sessions.
                env["SECRET_KEY"] = "synthetic-new-signing-key-at-least-32-bytes"
                process = start()
                self.assertNotEqual(int(process.pid_marker.read_text()), first_pid)
                self.assertEqual(httpx.get(base + "/auth/me", headers=headers, timeout=30).status_code, 200)
                self.assertEqual(httpx.post(base + "/auth/sessions/logout", headers=headers, timeout=30).status_code, 204)
                self.assertEqual(httpx.get(base + "/auth/me", headers=headers, timeout=30).status_code, 401)
                with engine.connect() as db:
                    self.assertIsNotNone(db.execute(text("SELECT revoked_at FROM auth_sessions")).scalar_one())
            finally:
                if process.poll() is None:
                    stop(process)
