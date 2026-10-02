"""Business service for the Axyrel Service History domain."""

from uuid import UUID
from sqlalchemy.orm import Session
from backend.repositories.service_history import ServiceHistoryRepository
from backend.repositories.service_visit import ServiceVisitRepository


class ServiceVisitReferenceError(ValueError):
    """A supplied history link does not resolve to a visible tenant visit."""


class ServiceHistoryService:
    """Application service for tenant-scoped service history."""

    def __init__(self, repository: ServiceHistoryRepository | None = None,
                 service_visit_repository: ServiceVisitRepository | None = None) -> None:
        self.repository = repository or ServiceHistoryRepository()
        self.service_visit_repository = service_visit_repository or ServiceVisitRepository()

    def _validate_visit(self, db: Session, company_id: UUID | None, visit_id: UUID | None):
        if visit_id is not None and self.service_visit_repository.get(db, company_id, visit_id) is None:
            raise ServiceVisitReferenceError("Service visit not found.")

    def list_history(self, db: Session, company_id: UUID | None, **filters): return self.repository.list(db, company_id, **filters)
    def get_history(self, db: Session, company_id: UUID | None, history_id: UUID): return self.repository.get(db, company_id, history_id)
    def create_history(self, db: Session, company_id: UUID | None, data: dict):
        self._validate_visit(db, company_id, data.get("service_visit_id"))
        return self.repository.create(db, company_id, data)

    def update_history(self, db: Session, company_id: UUID | None, history_id: UUID, data: dict):
        record = self.repository.get(db, company_id, history_id)
        if record is None:
            return None
        if "service_visit_id" in data:
            self._validate_visit(db, company_id, data["service_visit_id"])
        return self.repository.update(db, company_id, history_id, data)
    def delete_history(self, db: Session, company_id: UUID | None, history_id: UUID): return self.repository.soft_delete(db, company_id, history_id)
