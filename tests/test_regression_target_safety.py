"""No database access: regression connection target and admin guards."""
import sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from sqlalchemy.engine import make_url
sys.path.insert(0,str(Path(__file__).resolve().parent))
import isolated_backend_suite as guard

class RegressionSafety(unittest.TestCase):
 def test_rejects_application_owner_review_remote_and_uncreated_databases(self):
  for url in ["postgresql://unused@localhost/axyrel","postgresql://unused@localhost/axyrel_owner_review_"+"1"*32,"postgresql://unused@example.invalid/postgres","postgresql://unused@localhost/axyrel_task60_test_"+"1"*32,"sqlite:///D:/Axyrel_BACKUP_BEFORE_GEMINI/retained.db"]:
   with self.assertRaises(RuntimeError):guard.check_connection(make_url(url))
 def test_only_created_local_test_target_and_temporary_sqlite_are_allowed(self):
  name="axyrel_task60_test_"+"2"*32;guard.created.add(name)
  try:
   guard.check_connection(make_url("postgresql://unused@localhost/"+name));guard.check_connection(make_url("postgresql://unused@localhost/postgres"));guard.check_connection(make_url("sqlite:///"+str(Path(tempfile.gettempdir())/"synthetic.db")))
  finally:guard.created.remove(name)
 def test_admin_refuses_drop_of_unknown_database(self):
  connection=SimpleNamespace(engine=SimpleNamespace(url=make_url("postgresql://unused@localhost/postgres")))
  for statement in ['DROP DATABASE "axyrel"','CREATE DATABASE "unknown"','DELETE FROM users','DROP DATABASE "axyrel_task60_test_'+'3'*32+'"']:
   with self.assertRaises(RuntimeError):guard.guard_admin(connection,None,statement,None,None,False)
 def test_guard_rejects_real_connection_before_driver_access(self):
  engine=guard.guarded_engine("postgresql+psycopg://unused:unused@localhost/axyrel")
  try:
   with self.assertRaisesRegex(RuntimeError,"Regression refused"):
    engine.connect()
  finally:engine.dispose()
if __name__=="__main__":unittest.main(verbosity=2)
