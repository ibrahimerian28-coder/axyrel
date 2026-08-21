"""Tenant-scoped persistence operations for inventory transactions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.tenant_isolation import require_company_id
from backend.models.inventory_transaction import InventoryTransaction
from backend.repositories.base import TenantScopedRepository


class InventoryTransactionRepository(TenantScopedRepository):
    """Repository for inventory movement ledger records."""

    def get(self, db: Session, company_id: UUID | None, transaction_id: UUID):
        company_id = self._require_company_scope(company_id)
        return db.scalar(
            select(InventoryTransaction).where(
                InventoryTransaction.id == transaction_id,
                InventoryTransaction.company_id == company_id,
            )
        )

    def list(
        self,
        db: Session,
        company_id: UUID | None,
        inventory_item_id: UUID | None = None,
        transaction_type: str | None = None,
    ):
        company_id = require_company_id(company_id)
        stmt = select(InventoryTransaction).where(
            InventoryTransaction.company_id == company_id
        )
        if inventory_item_id is not None:
            stmt = stmt.where(InventoryTransaction.inventory_item_id == inventory_item_id)
        if transaction_type and transaction_type.strip():
            stmt = stmt.where(InventoryTransaction.transaction_type == transaction_type.strip())
        stmt = stmt.order_by(InventoryTransaction.created_at.desc())
        return list(db.scalars(stmt).all())

    def create(
        self,
        db: Session,
        company_id: UUID | None,
        data: dict,
    ) -> InventoryTransaction:
        company_id = require_company_id(company_id)
        transaction = InventoryTransaction(company_id=company_id, **data)
        db.add(transaction)
        db.flush()
        return transaction
