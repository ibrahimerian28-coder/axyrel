"""Run accepted service contracts using only their disposable test databases."""
from pathlib import Path
import os
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["AXYREL_ENV"] = "test"
from backend.core.config import get_settings
from sqlalchemy.engine import make_url

url = make_url(get_settings().database_url)
if url.get_backend_name() != "postgresql" or url.host not in {"localhost", "127.0.0.1", "::1"}:
    raise RuntimeError("Phase 3 contract validation requires a local PostgreSQL server.")
# The PostgreSQL suites connect only to postgres for CREATE DATABASE and then
# their generated axyrel_task52_test_/axyrel_task53_test_ targets. Other suites
# own disposable SQLite databases. No configured application DB is accessed.
modules = ["test_task51_request_work_order_integration", "test_task52_work_order_scheduling",
           "test_task53_schedule_service_visit", "test_task54_visit_history_integration",
           "test_task55_work_order_inventory"]
import subprocess
failed=[]
for name in modules:
    print("ISOLATED MODULE:",name,flush=True)
    result=subprocess.run([sys.executable,"-B",str(Path(__file__).resolve().parent/"isolated_backend_suite.py"),name],cwd=Path(__file__).resolve().parents[1])
    if result.returncode: failed.append(name)
raise SystemExit(1 if failed else 0)
