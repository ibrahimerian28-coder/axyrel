"""Business service for tenant-scoped service contracts."""
from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.service_contract import ServiceContractRepository
from backend.schemas.service_contract import validate_contract_dates


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
        record = self.repository.get(db, company_id, contract_id)
        if record is None:
            return None
        if "start_date" in data or "end_date" in data:
            start_date = data.get("start_date", record.start_date)
            end_date = data.get("end_date", record.end_date)
            # Required start_date null keeps the existing persistence semantics.
            if start_date is not None:
                validate_contract_dates(start_date, end_date)
        return self.repository.update(db, company_id, contract_id, data)

    def delete_contract(
        self, db: Session, company_id: UUID | None, contract_id: UUID
    ):
        return self.repository.soft_delete(db, company_id, contract_id)
