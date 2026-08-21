"""Business service for tenant-scoped service contracts."""
from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.service_contract import ServiceContractRepository


class ServiceContractService:
    def __init__(
        self, repository: ServiceContractRepository | None = None
    ) -> None:
        self.repository = repository or ServiceContractRepository()

    def list_contracts(self, db: Session, company_id: UUID | None, **filters):
        return self.repository.list(db, company_id, **filters)

    def get_contract(
        self, db: Session, company_id: UUID | None, contract_id: UUID
    ):
        return self.repository.get(db, company_id, contract_id)

    def create_contract(
        self, db: Session, company_id: UUID | None, data: dict
    ):
        return self.repository.create(db, company_id, data)

    def update_contract(
        self,
        db: Session,
        company_id: UUID | None,
        contract_id: UUID,
        data: dict,
    ):
        return self.repository.update(db, company_id, contract_id, data)

    def delete_contract(
        self, db: Session, company_id: UUID | None, contract_id: UUID
    ):
        return self.repository.soft_delete(db, company_id, contract_id)
