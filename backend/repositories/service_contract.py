"""Tenant-scoped persistence operations for service contracts."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.tenant_isolation import require_company_id
from backend.models.service_contract import ServiceContract
from backend.repositories.base import TenantScopedRepository


class ServiceContractRepository(TenantScopedRepository):
    """Repository for tenant-scoped service contracts."""

    def get(
        self, db: Session, company_id: UUID | None, contract_id: UUID
    ) -> ServiceContract | None:
        company_id = self._require_company_scope(company_id)
        return db.scalar(
            select(ServiceContract).where(
                ServiceContract.id == contract_id,
                ServiceContract.company_id == company_id,
                ServiceContract.status != "Deleted",
            )
        )

    def list(
        self,
        db: Session,
        company_id: UUID | None,
        customer_id: UUID | None = None,
        status: str | None = None,
        billing_frequency: str | None = None,
    ) -> list[ServiceContract]:
        company_id = require_company_id(company_id)
        stmt = select(ServiceContract).where(
            ServiceContract.company_id == company_id,
            ServiceContract.status != "Deleted",
        )
        if customer_id is not None:
            stmt = stmt.where(ServiceContract.customer_id == customer_id)
        if status and status.strip():
            stmt = stmt.where(ServiceContract.status == status.strip())
        if billing_frequency and billing_frequency.strip():
            stmt = stmt.where(
                ServiceContract.billing_frequency == billing_frequency.strip()
            )
        return list(
            db.scalars(
                stmt.order_by(
                    ServiceContract.start_date.desc(),
                    ServiceContract.created_at.desc(),
                )
            ).all()
        )

    def create(
        self, db: Session, company_id: UUID | None, data: dict
    ) -> ServiceContract:
        company_id = require_company_id(company_id)
        record = ServiceContract(company_id=company_id, **data)
        db.add(record)
        db.flush()
        return record

    def update(
        self,
        db: Session,
        company_id: UUID | None,
        contract_id: UUID,
        data: dict,
    ) -> ServiceContract | None:
        record = self.get(db, company_id, contract_id)
        if record is None:
            return None
        for key, value in data.items():
            setattr(record, key, value)
        db.flush()
        return record

    def soft_delete(
        self, db: Session, company_id: UUID | None, contract_id: UUID
    ) -> ServiceContract | None:
        record = self.get(db, company_id, contract_id)
        if record is None:
            return None
        record.status = "Deleted"
        db.flush()
        return record
