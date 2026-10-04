"""Focused accepted MVP suites; all database fixtures are disposable/local."""
import os
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
os.environ["AXYREL_ENV"]="test"
from backend.core.config import get_settings
from sqlalchemy.engine import make_url
url=make_url(get_settings().database_url)
if url.get_backend_name()!="postgresql" or url.host not in {"localhost","127.0.0.1","::1"}: raise RuntimeError("Local PostgreSQL only.")
modules=["test_task46_auth","test_task55_work_order_inventory","test_task56_order_billing_integration","test_task57_expense_profitability","test_task60_tracked_migrations","test_task61_indexes_constraints","test_task73_postgresql_repositories","test_task76_postgresql_financial","test_task78_tenant_isolation","test_phase2_profile_images"]
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in modules)
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
