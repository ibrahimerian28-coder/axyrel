"""Transactional operational API; no browser-side chain writes."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authorization import Permission, require_permission
from backend.schemas.service_desk import QuickService, Appointment, VisitOutcome, Reason
from backend.services.service_desk import ServiceDeskService

router = APIRouter(prefix="/service-desk", tags=["service desk"])
service = ServiceDeskService()
manage = [Depends(require_permission(Permission.SERVICE_MANAGE))]


def command(db, operation):
    try:
        result = operation()
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        raise


@router.get("", dependencies=[Depends(require_permission(Permission.SERVICE_READ))])
def list_jobs(db: DBSession, company_id: CompanyID):
    return service.jobs(db, company_id)


@router.post("/quick", status_code=201, dependencies=manage)
def quick(payload: QuickService, db: DBSession, company_id: CompanyID):
    return command(db, lambda: service.quick(db, company_id, payload.model_dump()))


@router.post("/requests/{request_id}/schedule", dependencies=manage)
def schedule_request(request_id: UUID, payload: Appointment, db: DBSession, company_id: CompanyID):
    return command(db, lambda: service.schedule_request(db, company_id, request_id, payload.model_dump()))


@router.post("/jobs/{order_id}/schedule", dependencies=manage)
def schedule_job(order_id: UUID, payload: Appointment, db: DBSession, company_id: CompanyID):
    return command(db, lambda: service.schedule_order(db, company_id, order_id, payload.model_dump()))


@router.post("/schedules/{schedule_id}/start", dependencies=manage)
def start(schedule_id: UUID, db: DBSession, company_id: CompanyID):
    return command(db, lambda: service.start(db, company_id, schedule_id))


@router.post("/schedules/{schedule_id}/reschedule", dependencies=manage)
def reschedule(schedule_id: UUID, payload: Appointment, db: DBSession, company_id: CompanyID):
    return command(db, lambda: service.reschedule(db, company_id, schedule_id, payload.model_dump()))


@router.post("/visits/{visit_id}/outcome", dependencies=manage)
def outcome(visit_id: UUID, payload: VisitOutcome, db: DBSession, company_id: CompanyID):
    return command(db, lambda: service.outcome(db, company_id, visit_id, payload.model_dump()))


@router.post("/jobs/{order_id}/cancel", dependencies=manage)
def cancel_job(order_id: UUID, payload: Reason, db: DBSession, company_id: CompanyID):
    return command(db, lambda: service.cancel_job(db, company_id, order_id, payload.reason))


@router.post("/schedules/{schedule_id}/cancel", dependencies=manage)
def cancel_appointment(schedule_id: UUID, payload: Reason, db: DBSession, company_id: CompanyID):
    return command(db, lambda: service.cancel_appointment(db, company_id, schedule_id, payload.reason))


@router.post("/jobs/{order_id}/correct-lifecycle", dependencies=manage + [Depends(require_permission(Permission.AUDIT_READ))])
def correct_lifecycle(order_id: UUID, payload: Reason, db: DBSession, company_id: CompanyID):
    return command(db, lambda: service.correct_terminal_job(db, company_id, order_id, payload.reason))
