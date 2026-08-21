from datetime import date
from uuid import UUID
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from backend.repositories.customer import CustomerRepository

class CustomerService:
    def __init__(self, repository=None):
        self.repository = repository or CustomerRepository()

    def list_customers(self, db: Session, company_id: UUID | None, search=None):
        return self.repository.list(db, company_id, search)

    def get_customer(self, db, company_id, customer_id):
        return self.repository.get(db, company_id, customer_id)

    def create_customer(self, db, company_id, data):
        return self.repository.create(db, company_id, data)

    def update_customer(self, db, company_id, customer_id, data):
        return self.repository.update(db, company_id, customer_id, data)

    def delete_customer(self, db, company_id, customer_id):
        return self.repository.soft_delete(db, company_id, customer_id)

    @staticmethod
    def calculate_summary(customer, visits=None, today=None):
        visits = visits or []
        today = today or date.today()
        dates = sorted([v.get("visit_date") for v in visits if v.get("visit_date")], reverse=True)
        last_visit = dates[0] if dates else customer.install_date
        count = len(visits)
        try: cycle = int(float(str(customer.cycle or "0").strip()))
        except (TypeError, ValueError): cycle = 0
        next_visit = last_visit + relativedelta(months=cycle) if last_visit and cycle > 0 else None
        days = (next_visit - today).days if next_visit else None
        status = "" if days is None else ("Overdue" if days < 0 else "Due Soon" if days <= 30 else "On Schedule")
        return {"visits_count": count, "last_visit": last_visit, "next_visit": next_visit, "days_remaining": days, "visit_status": status}
