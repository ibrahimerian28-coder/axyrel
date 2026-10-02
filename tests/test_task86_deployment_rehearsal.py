"""Production-mode local processes and tracked disposable PostgreSQL; no real target."""
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from uuid import uuid4

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session
import test_task60_tracked_migrations as fixture
from backend.core.security import hash_password
from backend.models.company import Company
from backend.models.user import User
import backend.models  # register accepted relationships


SERVER = '''
import socket, sys, threading
from pathlib import Path
import uvicorn
from backend.main import app
socket_listener = socket.socket()
socket_listener.bind(('127.0.0.1', 0))
socket_listener.listen(128)
server = uvicorn.Server(uvicorn.Config(app, log_level='warning', access_log=False))
thread = threading.Thread(target=server.run, kwargs={'sockets': [socket_listener]})
thread.start()
Path(sys.argv[1]).write_text(str(socket_listener.getsockname()[1]))
sys.stdin.readline()
server.should_exit = True
thread.join(15)
socket_listener.close()
assert not thread.is_alive(), 'Server failed to stop'
from backend.core.database import engine
engine.dispose()
print('ORDERLY_SHUTDOWN')
'''


class Task86DeploymentRehearsal(unittest.TestCase):
    _drop = fixture.Task60TrackedMigrationTests._drop
    _rows = fixture.Task60TrackedMigrationTests._rows

    def setUp(self):
        fixture.Task60TrackedMigrationTests.setUp(self)
        # Keep the original URL object: str(url) intentionally hides its password.
        url = self.engine.url.set(host='127.0.0.1')
        self.environment = os.environ.copy()
        self.environment.update(AXYREL_ENV='production',
            DATABASE_URL=url.render_as_string(hide_password=False),
            SECRET_KEY='synthetic-task86-key-not-a-production-secret',
            PYTHONPATH=str(fixture.ROOT), ACCESS_TOKEN_EXPIRE_MINUTES='60',
            AXYREL_API_TIMEOUT_SECONDS='20', AXYREL_UI_API_ENABLED='true',
            AXYREL_API_TOKEN='', AXYREL_COMPANY_ID='')
        self.http = requests.Session()
        self.http.trust_env = False
        self.addCleanup(self.http.close)

    def _command(self, arguments, environment=None):
        result = subprocess.run([sys.executable, '-B', *arguments], cwd=self.directory,
            env=environment or self.environment, capture_output=True, text=True, timeout=45)
        for sensitive in [self.environment['SECRET_KEY'], self.environment['DATABASE_URL']]:
            self.assertNotIn(sensitive, result.stdout + result.stderr)
        return result

    def _migrate(self):
        result = self._command(['-m', 'backend.scripts.init_database'])
        self.assertEqual(result.returncode, 0, 'Synthetic tracked migration command failed')
        return result.stdout

    def _start(self, sequence):
        port_file = self.directory / ('port_' + str(sequence))
        output = open(self.directory / ('server_' + str(sequence) + '.log'), 'w+')
        self.addCleanup(output.close)
        process = subprocess.Popen([sys.executable, '-B', '-c', SERVER, str(port_file)],
            cwd=self.directory, env=self.environment, stdin=subprocess.PIPE,
            stdout=output, stderr=output, text=True)
        def stop():
            if process.poll() is None:
                process.stdin.write('\n')
                process.stdin.flush()
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=10)
            process.stdin.close()
        self.addCleanup(stop)
        deadline = time.monotonic() + 20
        base = None
        while time.monotonic() < deadline and process.poll() is None:
            if port_file.exists():
                base = 'http://127.0.0.1:' + port_file.read_text()
                try:
                    response = self.http.get(base + '/health', timeout=1)
                    if response.status_code == 200:
                        self.assertEqual(response.json(), {'status': 'ok'})
                        return base, process, output, stop
                except requests.ConnectionError:
                    pass
            time.sleep(0.1)
        self.fail('Local synthetic server did not become healthy within 20 seconds')

    def test_reproducible_migrations_startup_database_requests_ui_and_shutdown(self):
        self.assertEqual(self._migrate().count('  OK:'), 13)
        before = self._rows()
        self.assertEqual(self._migrate().count('SKIP:'), 13)
        self.assertEqual(self._rows(), before)
        company, identity = uuid4(), uuid4()
        with Session(self.engine) as db, db.begin():
            organization = Company(id=company, name='Synthetic Deployment', status='active')
            user = User(id=identity, company=organization, email='rehearsal@example.invalid',
                full_name='Synthetic', password_hash=hash_password('synthetic-rehearsal-password'), role='admin')
            db.add_all([organization, user])
        for sequence in (1, 2):
            base, process, output, stop = self._start(sequence)
            response = self.http.post(base + '/api/v1/auth/login',
                data={'username': 'rehearsal@example.invalid', 'password': 'synthetic-rehearsal-password'}, timeout=5)
            self.assertEqual(response.status_code, 200)
            headers = {'Authorization': 'Bearer ' + response.json()['access_token']}
            self.assertEqual(self.http.get(base + '/api/v1/auth/me', headers=headers, timeout=5).json()['id'], str(identity))
            created = self.http.post(base + '/api/v1/customers', headers=headers,
                json={'name': 'Synthetic Deployment ' + str(sequence)}, timeout=5)
            self.assertEqual(created.status_code, 201)
            self.assertEqual(len(self.http.get(base + '/api/v1/customers', headers=headers, timeout=5).json()), sequence)
            # Render the real UI entry point in production mode, without browser/external services.
            ui_environment = {**self.environment, 'AXYREL_API_BASE_URL': base}
            ui = self._command(['-c', '''
from streamlit.testing.v1 import AppTest
from pathlib import Path
import os
app = AppTest.from_file(str(Path(os.environ['PYTHONPATH']) / 'app.py')).run(timeout=15)
assert not app.exception, 'UI startup error'
assert any(title.value == '🚰 Axyrel' for title in app.title), 'Login page missing'
print('UI_STARTUP_OK')
'''], ui_environment)
            self.assertEqual(ui.returncode, 0, 'Synthetic Streamlit startup failed')
            self.assertIn('UI_STARTUP_OK', ui.stdout)
            stop()
            self.assertEqual(process.returncode, 0)
            output.seek(0)
            logs = output.read()
            self.assertIn('ORDERLY_SHUTDOWN', logs)
            self.assertNotIn(self.environment['SECRET_KEY'], logs)
            self.assertNotIn(self.environment['DATABASE_URL'], logs)
        with self.engine.connect() as db:
            self.assertEqual(db.execute(text('SELECT count(*) FROM customers WHERE company_id=:company'), {'company': company}).scalar_one(), 2)
        self.assertEqual(self._rows(), before)

    def test_invalid_production_configuration_prevents_deployment_startup(self):
        for updates in [{'SECRET_KEY': ''}, {'SECRET_KEY': 'change-me-in-production'}, {'DATABASE_URL': 'invalid-url'}]:
            result = self._command(['-c', 'from backend.main import app'], {**self.environment, **updates})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Invalid application configuration.', result.stderr)
        with self.engine.connect() as db:
            self.assertEqual(db.execute(text("SELECT count(*) FROM pg_tables WHERE schemaname='public'")).scalar_one(), 0)


if __name__ == '__main__':
    unittest.main()
