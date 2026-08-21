"""Business service for the Axyrel Service History domain."""

from uuid import UUID
from sqlalchemy.orm import Session
from backend.repositories.service_history import ServiceHistoryRepository


class ServiceHistoryService:
    """Application service for tenant-scoped service history."""

    def __init__(self, repository: ServiceHistoryRepository | None = None) -> None:
        self.repository = repository or ServiceHistoryRepository()

    def list_history(self, db: Session, company_id: UUID | None, **filters): return self.repository.list(db, company_id, **filters)
    def get_history(self, db: Session, company_id: UUID | None, history_id: UUID): return self.repository.get(db, company_id, history_id)
    def create_history(self, db: Session, company_id: UUID | None, data: dict): return self.repository.create(db, company_id, data)
    def update_history(self, db: Session, company_id: UUID | None, history_id: UUID, data: dict): return self.repository.update(db, company_id, history_id, data)
    def delete_history(self, db: Session, company_id: UUID | None, history_id: UUID): return self.repository.soft_delete(db, company_id, history_id)
