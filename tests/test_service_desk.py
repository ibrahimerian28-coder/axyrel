"""Operational lifecycle acceptance on fresh in-memory disposable fixtures."""
import os
os.environ['DATABASE_URL']='sqlite:///:memory:'
os.environ['SECRET_KEY']='synthetic-service-desk-tests-at-least-32-bytes'
import unittest
from uuid import uuid4
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,select,func,event
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
import backend.models
from backend.models.base import Base
from backend.models.company import Company
from backend.models.customer import Customer
from backend.models.asset import Asset
from backend.models.user import User
from backend.models.work_order import WorkOrder
from backend.models.service_request import ServiceRequest
from backend.models.schedule import Schedule
from backend.models.service_visit import ServiceVisit
from backend.models.service_history import ServiceHistory
from backend.models.inventory_item import InventoryItem
from backend.models.technician_stock import TechnicianStock
from backend.models.inventory_transaction import InventoryTransaction
from backend.api.v1 import router
from backend.main import app as application
from backend.core.database import get_db
from backend.core.security import create_access_token,hash_password


class ServiceDeskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.password=hash_password('synthetic-password')
    def setUp(self):
        self.engine=self.new_engine()
        self.Session=sessionmaker(bind=self.engine,expire_on_commit=False)
        Base.metadata.create_all(self.engine)
        self.company,self.foreign,self.customer,self.asset,self.admin,self.tech,self.item,self.foreign_customer,self.foreign_tech=[uuid4() for _ in range(9)]
        with self.Session() as db:
            db.add_all([Company(id=self.company,name='Synthetic',status='active'),Company(id=self.foreign,name='Foreign',status='active')]);db.flush()
            db.add_all([Customer(id=self.customer,company_id=self.company,display_id=1011,name='Phone Customer',phone='+201000000011'),Customer(id=self.foreign_customer,company_id=self.foreign,name='Foreign customer')]);db.flush()
            db.add(Asset(id=self.asset,company_id=self.company,customer_id=self.customer,display_id=13,asset_type='Filter',serial_number='SMART-TEST-002'));db.flush()
            for id,role,tenant in [(self.admin,'admin',self.company),(self.tech,'technician',self.company),(self.foreign_tech,'technician',self.foreign)]:
                db.add(User(id=id,company_id=tenant,email=str(id)+'@example.test',full_name='Synthetic '+role,role=role,password_hash=self.password))
            db.add(InventoryItem(id=self.item,company_id=self.company,item_name='Filter',quantity=20,cost_price=5));db.flush()
            db.add(TechnicianStock(company_id=self.company,technician_id=self.tech,inventory_item_id=self.item,quantity=8));db.commit()
        app=FastAPI();app.exception_handlers.update(application.exception_handlers);app.include_router(router,prefix='/api/v1')
        def fixture():
            with self.Session() as db: yield db
        app.dependency_overrides[get_db]=fixture
        self.client=TestClient(app,raise_server_exceptions=False)
        self.headers={'Authorization':'Bearer '+create_access_token(str(self.admin))}
        self.addCleanup(self.client.close);self.addCleanup(self.engine.dispose)
    def new_engine(self):
        engine=create_engine('sqlite:///:memory:',poolclass=StaticPool,connect_args={'check_same_thread':False})
        @event.listens_for(engine,'connect')
        def fk(connection,_):connection.execute('PRAGMA foreign_keys=ON')
        return engine
    def post(self,path,data=None,status=200,headers=None):
        r=self.client.post('/api/v1/'+path,json=data,headers=headers or self.headers);self.assertEqual(r.status_code,status,r.text);return r.json() if r.content else None
    def get(self,path):
        r=self.client.get('/api/v1/'+path,headers=self.headers);self.assertEqual(r.status_code,200,r.text);return r.json()
    def appt(self,day=6):return dict(technician_id=str(self.tech),start_at=f'2026-10-{day:02d}T10:00:00',end_at=f'2026-10-{day:02d}T11:30:00')
    def quick(self,scheduled=True,**extra):
        return self.post('service-desk/quick',dict(command_id=str(uuid4()),customer_id=str(self.customer),asset_id=str(self.asset),title='RO Filter Urgent Maintenance',**({'appointment':self.appt()} if scheduled else {}),**extra),201)
    def start(self,job):return self.post('service-desk/schedules/'+job['next_schedule_id']+'/start')
    def outcome(self,job,outcome,**extra):return self.post('service-desk/visits/'+job['active_visit_id']+'/outcome',dict(outcome=outcome,notes='Recorded service activity',**extra))
    def counts(self):
        with self.Session() as db:return tuple(db.scalar(select(func.count()).select_from(m)) for m in [ServiceRequest,WorkOrder,Schedule,ServiceVisit,ServiceHistory,InventoryTransaction])
    def install(self,job,quantity=2,status=200):return self.post('service-visits/'+job['active_visit_id']+'/parts',dict(inventory_item_id=str(self.item),quantity=quantity),status)
    def stock(self):
        with self.Session() as db:return db.scalar(select(TechnicianStock.quantity).where(TechnicianStock.technician_id==self.tech))
    def test_save_request_only(self):
        j=self.quick(False);self.assertEqual(j['status'],'New');self.assertEqual(self.counts(),(1,0,0,0,0,0))
    def test_atomic_create_schedule_links(self):
        j=self.quick();self.assertEqual(j['status'],'Scheduled');self.assertEqual(self.counts()[:3],(1,1,1));s=self.get('schedules')[0];o=self.get('work-orders')[0];self.assertEqual(s['work_order_id'],o['id']);self.assertEqual(o['service_request_id'],j['request_id']);self.assertEqual(s['start_at'],'2026-10-06T07:00:00Z')
    def test_failed_range_rolls_back_chain(self):
        a=self.appt();a['end_at']=a['start_at']
        self.post('service-desk/quick',dict(command_id=str(uuid4()),customer_id=str(self.customer),title='Failure',appointment=a),400);self.assertEqual(self.counts(),(0,0,0,0,0,0))
    def test_downstream_failure_rolls_back(self):
        with patch('backend.services.schedule.ScheduleService.create_schedule',side_effect=ValueError('Synthetic failure')):
            self.post('service-desk/quick',dict(command_id=str(uuid4()),customer_id=str(self.customer),title='Failure',appointment=self.appt()),400)
        self.assertEqual(self.counts(),(0,0,0,0,0,0))
    def test_quick_retry_one_chain(self):
        payload=dict(command_id=str(uuid4()),customer_id=str(self.customer),title='Retry',appointment=self.appt());a=self.post('service-desk/quick',payload,201);b=self.post('service-desk/quick',payload,201);self.assertEqual(a,b);self.assertEqual(self.counts()[:3],(1,1,1))
    def test_foreign_customer_rejected(self):
        self.post('service-desk/quick',dict(command_id=str(uuid4()),customer_id=str(self.foreign_customer),title='Forbidden'),400);self.assertEqual(self.counts()[0],0)
    def test_foreign_technician_rejected_atomic(self):
        a=self.appt();a['technician_id']=str(self.foreign_tech);self.post('service-desk/quick',dict(command_id=str(uuid4()),customer_id=str(self.customer),title='Forbidden',appointment=a),400);self.assertEqual(self.counts()[:3],(0,0,0))
    def test_foreign_jobs_hidden_and_mutations_rejected(self):
        j=self.quick();headers={'Authorization':'Bearer '+create_access_token(str(self.foreign_tech))};self.assertEqual(self.client.get('/api/v1/service-desk',headers=headers).json(),[]);self.post('service-desk/schedules/'+j['next_schedule_id']+'/start',status=400,headers=headers)
    def test_unauthenticated_denied(self): self.assertEqual(self.client.get('/api/v1/service-desk').status_code,401)
    def test_invalid_role_denied(self):
        with self.Session() as db:db.get(User,self.admin).role='invalid';db.commit()
        self.assertEqual(self.client.get('/api/v1/service-desk',headers=self.headers).status_code,403)
    def test_technician_existing_permissions(self):
        self.quick();h={'Authorization':'Bearer '+create_access_token(str(self.tech))};self.assertEqual(self.client.get('/api/v1/service-desk',headers=h).status_code,200)
        r=self.client.post('/api/v1/customers',headers=h,json={'name':'Not permitted'});self.assertEqual(r.status_code,403)
    def test_start_links_and_retry(self):
        j=self.quick();active=self.start(j);again=self.start(j);self.assertEqual(active['active_visit_id'],again['active_visit_id']);self.assertEqual(self.counts()[3],1);v=self.get('service-visits')[0];self.assertEqual(v['status'],'In Progress');self.assertEqual(v['schedule_id'],j['next_schedule_id']);self.assertEqual(v['customer_id'],str(self.customer));self.assertEqual(v['asset_id'],str(self.asset));self.assertEqual(v['technician_id'],str(self.tech))
    def test_explicit_complete_job_and_history_retry(self):
        j=self.start(self.quick());completed=self.outcome(j,'complete-job');self.assertEqual(completed['status'],'Completed');self.outcome(j,'complete-job');self.assertEqual(self.counts()[4],1);h=self.get('service-history')[0];self.assertEqual(h['service_visit_id'],j['active_visit_id']);self.assertEqual(h['technician_id'],str(self.tech));self.assertEqual(h['notes'],'Recorded service activity');self.assertEqual(self.get('schedules')[0]['status'],'Completed')
    def test_complete_job_rejects_unresolved_second_schedule_atomic(self):
        j=self.quick();self.post('service-desk/jobs/'+j['work_order_id']+'/schedule',self.appt(8));j=self.start(j);self.post('service-desk/visits/'+j['active_visit_id']+'/outcome',dict(outcome='complete-job',notes='Done'),400);self.assertEqual(self.get('service-visits')[0]['status'],'In Progress');self.assertEqual(self.counts()[4],0)
    def test_exact_multischedule_completed_then_cancelled_second_starts(self):
        j=self.quick();self.post('service-desk/jobs/'+j['work_order_id']+'/schedule',self.appt(8));j=self.start(j);v=j['active_visit_id']
        for status in ['Completed','Cancelled']:
            r=self.client.patch('/api/v1/service-visits/'+v,headers=self.headers,json={'status':status});self.assertEqual(r.status_code,200,r.text);self.assertNotIn(self.get('work-orders')[0]['status'],['Completed','Cancelled'])
        next_job=self.get('service-desk')[0];self.assertEqual(next_job['status'],'Follow-up');second=self.start(next_job);self.assertNotEqual(second['active_visit_id'],v);self.assertEqual(second['work_order_id'],j['work_order_id']);self.assertEqual(self.get('service-history')[0]['status'],'Corrected')
    def test_followup_same_order_and_retry(self):
        j=self.start(self.quick());f=self.outcome(j,'follow-up',appointment=self.appt(8));self.assertEqual(f['status'],'Follow-up');self.outcome(j,'follow-up',appointment=self.appt(8));self.assertEqual(self.counts()[:5],(1,1,2,1,1));second=self.start(f);self.assertEqual(second['work_order_id'],j['work_order_id'])
    def test_no_show_not_completed_and_reschedule(self):
        j=self.start(self.quick());f=self.outcome(j,'unavailable');self.assertEqual(self.counts()[4],0);self.assertEqual(self.get('service-visits')[0]['status'],'Cancelled');self.assertEqual(f['status'],'Follow-up');new=self.post('service-desk/jobs/'+j['work_order_id']+'/schedule',self.appt(8));self.start(new)
    def test_cancel_visit_leaves_job_nonterminal(self):
        j=self.start(self.quick());f=self.outcome(j,'cancel-visit');self.assertEqual(f['status'],'Follow-up');self.assertEqual(self.get('work-orders')[0]['status'],'Open')
    def test_cancel_job_reason_and_all_appointments(self):
        j=self.quick();self.post('service-desk/jobs/'+j['work_order_id']+'/schedule',self.appt(8));self.start(j);cancelled=self.post('service-desk/jobs/'+j['work_order_id']+'/cancel',{'reason':'Customer declined'});self.assertEqual(cancelled['status'],'Cancelled');self.assertEqual({s['status'] for s in self.get('schedules')},{'Cancelled'});self.assertIn('Customer declined',self.get('work-orders')[0]['notes'])
    def test_active_install_and_full_reversal_retry(self):
        j=self.start(self.quick());self.install(j);self.assertEqual(self.stock(),6);path='service-visits/'+j['active_visit_id']+'/parts/reverse';self.post(path,{'reason':'Wrong quantity'});self.assertEqual(self.stock(),8);self.post(path,{'reason':'Retry'});self.assertEqual(self.counts()[5],2);self.install(j,1);self.assertEqual(self.stock(),7);self.outcome(j,'cancel-visit');self.assertEqual(self.stock(),8);self.assertEqual(self.counts()[5],4)
    def test_terminal_part_install_rejected(self):
        for outcome in ['complete-job','cancel-visit']:
            j=self.start(self.quick());self.outcome(j,outcome);self.install(j,status=400)
        self.assertEqual(self.stock(),8)
    def test_completed_cancel_reverses_preserves_history(self):
        j=self.start(self.quick());self.install(j);self.outcome(j,'complete-job');self.post('service-desk/jobs/'+j['work_order_id']+'/cancel',{'reason':'Correction'});self.assertEqual(self.stock(),8);history=self.get('service-history')[0];self.assertEqual(history['status'],'Corrected');self.assertEqual(history['notes'],'Recorded service activity')
    def test_resolved_schedule_not_reopened_or_deleted(self):
        j=self.start(self.quick());sid=self.get('service-visits')[0]['schedule_id'];self.outcome(j,'complete-job');r=self.client.patch('/api/v1/schedules/'+sid,headers=self.headers,json={'status':'Scheduled'});self.assertEqual(r.status_code,400);r=self.client.delete('/api/v1/schedules/'+sid,headers=self.headers);self.assertEqual(r.status_code,400)
    def test_save_request_later_schedule(self):
        j=self.quick(False);s=self.post('service-desk/requests/'+j['request_id']+'/schedule',self.appt());self.assertEqual(s['status'],'Scheduled');self.assertEqual(self.counts()[:3],(1,1,1))
    def test_terminal_job_cannot_schedule(self):
        j=self.start(self.quick());self.outcome(j,'complete-job');self.post('service-desk/jobs/'+j['work_order_id']+'/schedule',self.appt(8),400)
    def test_cancel_future_appointment_only(self):
        j=self.quick();self.post('service-desk/jobs/'+j['work_order_id']+'/schedule',self.appt(8));self.post('service-desk/schedules/'+j['next_schedule_id']+'/cancel',{'reason':'Customer requested another date'});self.assertEqual(self.get('work-orders')[0]['status'],'Open');self.assertEqual([s['status'] for s in self.get('schedules')],['Cancelled','Scheduled'])
    def test_complete_visit_keeps_existing_followup_without_extra_schedule(self):
        j=self.quick();self.post('service-desk/jobs/'+j['work_order_id']+'/schedule',self.appt(8));j=self.start(j);f=self.outcome(j,'follow-up');self.assertEqual(f['status'],'Follow-up');self.assertEqual(self.counts()[:5],(1,1,2,1,1));self.start(f)
    def test_blank_outcome_and_reason_are_rejected(self):
        j=self.start(self.quick());self.post('service-desk/visits/'+j['active_visit_id']+'/outcome',{'outcome':'complete-job','notes':' '},400);self.post('service-desk/jobs/'+j['work_order_id']+'/cancel',{'reason':' '},400);self.assertEqual(self.get('service-visits')[0]['status'],'In Progress')
    def test_part_correction_foreign_tenant_and_terminal_rejected(self):
        j=self.start(self.quick());self.install(j);path='service-visits/'+j['active_visit_id']+'/parts/reverse';h={'Authorization':'Bearer '+create_access_token(str(self.foreign_tech))};self.post(path,{'reason':'Foreign'},404,headers=h);self.assertEqual(self.stock(),6);self.outcome(j,'complete-job');self.post(path,{'reason':'Terminal'},400);self.assertEqual(self.stock(),6)
    def test_explicit_legacy_lifecycle_correction_and_second_visit(self):
        j=self.quick();self.post('service-desk/jobs/'+j['work_order_id']+'/schedule',self.appt(8));active=self.start(j);self.outcome(active,'cancel-visit')
        from uuid import UUID
        with self.Session() as db:
            db.get(WorkOrder,UUID(j['work_order_id'])).status='Cancelled'
            db.get(Schedule,UUID(j['next_schedule_id'])).status='Scheduled'
            db.commit()
        legacy=self.get('service-desk')[0];self.assertTrue(legacy['lifecycle_conflict']);before=self.counts()
        corrected=self.post('service-desk/jobs/'+j['work_order_id']+'/correct-lifecycle',{'reason':'Review confirmed premature visit aggregation'})
        self.assertEqual(corrected['status'],'Follow-up');self.assertEqual(self.counts(),before);self.assertIn('Lifecycle correction from Cancelled',self.get('work-orders')[0]['notes']);self.start(corrected)
    def test_explicit_cancelled_job_has_no_correction_path(self):
        j=self.quick();self.post('service-desk/jobs/'+j['work_order_id']+'/cancel',{'reason':'Intentional whole job cancellation'});self.assertFalse(self.get('service-desk')[0]['lifecycle_conflict']);self.post('service-desk/jobs/'+j['work_order_id']+'/correct-lifecycle',{'reason':'Invalid reopening'},400)
    def test_lifecycle_correction_requires_audit_permission(self):
        j=self.quick();h={'Authorization':'Bearer '+create_access_token(str(self.tech))};self.post('service-desk/jobs/'+j['work_order_id']+'/correct-lifecycle',{'reason':'Not allowed'},403,headers=h)
    def test_start_existing_planned_visit_fills_authoritative_context(self):
        j=self.quick();v=self.post('service-visits',dict(work_order_id=j['work_order_id'],schedule_id=j['next_schedule_id'],customer_id=str(self.customer)),201)
        active=self.start(j);self.assertEqual(active['active_visit_id'],v['id']);self.assertEqual(self.get('service-visits')[0]['asset_id'],str(self.asset));self.assertEqual(self.counts()[3],1)
    def test_legacy_request_priority_new_order_is_canonical_without_rewriting_request(self):
        j=self.quick(False)
        from uuid import UUID
        with self.Session() as db:db.get(ServiceRequest,UUID(j['request_id'])).priority='high';db.commit()
        self.post('service-desk/requests/'+j['request_id']+'/schedule',self.appt());self.assertEqual(self.get('work-orders')[0]['priority'],'High');self.assertEqual(self.get('service-requests')[0]['priority'],'high')
    def test_reschedule_rejects_foreign_technician_without_changes(self):
        j=self.quick();before=self.get('schedules');a=self.appt(8);a['technician_id']=str(self.foreign_tech);self.post('service-desk/schedules/'+j['next_schedule_id']+'/reschedule',a,400);self.assertEqual(self.get('schedules'),before)

if __name__=='__main__':unittest.main()
