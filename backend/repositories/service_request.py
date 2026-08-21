"""Persistence operations for tenant-scoped Service Requests."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.tenant_isolation import require_company_id
from backend.models.service_request import ServiceRequest
from backend.repositories.base import TenantScopedRepository


class ServiceRequestRepository(TenantScopedRepository):
    """Tenant-scoped repository for Service Request records."""

    def get(
        self,
        db: Session,
        company_id: UUID | None,
        request_id: UUID,
    ) -> ServiceRequest | None:
        company_id = self._require_company_scope(company_id)
        return db.scalar(
            select(ServiceRequest).where(
                ServiceRequest.id == request_id,
                ServiceRequest.company_id == company_id,
                ServiceRequest.status != "Deleted",
            )
        )

    def list(
        self,
        db: Session,
        company_id: UUID | None,
        customer_id: UUID | None = None,
        asset_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[ServiceRequest]:
        company_id = require_company_id(company_id)
        stmt = select(ServiceRequest).where(
            ServiceRequest.company_id == company_id,
            ServiceRequest.status != "Deleted",
        )

        if customer_id is not None:
            stmt = stmt.where(ServiceRequest.customer_id == customer_id)
        if asset_id is not None:
            stmt = stmt.where(ServiceRequest.asset_id == asset_id)
        if status and status.strip():
            stmt = stmt.where(ServiceRequest.status == status.strip())
        if search and search.strip():
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                ServiceRequest.title.ilike(term)
                | ServiceRequest.description.ilike(term)
            )

        return list(
            db.scalars(
                stmt.order_by(ServiceRequest.requested_at.desc())
            ).all()
        )

    def create(
        self,
        db: Session,
        company_id: UUID | None,
        data: dict,
    ) -> ServiceRequest:
        company_id = require_company_id(company_id)
        display_id = data.pop("display_id", None)
        if display_id is None:
            max_id = db.scalar(select(func.max(ServiceRequest.display_id)).where(ServiceRequest.company_id == company_id)) or 0
            display_id = int(max_id) + 1
        request = ServiceRequest(company_id=company_id, display_id=display_id, **data)
        db.add(request)
        db.flush()
        return request

    def update(
        self,
        db: Session,
        company_id: UUID | None,
        request_id: UUID,
        data: dict,
    ) -> ServiceRequest | None:
        request = self.get(db, company_id, request_id)
        if request is None:
            return None

        for key, value in data.items():
            setattr(request, key, value)
        db.flush()
        return request

    def soft_delete(
        self,
        db: Session,
        company_id: UUID | None,
        request_id: UUID,
    ) -> ServiceRequest | None:
        company_id = self._require_company_scope(company_id)
        request = db.scalar(
            select(ServiceRequest).where(
                ServiceRequest.id == request_id,
                ServiceRequest.company_id == company_id,
            )
        )
        if request is None:
            return None

        request.status = "Deleted"
        db.flush()
        return request
