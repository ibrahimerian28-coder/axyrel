"""Service Desk orchestrates existing entities inside the caller's transaction."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from uuid import uuid5
from sqlalchemy import select
from backend.core.service_lock import lock_service
from backend.models.customer import Customer
from backend.models.asset import Asset
from backend.models.user import User
from backend.services.service_request import ServiceRequestService
from backend.services.work_order import WorkOrderService
from backend.services.schedule import ScheduleService
from backend.services.service_visit import ServiceVisitService
from backend.schemas.schedule import ScheduleCreate
from backend.schemas.work_order import WorkOrderCreate
from backend.schemas.service_request import ServiceRequestCreate, REQUEST_PRIORITIES
from backend.repositories.service_history import ServiceHistoryRepository


class ServiceDeskService:
    def __init__(self):
        self.requests = ServiceRequestService()
        self.orders = WorkOrderService()
        self.schedules = ScheduleService()
        self.visits = ServiceVisitService()

    def _references(self, db, company_id, customer_id, asset_id=None, technician_id=None):
        customer = db.scalar(select(Customer).where(Customer.id == customer_id, Customer.company_id == company_id, Customer.status != "Deleted"))
        if not customer:
            raise ValueError("Customer not found")
        if asset_id:
            asset = db.scalar(select(Asset).where(Asset.id == asset_id, Asset.company_id == company_id, Asset.customer_id == customer_id, Asset.status != "Deleted"))
            if not asset:
                raise ValueError("Asset does not belong to this customer")
        if technician_id:
            technician = db.scalar(select(User).where(User.id == technician_id, User.company_id == company_id, User.role == "technician", User.is_active == True))
            if not technician:
                raise ValueError("Technician not found")

    def quick(self, db, company_id, payload):
        lock_service(db, company_id)
        request_id = uuid5(company_id, str(payload.pop("command_id")))
        if self.requests.get_request(db, company_id, request_id):
            return self.job_for_request(db, company_id, request_id)
        appointment = payload.pop("appointment", None)
        self._references(db, company_id, payload["customer_id"], payload.get("asset_id"), (appointment or {}).get("technician_id"))
        request = self.requests.create_request(db, company_id, {**ServiceRequestCreate(**payload).model_dump(), "id": request_id})
        if appointment:
            self.schedule_request(db, company_id, request.id, appointment)
        return self.job_for_request(db, company_id, request.id)

    def schedule_request(self, db, company_id, request_id, appointment):
        lock_service(db, company_id)
        request = self.requests.get_request(db, company_id, request_id)
        if not request or request.status in {"Cancelled", "Closed", "Resolved"}:
            raise ValueError("Request is unavailable for scheduling")
        orders = self.orders.list_work_orders(db, company_id, service_request_id=request_id)
        if orders:
            raise ValueError("Request already has a job; schedule that existing job")
        self._references(db, company_id, request.customer_id, request.asset_id, appointment["technician_id"])
        data = WorkOrderCreate(customer_id=request.customer_id, asset_id=request.asset_id,
            service_request_id=request.id, title=request.title, description=request.description,
            priority=next((p for p in REQUEST_PRIORITIES if p.casefold() == request.priority.strip().casefold()), request.priority), assigned_technician_id=appointment["technician_id"]).model_dump()
        order = self.orders.create_work_order(db, company_id, data)
        self.schedule_order(db, company_id, order.id, appointment)
        return self.job_for_order(db, company_id, order.id)

    def schedule_order(self, db, company_id, order_id, appointment):
        lock_service(db, company_id)
        order = self.orders.get_work_order(db, company_id, order_id)
        if not order:
            raise ValueError("Work order not found")
        self._references(db, company_id, order.customer_id, order.asset_id, appointment["technician_id"])
        data = ScheduleCreate(work_order_id=order.id, **appointment).model_dump()
        self.schedules.create_schedule(db, company_id, data)
        return self.job_for_order(db, company_id, order.id)

    def start(self, db, company_id, schedule_id):
        lock_service(db, company_id)
        schedule = self.schedules.get_schedule(db, company_id, schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")
        order = self.orders.get_work_order(db, company_id, schedule.work_order_id)
        if not order or order.status in {"Completed", "Cancelled"}:
            raise ValueError("Job is terminal")
        visits = self.visits.list_visits(db, company_id, schedule_id=schedule_id)
        active = next((v for v in visits if v.status == "In Progress"), None)
        if active:
            return self.job_for_order(db, company_id, order.id)
        if schedule.status != "Scheduled" or any(v.status in {"Completed", "Cancelled"} for v in visits):
            raise ValueError("Appointment is resolved; schedule another visit")
        technician = schedule.technician_id or order.assigned_technician_id
        if not technician:
            raise ValueError("Assign a technician before starting")
        self._references(db, company_id, order.customer_id, order.asset_id, technician)
        planned = next((v for v in visits if v.status == "Planned"), None)
        if planned:
            self.visits.update_visit(db, company_id, planned.id, {"status": "In Progress", "actual_start_at": datetime.now(timezone.utc), "technician_id": technician,
                "customer_id": order.customer_id, "asset_id": order.asset_id})
        else:
            self.visits.create_visit(db, company_id, dict(work_order_id=order.id, schedule_id=schedule.id,
                customer_id=order.customer_id, asset_id=order.asset_id, technician_id=technician,
                status="In Progress", actual_start_at=datetime.now(timezone.utc)))
        return self.job_for_order(db, company_id, order.id)

    def outcome(self, db, company_id, visit_id, payload):
        lock_service(db, company_id)
        visit = self.visits.get_visit(db, company_id, visit_id)
        if not visit:
            raise ValueError("Visit not found")
        outcome = payload["outcome"]
        complete = outcome in {"complete-job", "follow-up"}
        if not payload["notes"].strip():
            raise ValueError("Activity summary or reason is required")
        if visit.status == "Completed" and complete:
            # Follow-up retry must not add another appointment.
            if outcome == "complete-job":
                self.orders.update_work_order(db, company_id, visit.work_order_id, {"status": "Completed"})
            return self.job_for_order(db, company_id, visit.work_order_id)
        if visit.status == "Cancelled" and not complete:
            return self.job_for_order(db, company_id, visit.work_order_id)
        if visit.status != "In Progress":
            raise ValueError("Only active work can record this outcome")
        if outcome == "follow-up" and not payload.get("appointment"):
            future = self.schedules.list_schedules(db, company_id, work_order_id=visit.work_order_id)
            if not any(s.status == "Scheduled" and s.id != visit.schedule_id for s in future):
                raise ValueError("Choose the follow-up appointment")
        notes = payload["notes"].strip()
        if outcome == "unavailable":
            notes = f"Customer unavailable / no-show: {notes}"
        self.visits.update_visit(db, company_id, visit.id, {"status": "Completed" if complete else "Cancelled",
            "actual_end_at": datetime.now(timezone.utc), "notes": notes})
        if payload.get("appointment"):
            if outcome not in {"follow-up", "unavailable"}:
                raise ValueError("This outcome does not accept another appointment")
            self.schedule_order(db, company_id, visit.work_order_id, payload["appointment"])
        if outcome == "complete-job":
            self.orders.update_work_order(db, company_id, visit.work_order_id, {"status": "Completed"})
        return self.job_for_order(db, company_id, visit.work_order_id)

    def cancel_job(self, db, company_id, order_id, reason):
        lock_service(db, company_id)
        if not reason.strip():
            raise ValueError("A cancellation reason is required")
        order = self.orders.get_work_order(db, company_id, order_id)
        if not order:
            raise ValueError("Job not found")
        if order.status != "Cancelled":
            self.orders.update_work_order(db, company_id, order.id,
                {"status": "Cancelled", "notes": (order.notes or "") + f"\nJob cancelled: {reason.strip()}"})
        return self.job_for_order(db, company_id, order.id)

    def reschedule(self, db, company_id, schedule_id, appointment):
        lock_service(db, company_id)
        schedule = self.schedules.get_schedule(db, company_id, schedule_id)
        if not schedule:
            raise ValueError("Appointment not found")
        order = self.orders.get_work_order(db, company_id, schedule.work_order_id)
        if not order or order.status in {"Completed", "Cancelled"} or schedule.status != "Scheduled":
            raise ValueError("Only an outstanding appointment on an open job can be rescheduled")
        self._references(db, company_id, order.customer_id, order.asset_id, appointment["technician_id"])
        data = ScheduleCreate(work_order_id=order.id, **appointment).model_dump(exclude={"work_order_id", "status", "notes"})
        self.schedules.update_schedule(db, company_id, schedule.id, data)
        return self.job_for_order(db, company_id, order.id)

    def cancel_appointment(self, db, company_id, schedule_id, reason):
        lock_service(db, company_id)
        schedule = self.schedules.get_schedule(db, company_id, schedule_id)
        if not schedule or not reason.strip():
            raise ValueError("Appointment and cancellation reason are required")
        if schedule.status == "Cancelled":
            return self.job_for_order(db, company_id, schedule.work_order_id)
        self.schedules.update_schedule(db, company_id, schedule.id,
            {"status": "Cancelled", "notes": (schedule.notes or "") + f"\nAppointment cancelled: {reason.strip()}"})
        return self.job_for_order(db, company_id, schedule.work_order_id)

    def correct_terminal_job(self, db, company_id, order_id, reason):
        """Explicit audited repair of historical premature terminal aggregation."""
        lock_service(db, company_id)
        order = self.orders.get_work_order(db, company_id, order_id)
        if not order or not reason.strip():
            raise ValueError("Job and correction reason are required")
        schedules = self.schedules.list_schedules(db, company_id, work_order_id=order_id)
        visits = self.visits.list_visits(db, company_id, work_order_id=order_id)
        remaining = [s for s in schedules if s.status == "Scheduled" and not any(v.schedule_id == s.id and v.status in {"Completed", "Cancelled"} for v in visits)]
        if order.status not in {"Completed", "Cancelled"} or not remaining or any(v.status in {"Planned", "In Progress"} for v in visits):
            raise ValueError("Correction is only available for a terminal job with unexecuted appointments and no active visit")
        for visit in visits:
            if visit.schedule_id and visit.status in {"Completed", "Cancelled"}:
                self.visits.schedule_repository.update(db, company_id, visit.schedule_id, {"status": visit.status})
        # Intentional administrative exception, not automatic reopening.
        self.orders.repository.update(db, company_id, order.id, {"status": "Open",
            "notes": (order.notes or "") + f"\nLifecycle correction from {order.status}: {reason.strip()}"})
        return self.job_for_order(db, company_id, order.id)

    def job_for_request(self, db, company_id, request_id):
        return next(j for j in self.jobs(db, company_id) if j["request_id"] == request_id)

    def job_for_order(self, db, company_id, order_id):
        return next(j for j in self.jobs(db, company_id) if j["work_order_id"] == order_id)

    def jobs(self, db, company_id):
        requests = self.requests.list_requests(db, company_id)
        orders = self.orders.list_work_orders(db, company_id)
        schedules = self.schedules.list_schedules(db, company_id)
        visits = self.visits.list_visits(db, company_id)
        customers = {r.id: r for r in db.scalars(select(Customer).where(Customer.company_id == company_id))}
        assets = {r.id: r for r in db.scalars(select(Asset).where(Asset.company_id == company_id))}
        technicians = {r.id: r for r in db.scalars(select(User).where(User.company_id == company_id))}
        histories = ServiceHistoryRepository().list(db, company_id)
        request_by_id = {r.id: r for r in requests}
        rows = [(request_by_id.get(o.service_request_id), o) for o in orders]
        rows += [(r, None) for r in requests if not any(o.service_request_id == r.id for o in orders)]
        jobs = []
        today = datetime.now(ZoneInfo("Africa/Cairo")).date()
        for request, order in rows:
            source = order or request
            future = [s for s in schedules if order and s.work_order_id == order.id and s.status == "Scheduled"]
            activity = [v for v in visits if order and v.work_order_id == order.id]
            active = next((v for v in activity if v.status == "In Progress"), None)
            next_visit = next((s for s in future if not any(v.schedule_id == s.id and v.status in {"Completed", "Cancelled", "In Progress"} for v in activity)), None)
            status = "Cancelled" if source.status == "Cancelled" else "Completed" if source.status in {"Completed", "Closed", "Resolved"} else "In Progress" if active else "Follow-up" if any(v.status in {"Completed", "Cancelled"} for v in activity) else "Scheduled" if next_visit else "New"
            customer = customers.get(source.customer_id)
            asset = assets.get(source.asset_id)
            tech_id = active.technician_id if active else next_visit.technician_id if next_visit else order.assigned_technician_id if order else None
            technician = technicians.get(tech_id)
            phones = [str(getattr(customer, k, None) or "") for k in ("phone", "phone_1", "phone_2", "phone_3", "phone_4")]
            for p in getattr(customer, "phones", None) or []:
                phones.extend([str(p.get("number", "")), str(p.get("normalized", ""))])
            completed_today = status == "Completed" and any(v.actual_end_at and (v.actual_end_at.replace(tzinfo=timezone.utc) if v.actual_end_at.tzinfo is None else v.actual_end_at).astimezone(ZoneInfo("Africa/Cairo")).date() == today for v in activity if v.status == "Completed")
            jobs.append(dict(id=source.id, request_id=request.id if request else None, work_order_id=order.id if order else None,
                number=f"Job #{order.display_id}" if order and order.display_id else f"Request #{request.display_id}" if request and request.display_id else "Service job",
                customer_id=source.customer_id, customer=f"#{customer.display_id} · {customer.name}" if customer and customer.display_id else customer.name if customer else "Unavailable customer",
                phone=" / ".join(p for p in phones if p), location=" · ".join(str(getattr(customer, k, None) or "") for k in ("area", "address")),
                asset=f"#{asset.display_id} · {asset.serial_number or asset.model or asset.asset_type}" if asset and asset.display_id else asset.serial_number or asset.model or asset.asset_type if asset else "No asset",
                issue=source.title, description=source.description, priority=source.priority, technician_id=tech_id,
                technician=technician.full_name if technician else "Unassigned", status=status,
                next_schedule_id=next_visit.id if next_visit else None, next_visit=next_visit.start_at if next_visit else None,
                active_visit_id=active.id if active else None, history_ids=[h.id for h in histories if order and h.work_order_id == order.id],
                lifecycle_conflict=bool(order and order.status in {"Completed", "Cancelled"} and next_visit and not any(v.status in {"Planned", "In Progress"} for v in activity)),
                completed_today=completed_today))
        return jobs
