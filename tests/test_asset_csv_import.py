"""Real PostgreSQL, generated database only: CSV import safety and concurrency."""
import importlib.util
import sys
from pathlib import Path
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location("phase3_fixture", Path(__file__).resolve().parents[1] / "frontend/tests/phase3-api.py")
fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
from fastapi.testclient import TestClient

class AssetImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = fixture.synthetic_application(); app = cls.fixture.__enter__(); cls.client = TestClient(app)
        cls.headers = {}
        for role in ["admin", "foreign", "technician"]:
            response = cls.client.post("/api/v1/auth/login", data={"username":role+"@example.test", "password":"synthetic-password"})
            cls.headers[role] = {"Authorization":"Bearer "+response.json()["access_token"]}
    @classmethod
    def tearDownClass(cls):
        cls.client.close(); cls.fixture.__exit__(None, None, None)
    def preview(self, source, role="admin"):
        return self.client.post("/api/v1/assets/import/validate", headers=self.headers[role], json={"csv":source})
    def commit(self, source, preview=None, key=None, role="admin"):
        token = (preview or self.preview(source).json()).get("token", "")
        return self.client.post("/api/v1/assets/import/commit", headers=self.headers[role], json={"csv":source,"token":token,"idempotency_key":key or str(uuid4())})
    def source(self, serial=None):
        return "customer_reference,asset_type,serial_number\n1001,Device," + (serial or uuid4().hex) + "\n"
    def test_success_and_durable_retry(self):
        source=self.source(); preview=self.preview(source).json(); self.assertTrue(preview["valid"])
        key=str(uuid4()); first=self.commit(source,preview,key).json(); second=self.commit(source,preview,key).json()
        self.assertEqual(first["created"],1); self.assertEqual(first["display_ids"],second["display_ids"]); self.assertTrue(second["replayed"])
        self.assertEqual(self.commit(self.source(),preview,key).status_code,400)
    def test_blank_serials_repeat_and_stored_value_preserved(self):
        source="customer_reference,asset_type,serial_number\n1001,Device,\n1001,Device,   \n1001,Device,  "+uuid4().hex+"  \n"
        self.assertEqual(self.commit(source).json()["created"],3)
        rows=self.client.get("/api/v1/assets",headers=self.headers["admin"]).json()
        self.assertTrue(any(str(r["serial_number"]).startswith("  ") and str(r["serial_number"]).endswith("  ") for r in rows))
    def test_duplicate_file_and_existing_including_deleted(self):
        serial=uuid4().hex; source=self.source(serial)+"1001,Device,  "+serial+"  \n"
        self.assertIn("duplicate_file",[e["code"] for e in self.preview(source).json()["errors"]])
        self.commit(self.source(serial)); self.assertIn("duplicate_tenant",[e["code"] for e in self.preview(self.source(serial)).json()["errors"]])
    def test_tenant_customer_and_token_isolation(self):
        source=self.source(); preview=self.preview(source).json()
        self.assertEqual(self.preview(source,"foreign").json()["preview"][0]["customer"],"Other customer")
        self.assertEqual(self.commit(source,preview,role="foreign").status_code,400)
        self.assertFalse(self.preview(source.replace("1001","99999")).json()["valid"])
    def test_same_serial_different_tenants(self):
        from backend.core.database import SessionLocal
        from backend.models.customer import Customer
        from backend.models.user import User
        from sqlalchemy import select
        with SessionLocal() as db:
            company=db.scalar(select(User.company_id).where(User.email=="foreign@example.test"))
            db.add(Customer(company_id=company,display_id=1001,name="Other customer",status="Active")); db.commit()
        serial=uuid4().hex
        self.assertEqual(self.commit(self.source(serial)).json()["created"],1)
        self.assertEqual(self.commit(self.source(serial),role="foreign",preview=self.preview(self.source(serial),"foreign").json()).json()["created"],1)
    def test_commit_revalidates_and_no_partial_writes(self):
        serial=uuid4().hex; source=self.source(serial)+"1001,Device,"+uuid4().hex+"\n"
        preview=self.preview(source).json(); self.commit(self.source(serial))
        before=len(self.client.get("/api/v1/assets",headers=self.headers["admin"]).json())
        self.assertFalse(self.commit(source,preview).json()["valid"])
        self.assertEqual(before,len(self.client.get("/api/v1/assets",headers=self.headers["admin"]).json()))
    def test_atomic_rollback_on_failure_and_retry(self):
        source=self.source()+"1001,Device,"+uuid4().hex+"\n"; preview=self.preview(source).json(); key=str(uuid4())
        from backend.services.asset import AssetService
        original=AssetService.create_asset; calls=[]
        def fail(service,*args):
            calls.append(1)
            if len(calls)==2: raise RuntimeError("synthetic failure")
            return original(service,*args)
        before=len(self.client.get("/api/v1/assets",headers=self.headers["admin"]).json())
        with patch.object(AssetService,"create_asset",fail):
            with self.assertRaises(RuntimeError): self.commit(source,preview,key)
        self.assertEqual(before,len(self.client.get("/api/v1/assets",headers=self.headers["admin"]).json()))
        self.assertEqual(self.commit(source,preview,key).json()["created"],2)
    def test_expired_preview_completed_retry_and_soft_deleted_serial(self):
        from backend.services.asset_import import preview_token, checksum
        from backend.core.config import get_settings
        import jwt
        source=self.source(); preview=self.preview(source).json(); claims=jwt.decode(preview["token"],get_settings().secret_key,algorithms=["HS256"]); claims["exp"]=1
        expired={"token":jwt.encode(claims,get_settings().secret_key,algorithm="HS256")}
        self.assertEqual(self.commit(source,expired).status_code,400)
        key=str(uuid4());self.commit(source,preview,key)
        self.assertTrue(self.commit(source,expired,key).json()["replayed"])
        rows=self.client.get("/api/v1/assets",headers=self.headers["admin"]).json()
        asset=next(r for r in rows if r["serial_number"]==source.splitlines()[1].split(",")[2])
        self.assertEqual(self.client.delete("/api/v1/assets/"+asset["id"],headers=self.headers["admin"]).status_code,204)
        self.assertFalse(self.preview(source).json()["valid"])
    def test_two_concurrent_imports_same_serial_different_keys(self):
        from backend.core.database import SessionLocal
        from backend.models.user import User
        from backend.services.asset_import import commit_import,preview_token
        from sqlalchemy import select
        with SessionLocal() as db:
            user=db.scalar(select(User).where(User.email=="admin@example.test"));company=user.company_id;actor=user.id
        source=self.source();token=preview_token(source,company,actor)
        def write(_):
            with SessionLocal() as db:
                result=commit_import(db,company,actor,source,token,str(uuid4()));db.commit();return result
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(write,range(2)))
        self.assertEqual(sum(r["valid"] for r in results),1)

    def test_malformed_oversized_fields_utf8_headers_dates(self):
        for source in ["",'customer_reference,asset_type\n1001,"bad',"company_id,asset_type\n1,Device", "customer_reference,asset_type,installation_date\n1001,Device,invalid", "customer_reference,asset_type\n1001,"+"x"*151]:
            self.assertFalse(self.preview(source).json()["valid"])
        self.assertEqual(self.preview("x"*1048577).status_code,413)
        self.assertEqual(self.client.post("/api/v1/assets/import/validate",headers=self.headers["admin"],content=b"\xff").status_code,400)
        source="customer_reference,asset_type\n"+"1001,Device\n"*1001
        self.assertFalse(self.preview(source).json()["valid"])
    def test_permissions_and_unauthenticated(self):
        self.assertEqual(self.client.post("/api/v1/assets/import/validate",json={"csv":self.source()}).status_code,401)
        self.assertEqual(self.preview(self.source(),"technician").status_code,403)
    def test_concurrent_import_crud_and_same_key(self):
        from backend.core.database import SessionLocal
        from backend.models.user import User
        from backend.models.customer import Customer
        from backend.services.asset_import import commit_import,preview_token
        from backend.services.asset import AssetService
        from sqlalchemy import select
        with SessionLocal() as db:
            user=db.scalar(select(User).where(User.email=="admin@example.test")); company=user.company_id; actor=user.id
            customer=db.scalar(select(Customer.id).where(Customer.company_id==company,Customer.display_id==1001))
        source=self.source(); token=preview_token(source,company,actor); key=str(uuid4())
        def write(index):
            with SessionLocal() as db:
                if index<2: result=commit_import(db,company,actor,source,token,key)
                else:
                    asset=AssetService().create_asset(db,company,{"customer_id":customer,"asset_type":"Concurrent"}); result={"display_ids":[asset.display_id]}
                db.commit(); return result
        with ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(write,range(4)))
        self.assertEqual(results[0]["display_ids"],results[1]["display_ids"])
        self.assertEqual(len({r["display_ids"][0] for r in results}),3)

if __name__=="__main__": unittest.main(verbosity=2)
