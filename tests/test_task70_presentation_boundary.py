"""Presentation sources use the accepted HTTP boundary rather than database access."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
import requests
from utils import api_client

ROOT = Path(__file__).resolve().parents[1]


class Task70PresentationBoundaryTests(unittest.TestCase):
    def test_presentation_imports_have_no_database_or_backend_business_dependencies(self):
        paths = [ROOT / 'app.py']
        for directory in ('modules', 'components', 'utils'):
            paths.extend((ROOT / directory).rglob('*.py'))
        drivers = {'sqlalchemy', 'sqlite3', 'psycopg', 'psycopg2', 'asyncpg', 'pg8000'}
        for path in paths:
            tree = ast.parse(path.read_text(encoding='utf-8-sig'))
            for node in ast.walk(tree):
                names = ([node.module or ''] if isinstance(node, ast.ImportFrom) else
                         [alias.name for alias in node.names] if isinstance(node, ast.Import) else [])
                for name in names:
                    self.assertNotIn(name.split('.')[0], drivers, str(path))
                    if name == 'backend' or name.startswith('backend.'):
                        self.assertEqual(name, 'backend.core.config', str(path))

    def test_http_boundary_preserves_authenticated_api_request(self):
        response = MagicMock(status_code=200, content=b'[]')
        response.json.return_value = []
        settings = SimpleNamespace(api_base_url='http://127.0.0.1:8000', api_prefix='/api/v1',
                                   api_token='', api_timeout_seconds=10)
        with patch.object(api_client, 'settings', settings), \
                patch.object(api_client, 'st', SimpleNamespace(session_state={'api_access_token': 'synthetic-token'})), \
                patch.object(api_client.requests, 'request', return_value=response) as request:
            self.assertEqual(api_client.list_records('inventory'), [])
            self.assertEqual(request.call_args.args[:2], ('GET', 'http://127.0.0.1:8000/api/v1/inventory'))
            headers = request.call_args.kwargs['headers']
            self.assertEqual(headers['Authorization'], 'Bearer synthetic-token')
            self.assertNotIn('X-Company-ID', headers)

    def test_transport_failure_remains_api_error_without_local_fallback(self):
        with patch.object(api_client, 'st', SimpleNamespace(session_state={'api_access_token': 'synthetic-token'})), \
                patch.object(api_client.requests, 'request', side_effect=requests.ConnectionError('synthetic')) as request:
            with self.assertRaises(api_client.APIClientError):
                api_client.list_records('inventory')
            request.assert_called_once()


if __name__ == '__main__':
    unittest.main()
