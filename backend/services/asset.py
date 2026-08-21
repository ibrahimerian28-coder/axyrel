"""Business service for the Axyrel Asset domain."""

from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.asset import AssetRepository


class AssetService:
    """Application service for tenant-scoped asset operations."""

    def __init__(self, repository: AssetRepository | None = None) -> None:
        self.repository = repository or AssetRepository()

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
        return self.repository.create(db, company_id, data)

    def update_asset(
        self,
        db: Session,
        company_id: UUID | None,
        asset_id: UUID,
        data: dict,
    ):
        return self.repository.update(db, company_id, asset_id, data)

    def delete_asset(
        self,
        db: Session,
        company_id: UUID | None,
        asset_id: UUID,
    ):
        return self.repository.soft_delete(db, company_id, asset_id)
