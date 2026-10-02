"""Business service for the Axyrel Asset domain."""

from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.asset import AssetRepository
from backend.repositories.customer import CustomerRepository


class AssetService:
    """Application service for tenant-scoped asset operations."""

    def __init__(
        self,
        repository: AssetRepository | None = None,
        customer_repository: CustomerRepository | None = None,
    ) -> None:
        self.repository = repository or AssetRepository()
        self.customer_repository = customer_repository or CustomerRepository()

    def _validate_customer(self, db, company_id, customer_id):
        if customer_id is None:
            raise ValueError("Customer is required.")
        if self.customer_repository.get(db, company_id, customer_id) is None:
            raise ValueError("Customer not found.")

    def list_assets(
        self,
        db: Session,
        company_id: UUID | None,
        customer_id: UUID | None = None,
        search: str | None = None,
    ):
        return self.repository.list(db, company_id, customer_id, search)

    def get_asset(
        self,
        db: Session,
        company_id: UUID | None,
        asset_id: UUID,
    ):
        return self.repository.get(db, company_id, asset_id)

    def create_asset(
        self,
        db: Session,
        company_id: UUID | None,
        data: dict,
    ):
        self._validate_customer(db, company_id, data.get("customer_id"))
        return self.repository.create(db, company_id, data)

    def update_asset(
        self,
        db: Session,
        company_id: UUID | None,
        asset_id: UUID,
        data: dict,
    ):
        if self.repository.get(db, company_id, asset_id) is None:
            return None
        if "customer_id" in data:
            self._validate_customer(db, company_id, data["customer_id"])
        return self.repository.update(db, company_id, asset_id, data)

    def delete_asset(
        self,
        db: Session,
        company_id: UUID | None,
        asset_id: UUID,
    ):
        return self.repository.soft_delete(db, company_id, asset_id)
