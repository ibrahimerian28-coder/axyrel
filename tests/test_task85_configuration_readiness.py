"""Offline startup checks: synthetic values, no .env or database/network access."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_SECRET = 'synthetic-task85-secret-not-a-production-credential'
SYNTHETIC_URL = 'postgresql+psycopg://synthetic:synthetic@database.invalid/axyrel_synthetic'


class Task85ConfigurationReadiness(unittest.TestCase):
    def _run(self, environment='production', secret=SYNTHETIC_SECRET,
             database=SYNTHETIC_URL, extra=None, script=None):
        values = os.environ.copy()
        values.update(AXYREL_ENV=environment, SECRET_KEY=secret, DATABASE_URL=database,
                      PYTHONPATH=str(ROOT), ACCESS_TOKEN_EXPIRE_MINUTES='60',
                      AXYREL_API_TIMEOUT_SECONDS='20')
        if extra:
            values.update(extra)
        for key in ['SECRET_KEY', 'DATABASE_URL']:
            if values[key] is None:
                del values[key]
        # A fresh directory prevents reading any real workspace .env.
        with tempfile.TemporaryDirectory(prefix='axyrel_task85_') as directory:
            result = subprocess.run([sys.executable, '-B', '-c', script or '''
from unittest.mock import patch
with patch('psycopg.connect', side_effect=AssertionError('Database connection forbidden')), patch('sqlalchemy.engine.Engine.connect', side_effect=AssertionError('Database connection forbidden')):
    from fastapi.testclient import TestClient
    from backend.main import app
    with TestClient(app) as client:
        assert client.get('/health').json() == {'status': 'ok'}
        assert client.get('/api/v1/customers').status_code == 401
print('STARTUP_OK')
'''], cwd=directory, env=values, capture_output=True, text=True, timeout=40)
        self.assertNotIn(SYNTHETIC_SECRET, result.stdout + result.stderr)
        self.assertNotIn(SYNTHETIC_URL, result.stdout + result.stderr)
        return result

    def _refused(self, **values):
        result = self._run(**values)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('STARTUP_OK', result.stdout)
        self.assertIn('Invalid application configuration.', result.stderr)

    def test_synthetic_production_startup_and_existing_health_auth_contracts(self):
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('STARTUP_OK', result.stdout)

    def test_missing_blank_and_development_secret_fail_before_engine_creation(self):
        for secret in ['', '   ', 'change-me-in-production', ' change-me-in-production ']:
            with self.subTest(kind='blank-or-default'):
                self._refused(secret=secret)

    def test_invalid_missing_and_prohibited_database_fail_closed(self):
        for database in ['', 'not-a-url', 'sqlite:///synthetic.db',
                         'postgresql+psycopg://synthetic:synthetic@localhost/synthetic',
                         'postgresql+psycopg://synthetic:synthetic@LOCALHOST/synthetic',
                         'postgresql+psycopg://database.invalid',
                         'postgresql+psycopg://database.invalid:bad/synthetic']:
            with self.subTest(kind='invalid-or-prohibited'):
                self._refused(database=database)

    def test_invalid_typed_setting_does_not_echo_sensitive_input(self):
        self._refused(extra={'ACCESS_TOKEN_EXPIRE_MINUTES': SYNTHETIC_SECRET})

    def test_absent_required_production_values_cannot_use_development_defaults(self):
        self._refused(secret=None)
        self._refused(database=None)

    def test_production_mode_case_and_whitespace_do_not_bypass_validation(self):
        self._refused(environment=' Production ', secret='change-me-in-production')

    def test_development_and_test_do_not_apply_production_only_rules(self):
        for environment in ['development', 'test']:
            with self.subTest(environment=environment):
                result = self._run(environment=environment, secret='change-me-in-production',
                                   database='sqlite://')
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_asgi_lifespan_calls_validator_and_refuses_to_serve_on_failure(self):
        result = self._run(script='''
from unittest.mock import patch
with patch('psycopg.connect', side_effect=AssertionError('Database connection forbidden')), patch('sqlalchemy.engine.Engine.connect', side_effect=AssertionError('Database connection forbidden')):
    from backend.main import app
    from backend.core.config import Settings
    from fastapi.testclient import TestClient
    with patch.object(Settings, 'validate_production_security', side_effect=ValueError('Startup refused')) as validator:
        try:
            with TestClient(app):
                raise AssertionError('Failed validator allowed startup')
        except ValueError as error:
            assert str(error) == 'Startup refused'
        validator.assert_called_once()
print('LIFESPAN_REFUSED')
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('LIFESPAN_REFUSED', result.stdout)

    def test_configuration_refusal_precedes_database_engine_construction(self):
        result = self._run(secret='change-me-in-production', script='''
from unittest.mock import patch
with patch('sqlalchemy.create_engine', side_effect=AssertionError('Engine created too early')):
    from backend.main import app
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Invalid application configuration.', result.stderr)
        self.assertNotIn('Engine created too early', result.stderr)


if __name__ == '__main__':
    unittest.main()
