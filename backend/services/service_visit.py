"""Business service for the Axyrel Service Visit domain."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.service_visit import ServiceVisitRepository


class ServiceVisitService:
    """Application service for tenant-scoped service visits."""

    def __init__(self, repository: ServiceVisitRepository | None = None) -> None:
        self.repository = repository or ServiceVisitRepository()

    def list_visits(self, db: Session, company_id: UUID | None, **filters):
        return self.repository.list(db, company_id, **filters)

    def get_visit(self, db: Session, company_id: UUID | None, visit_id: UUID):
        return self.repository.get(db, company_id, visit_id)

    def create_visit(self, db: Session, company_id: UUID | None, data: dict):
        return self.repository.create(db, company_id, data)

    def update_visit(self, db: Session, company_id: UUID | None, visit_id: UUID, data: dict):
        return self.repository.update(db, company_id, visit_id, data)

    def delete_visit(self, db: Session, company_id: UUID | None, visit_id: UUID):
        return self.repository.soft_delete(db, company_id, visit_id)
