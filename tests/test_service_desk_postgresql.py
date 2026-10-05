"""Real PostgreSQL atomicity and cross-request locking, generated fixture only."""
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from backend.core.config import get_settings

url=make_url(get_settings().database_url)
if url.get_backend_name()!='postgresql' or url.host not in {'localhost','127.0.0.1','::1'}:
    raise RuntimeError('Local PostgreSQL configuration required; application DB is never connected.')
import test_service_desk as fixture


class ServiceDeskPostgreSQLTests(fixture.ServiceDeskTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.database='axyrel_phase3_test_'+uuid4().hex
        admin=create_engine(url.set(database='postgres'),isolation_level='AUTOCOMMIT')
        with admin.connect() as db:db.exec_driver_sql(f'CREATE DATABASE "{cls.database}"')
        admin.dispose()
        # Intentionally retain generated database; no DROP or persistent DB use.

    def new_engine(self):
        engine=create_engine(url.set(database=self.database))
        fixture.Base.metadata.create_all(engine)
        with engine.begin() as db:
            for table in reversed(fixture.Base.metadata.sorted_tables):db.execute(table.delete())
        return engine

    def test_concurrent_start_one_active_visit(self):
        j=self.quick()
        with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(lambda _:self.start(j),range(4)))
        self.assertEqual(len({r['active_visit_id'] for r in results}),1);self.assertEqual(self.counts()[3],1)

    def test_concurrent_completion_one_history(self):
        j=self.start(self.quick())
        with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(lambda _:self.outcome(j,'complete-job'),range(4)))
        self.assertEqual({r['status'] for r in results},{'Completed'});self.assertEqual(self.counts()[4],1)

    def test_concurrent_reversal_one_stock_restoration(self):
        j=self.start(self.quick());self.install(j)
        path='service-visits/'+j['active_visit_id']+'/parts/reverse'
        with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(lambda _:self.post(path,{'reason':'Concurrent correction'}),range(4)))
        self.assertEqual(self.stock(),8);self.assertEqual(self.counts()[5],2)
