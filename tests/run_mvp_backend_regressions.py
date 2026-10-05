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
# Each module owns process-local configuration and fixtures. Importing them all
# after caching PostgreSQL settings can redirect SQLite fixtures to the app DB.
import subprocess
failed=[]
for name in modules:
    print("ISOLATED MODULE:",name,flush=True)
    result=subprocess.run([sys.executable,"-B",str(Path(__file__).resolve().parent/"isolated_backend_suite.py"),name],cwd=Path(__file__).resolve().parents[1])
    if result.returncode: failed.append(name)
if failed: print("Failed isolated modules:",", ".join(failed))
raise SystemExit(1 if failed else 0)
