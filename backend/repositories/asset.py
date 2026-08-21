"""Persistence operations for customer assets."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.tenant_isolation import require_company_id
from backend.models.asset import Asset
from backend.repositories.base import TenantScopedRepository


class AssetRepository(TenantScopedRepository):
    """Tenant-scoped repository for Asset records."""

    def get(
        self,
        db: Session,
        company_id: UUID | None,
        asset_id: UUID,
    ) -> Asset | None:
        company_id = self._require_company_scope(company_id)
        return db.scalar(
            select(Asset).where(
                Asset.id == asset_id,
                Asset.company_id == company_id,
                Asset.status != "Deleted",
            )
        )

    def list(
        self,
        db: Session,
        company_id: UUID | None,
        customer_id: UUID | None = None,
        search: str | None = None,
    ) -> list[Asset]:
        company_id = require_company_id(company_id)
        stmt = select(Asset).where(
            Asset.company_id == company_id,
            Asset.status != "Deleted",
        )

        if customer_id is not None:
            stmt = stmt.where(Asset.customer_id == customer_id)

        if search and search.strip():
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                Asset.asset_type.ilike(term)
                | Asset.serial_number.ilike(term)
                | Asset.model.ilike(term)
                | Asset.manufacturer.ilike(term)
            )

        return list(
            db.scalars(
                stmt.order_by(Asset.display_id, Asset.asset_type)
            ).all()
        )

    def create(
        self,
        db: Session,
        company_id: UUID | None,
        data: dict,
    ) -> Asset:
        company_id = require_company_id(company_id)
        display_id = data.pop("display_id", None)
        if display_id is None:
            max_id = db.scalar(select(func.max(Asset.display_id)).where(Asset.company_id == company_id)) or 0
            display_id = int(max_id) + 1
        asset = Asset(company_id=company_id, display_id=display_id, **data)
        db.add(asset)
        db.flush()
        return asset

    def update(
        self,
        db: Session,
        company_id: UUID | None,
        asset_id: UUID,
        data: dict,
    ) -> Asset | None:
        asset = self.get(db, company_id, asset_id)
        if asset is None:
            return None

        for key, value in data.items():
            setattr(asset, key, value)
        db.flush()
        return asset

    def soft_delete(
        self,
        db: Session,
        company_id: UUID | None,
        asset_id: UUID,
    ) -> Asset | None:
        company_id = self._require_company_scope(company_id)
        asset = db.scalar(
            select(Asset).where(
                Asset.id == asset_id,
                Asset.company_id == company_id,
            )
        )
        if asset is None:
            return None

        asset.status = "Deleted"
        db.flush()
        return asset
