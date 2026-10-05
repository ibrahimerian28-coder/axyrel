"""Requests editor API contract on a disposable temporary SQLite database."""
import os
import tempfile
import unittest
from uuid import uuid4

DB_FILE = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
DB_FILE.close()
os.environ['DATABASE_URL'] = f'sqlite:///{DB_FILE.name}'
os.environ['SECRET_KEY'] = 'request-contract-test-secret-at-least-32-bytes'

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import backend.models
from backend.api.v1 import router
from backend.core.database import get_db
from backend.core.security import create_access_token, hash_password
from backend.main import app as application
from backend.models.base import Base
from backend.models.company import Company
from backend.models.customer import Customer
from backend.models.user import User
from backend.models.service_request import ServiceRequest


class RequestEditorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=create_engine(f'sqlite:///{DB_FILE.name}',connect_args={'check_same_thread':False})
        cls.Session=sessionmaker(bind=cls.engine)
        Base.metadata.create_all(cls.engine)
        cls.password=hash_password('Synthetic-password')

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose();os.unlink(DB_FILE.name)

    def setUp(self):
        self.company,self.customer,self.user,self.legacy=[uuid4() for _ in range(4)]
        with self.Session() as db:
            for table in reversed(Base.metadata.sorted_tables):db.execute(table.delete())
            db.add(Company(id=self.company,name='Disposable',status='active'));db.flush()
            db.add_all([Customer(id=self.customer,company_id=self.company,name='Synthetic customer'),User(id=self.user,company_id=self.company,email='admin@example.test',full_name='Synthetic Admin',role='admin',password_hash=self.password)])
            db.flush();db.add(ServiceRequest(id=self.legacy,company_id=self.company,customer_id=self.customer,title='Legacy request',priority='high',status='CLOSED'));db.commit()
        app=FastAPI();app.exception_handlers.update(application.exception_handlers);app.include_router(router,prefix='/api/v1')
        def disposable_db():
            with self.Session() as db:yield db
        app.dependency_overrides[get_db]=disposable_db
        self.client=TestClient(app,raise_server_exceptions=False);self.addCleanup(self.client.close)
        self.headers={'Authorization':'Bearer '+create_access_token(str(self.user))}

    def create(self,**values):
        return self.client.post('/api/v1/service-requests',headers=self.headers,json={'customer_id':str(self.customer),'title':'New request',**values})
    def patch(self,**values):
        return self.client.patch('/api/v1/service-requests/'+str(self.legacy),headers=self.headers,json=values)
    def read(self):
        return self.client.get('/api/v1/service-requests/'+str(self.legacy),headers=self.headers)

    def test_defaults_and_optional_asset(self):
        result=self.create();self.assertEqual(result.status_code,201,result.text)
        self.assertEqual((result.json()['priority'],result.json()['status'],result.json()['asset_id']),('Normal','Open',None))

    def test_all_canonical_priorities(self):
        for value in ['Low','Normal','High','Urgent']:
            with self.subTest(value=value):
                result=self.create(priority=value);self.assertEqual(result.status_code,201,result.text);self.assertEqual(result.json()['priority'],value)

    def test_all_canonical_statuses(self):
        for value in ['Open','In Progress','Resolved','Closed','Cancelled']:
            with self.subTest(value=value):
                result=self.create(status=value);self.assertEqual(result.status_code,201,result.text);self.assertEqual(result.json()['status'],value)

    def test_arbitrary_and_noncanonical_create_rejected(self):
        for field,value in [('priority','super-high'),('status','whatever'),('priority','high'),('priority','LOW'),('status','CLOSED'),('priority',None),('status',None)]:
            with self.subTest(field=field,value=value):
                result=self.create(**{field:value});self.assertEqual(result.status_code,422,result.text);self.assertNotIn('Traceback',result.text)

    def test_changed_values_enforced_and_patch_atomic(self):
        before=self.read().json()
        for field,value in [('priority','super-high'),('status','whatever'),('priority','high'),('status','CLOSED'),('priority',None),('status',None)]:
            result=self.patch(notes='Must not persist',**{field:value});self.assertEqual(result.status_code,422,result.text)
            self.assertEqual(self.read().json(),before)

    def test_legacy_read_and_unrelated_patch_preserve_bytes(self):
        for priority,status in [('high','CLOSED'),('LOW','Open'),('critical legacy','Awaiting parts')]:
            with self.Session() as db:
                row=db.get(ServiceRequest,self.legacy);row.priority=priority;row.status=status;db.commit()
            self.assertEqual(self.read().status_code,200)
            result=self.patch(notes='Unrelated edit');self.assertEqual(result.status_code,200,result.text)
            self.assertEqual((result.json()['priority'],result.json()['status']),(priority,status))
            self.assertEqual((self.read().json()['priority'],self.read().json()['status']),(priority,status))

    def test_explicit_canonical_replacement_persists(self):
        result=self.patch(priority='High',status='Closed');self.assertEqual(result.status_code,200,result.text)
        result=self.read().json();self.assertEqual((result['priority'],result['status']),('High','Closed'))
        self.assertEqual(self.patch(priority='Urgent',status='In Progress').status_code,200)
        self.assertEqual(self.read().json()['status'],'In Progress')

    def test_required_fields_and_unrelated_legacy_patch(self):
        for title in ['', '   ',None]:
            self.assertEqual(self.create(title=title).status_code,422)
            self.assertEqual(self.patch(title=title).status_code,422)
        self.assertEqual(self.create(customer_id=None).status_code,422)
        self.assertEqual(self.patch(customer_id=None).status_code,422)
        self.assertEqual(self.patch(description='Still editable').status_code,200)

    def test_request_soft_delete_remains_reserved_internal_status(self):
        self.assertEqual(self.create(status='Deleted').status_code,422)
        self.assertEqual(self.patch(status='Deleted').status_code,422)
        result=self.client.delete('/api/v1/service-requests/'+str(self.legacy),headers=self.headers)
        self.assertEqual(result.status_code,204,result.text);self.assertEqual(self.read().status_code,404)

if __name__=='__main__':unittest.main(verbosity=2)
