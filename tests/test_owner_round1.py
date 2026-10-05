"""Owner remediation: real PostgreSQL, isolated synthetic records only."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import unittest
from uuid import uuid4
from sqlalchemy import text
import test_asset_csv_import as import_tests
import test_task60_tracked_migrations as migration_tests
ROOT=migration_tests.ROOT

class OwnerRoundOneAPI(unittest.TestCase):
    setUpClass = classmethod(import_tests.AssetImportTests.setUpClass.__func__)
    tearDownClass = classmethod(import_tests.AssetImportTests.tearDownClass.__func__)
    def customer(self,**extra):
        response=self.client.post("/api/v1/customers",headers=self.headers["admin"],json=dict(name="Synthetic Round1 "+uuid4().hex,**extra)); self.assertEqual(response.status_code,201,response.text);return response.json()
    def asset(self,**extra):
        response=self.client.post("/api/v1/assets",headers=self.headers["admin"],json=dict(customer_id=self.customer()["id"],asset_type="Synthetic Device",**extra));self.assertEqual(response.status_code,201,response.text);return response.json()
    def test_dynamic_phones_default_egypt_and_international_normalization(self):
        phones=[dict(number="01000000002",label="Primary")]+[dict(country="GB",number="020 7946 0018",label="Work "+str(i)) for i in range(6)]
        customer=self.customer(phones=phones);self.assertEqual(len(customer["phones"]),7);self.assertEqual(customer["phones"][0]["country"],"EG");self.assertEqual(customer["phones"][0]["normalized"],"+201000000002");self.assertEqual(customer["phones"][1]["normalized"],"+442079460018")
        headers=self.headers["admin"];path="/api/v1/customers/"+customer["id"]
        self.assertEqual(self.client.get(path,headers=headers).json()["phones"],customer["phones"])
        self.assertEqual(self.client.get(path,headers=self.headers["foreign"]).status_code,404)
        self.assertEqual(self.client.patch(path,headers=self.headers["foreign"],json={"name":"Forbidden","phones":[]}).status_code,404)
        self.assertEqual(self.client.patch(path,headers=self.headers["technician"],json={"name":"Forbidden","phones":[]}).status_code,403)
        found=self.client.get("/api/v1/customers",headers=headers,params={"search":"442079460018"}).json()
        self.assertIn(customer["id"],[r["id"] for r in found])
        self.assertEqual(self.client.patch(path,headers=headers,json={"name":customer["name"],"phones":[]}).json()["phones"],[])
        bad=self.client.post("/api/v1/customers",headers=headers,json={"name":"Invalid synthetic","phones":[{"number":"bad","country":"EG"}]});self.assertEqual(bad.status_code,400)
        forged=self.client.post("/api/v1/customers",headers=headers,json={"name":"Invalid synthetic","phones":[{"number":"arbitrary","country":None,"normalized":"+201000000002"}]});self.assertEqual(forged.status_code,400)
    def test_legacy_phone_and_customer_location_preservation(self):
        values=dict(phone="01000000001",phone_1="+442079460018",phone_2="old extension 456",phone_3="01111111111",phone_4="legacy four",address="Preserve old address",area="Preserve old area",location_url="https://example.test/old")
        customer=self.customer(**values);self.assertEqual([p["number"] for p in customer["phones"]],[values[k] for k in ["phone","phone_1","phone_2","phone_3","phone_4"]]);self.assertIsNone(customer["phones"][0]["normalized"])
        updated=self.client.patch("/api/v1/customers/"+customer["id"],headers=self.headers["admin"],json={"name":customer["name"],"phones":customer["phones"]}).json()
        for key,value in values.items(): self.assertEqual(updated[key],value)
        phones=updated["phones"];phones[0]["country"]=""
        path="/api/v1/customers/"+customer["id"]
        retained=self.client.patch(path,headers=self.headers["admin"],json={"name":customer["name"],"phones":phones})
        self.assertEqual(retained.status_code,200);self.assertIsNone(retained.json()["phones"][0]["country"])
        self.assertEqual(self.client.patch(path,headers=self.headers["admin"],json={"name":customer["name"],"phones":retained.json()["phones"]}).status_code,200)
        phones[0]["country"]="EG"
        normalized=self.client.patch("/api/v1/customers/"+customer["id"],headers=self.headers["admin"],json={"name":customer["name"],"phones":phones}).json();self.assertEqual(normalized["phones"][0]["normalized"],"+201000000001");self.assertEqual(normalized["phone"],values["phone"])
    def test_asset_location_and_service_fields_and_permissions(self):
        asset=self.asset(country="EG",state="EG-C",area="Cairo",address="Synthetic service address",location_url="https://example.test/map",installation_date="2024-02-29",maintenance_cycle=6,warranty_years=1)
        self.assertEqual(asset["warranty_end"],"2025-02-28");path="/api/v1/assets/"+asset["id"]
        self.assertEqual(self.client.get(path,headers=self.headers["admin"]).json()["address"],"Synthetic service address")
        self.assertEqual(self.client.get(path,headers=self.headers["foreign"]).status_code,404)
        self.assertEqual(self.client.patch(path,headers=self.headers["technician"],json={"area":"forbidden"}).status_code,403)
        self.assertEqual(self.client.patch(path,headers=self.headers["foreign"],json={"area":"forbidden"}).status_code,404)
        self.assertEqual(self.client.patch(path,headers=self.headers["admin"],json={"country":"US","state":"EG-C"}).status_code,400)
        self.assertEqual(self.client.patch(path,headers=self.headers["admin"],json={"location_url":"javascript:alert(1)"}).status_code,400)
        self.assertEqual(self.client.patch(path,headers=self.headers["admin"],json={"maintenance_cycle":0}).status_code,422)
        self.assertEqual(self.client.patch(path,headers=self.headers["admin"],json={"country":"US","state":"US-CA","area":"Actual owner-entered locality"}).status_code,200)
    def test_warranty_missing_values_clear_and_legacy_compatibility(self):
        self.assertIsNone(self.asset(warranty_years=2)["warranty_end"])
        self.assertIsNone(self.asset(installation_date="2025-05-01")["warranty_end"])
        self.assertEqual(self.asset(installation_date="2025-05-01",warranty_years=0)["warranty_end"],"2025-05-01")
        asset=self.asset(installation_date="2024-02-29",warranty_years=4,warranty_end="2099-01-01");self.assertEqual(asset["warranty_end"],"2028-02-29")
        path="/api/v1/assets/"+asset["id"]
        response=self.client.patch(path,headers=self.headers["admin"],json={"warranty_end":"2099-01-01"});self.assertEqual(response.json()["warranty_end"],"2028-02-29")
        self.assertEqual(self.client.patch(path,headers=self.headers["admin"],json={"installation_date":"9999-01-01","warranty_years":1}).status_code,400)
        response=self.client.patch(path,headers=self.headers["admin"],json={"installation_date":None});self.assertIsNone(response.json()["warranty_end"])
        self.client.patch(path,headers=self.headers["admin"],json={"installation_date":"2025-06-20"})
        response=self.client.patch(path,headers=self.headers["admin"],json={"warranty_years":None});self.assertIsNone(response.json()["warranty_end"])
        legacy=self.asset(warranty_start="2020-01-01",warranty_end="2030-01-01")
        response=self.client.patch("/api/v1/assets/"+legacy["id"],headers=self.headers["admin"],json={"notes":"Legacy date retained"});self.assertEqual(response.json()["warranty_end"],"2030-01-01")
    def test_import_final_fields_preview_and_commit(self):
        source="customer_reference,asset_type,country,state,area,address,location_url,installation_date,maintenance_cycle,warranty_years,serial_number\n1001,Synthetic Device,EG,EG-C,Cairo,Test address,https://example.test/map,2024-02-29,6,1,"+uuid4().hex+"\n"
        preview=self.client.post("/api/v1/assets/import/validate",headers=self.headers["admin"],json={"csv":source}).json();self.assertTrue(preview["valid"],preview)
        commit=self.client.post("/api/v1/assets/import/commit",headers=self.headers["admin"],json={"csv":source,"token":preview["token"],"idempotency_key":str(uuid4())}).json();self.assertTrue(commit["valid"],commit)
        rows=self.client.get("/api/v1/assets",headers=self.headers["admin"]).json();asset=next(a for a in rows if a["display_id"]==commit["display_ids"][0]);self.assertEqual(asset["warranty_end"],"2025-02-28");self.assertEqual(asset["maintenance_cycle"],6);self.assertEqual(asset["state"],"EG-C")
        for bad in [source.replace(",6,1,",",abc,1,"),source.replace("EG-C","US-CA"),source.replace("https://example.test/map","javascript:bad")]:
            response=self.client.post("/api/v1/assets/import/validate",headers=self.headers["admin"],json={"csv":bad}).json();self.assertFalse(response["valid"]);self.assertTrue(response["errors"])

class OwnerRoundOneMigration(unittest.TestCase):
    setUp=migration_tests.Task60TrackedMigrationTests.setUp
    _drop=migration_tests.Task60TrackedMigrationTests._drop
    _apply=migration_tests.Task60TrackedMigrationTests._apply
    _rows=migration_tests.Task60TrackedMigrationTests._rows
    def test_additive_migration_preserves_old_rows_and_ledger(self):
        for path in (ROOT/"migrations").glob("*.sql"):
            if not path.name.startswith("015_"): (self.directory/path.name).write_bytes(path.read_bytes())
        self._apply();old=self._rows();company,customer,asset=uuid4(),uuid4(),uuid4()
        with self.engine.begin() as db:
            db.execute(text("INSERT INTO customers (id,company_id,name,phone,phone_1,phone_2,phone_3,phone_4,address,area,location_url,status) VALUES (:id,:company,'Legacy','one','two','three','four','five','old address','old area','https://example.test/old','Active')"),dict(id=customer,company=company))
            db.execute(text("INSERT INTO assets (id,company_id,customer_id,asset_type,serial_number,warranty_end,status) VALUES (:id,:company,:customer,'Legacy device','old serial','2030-01-01','Active')"),dict(id=asset,company=company,customer=customer))
            before_customer=db.execute(text("SELECT * FROM customers WHERE id=:id"),dict(id=customer)).mappings().one();before_asset=db.execute(text("SELECT * FROM assets WHERE id=:id"),dict(id=asset)).mappings().one()
        self._apply(ROOT/"migrations");self.assertEqual(self._rows()[:-1],old)
        with self.engine.connect() as db:
            after_customer=db.execute(text("SELECT * FROM customers WHERE id=:id"),dict(id=customer)).mappings().one();after_asset=db.execute(text("SELECT * FROM assets WHERE id=:id"),dict(id=asset)).mappings().one()
            for key,value in before_customer.items():self.assertEqual(after_customer[key],value)
            for key,value in before_asset.items():self.assertEqual(after_asset[key],value)
            self.assertIsNone(after_customer["phones"]);self.assertIsNone(after_asset["country"])
        self.assertEqual(self._apply(ROOT/"migrations").count("SKIP:"),14)

if __name__=="__main__":unittest.main(verbosity=2)
