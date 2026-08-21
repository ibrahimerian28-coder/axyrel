"""Repository operations for Axyrel companies."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.company import Company


class CompanyRepository:
    def get_by_id(self, db: Session, company_id: UUID) -> Company | None:
        return db.scalar(select(Company).where(Company.id == company_id))
