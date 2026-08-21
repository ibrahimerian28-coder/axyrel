"""Business service for the Axyrel Service Request domain."""

from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.service_request import ServiceRequestRepository


class ServiceRequestService:
    """Application service for tenant-scoped service requests."""

    def __init__(self, repository: ServiceRequestRepository | None = None) -> None:
        self.repository = repository or ServiceRequestRepository()

    def list_requests(
        self,
        db: Session,
        company_id: UUID | None,
        customer_id: UUID | None = None,
        asset_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
    ):
        return self.repository.list(
            db, company_id, customer_id, asset_id, status, search
        )

    def get_request(
        self,
        db: Session,
        company_id: UUID | None,
        request_id: UUID,
    ):
        return self.repository.get(db, company_id, request_id)

    def create_request(
        self,
        db: Session,
        company_id: UUID | None,
        data: dict,
    ):
        return self.repository.create(db, company_id, data)

    def update_request(
        self,
        db: Session,
        company_id: UUID | None,
        request_id: UUID,
        data: dict,
    ):
        return self.repository.update(db, company_id, request_id, data)

    def delete_request(
        self,
        db: Session,
        company_id: UUID | None,
        request_id: UUID,
    ):
        return self.repository.soft_delete(db, company_id, request_id)
