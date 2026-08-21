"""Repository operations for database-backed Axyrel users."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.user import User


class UserRepository:
    def get_by_id(self, db: Session, user_id: UUID) -> User | None:
        return db.scalar(select(User).where(User.id == user_id))

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(func.lower(User.email) == email.lower()))
