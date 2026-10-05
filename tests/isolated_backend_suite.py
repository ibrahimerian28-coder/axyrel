"""Process-isolated suite with fail-closed connection guards.
Never allow configured application or Owner Review databases in regressions.
"""
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from sqlalchemy import event
from sqlalchemy.engine import Engine, make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tests"))
GENERATED = re.compile(r"axyrel_(?:task(?:52|53|60)|phase3)_test_[0-9a-f]{32}")
created = set()

def check_connection(url):
    if url.get_backend_name()=="sqlite":
        if url.database in {None,"",":memory:"}:return
        if Path(url.database).resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()):return
        raise RuntimeError("Regression SQLite database must be disposable temporary storage.")
    if url.get_backend_name()=="postgresql" and url.host in {"localhost","127.0.0.1","::1"}:
        if url.database=="postgres" or url.database in created:return
    raise RuntimeError("Regression refused a database not created by this isolated process.")

@event.listens_for(Engine,"do_connect")
def guard_connection(dialect, record, args, kwargs):
    check_connection(dialect._regression_url)

@event.listens_for(Engine,"before_cursor_execute")
def guard_admin(connection,cursor,statement,parameters,context,executemany):
    if connection.engine.url.get_backend_name()!="postgresql" or connection.engine.url.database!="postgres":return
    create=re.fullmatch(r'CREATE DATABASE "(axyrel_[a-z0-9_]+)"',statement.strip(),re.I)
    drop=re.fullmatch(r'DROP DATABASE(?: IF EXISTS)? "(axyrel_[a-z0-9_]+)"(?: WITH \(FORCE\))?',statement.strip(),re.I)
    if create and GENERATED.fullmatch(create[1]):return
    if drop and drop[1] in created:return
    if statement.lstrip().upper().startswith("SELECT "):return
    raise RuntimeError("Regression refused unexpected PostgreSQL administration SQL.")

@event.listens_for(Engine,"after_cursor_execute")
def record_created(connection,cursor,statement,parameters,context,executemany):
    if connection.engine.url.database!="postgres":return
    match=re.fullmatch(r'CREATE DATABASE "(axyrel_[a-z0-9_]+)"',statement.strip(),re.I)
    if match:created.add(match[1])

# SQLAlchemy exposes the actual engine to engine_connect, before use; do_connect
# happens earlier, so wrap construction to install a per-dialect URL at creation.
import sqlalchemy
_original_create_engine=sqlalchemy.create_engine
def guarded_engine(url,*args,**kwargs):
    engine=_original_create_engine(url,*args,**kwargs)
    engine.dialect._regression_url=make_url(url)
    return engine
sqlalchemy.create_engine=guarded_engine

if __name__=="__main__":
    os.chdir(ROOT)
    os.environ["AXYREL_ENV"]="test"
    suite=unittest.defaultTestLoader.loadTestsFromName(sys.argv[1])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
