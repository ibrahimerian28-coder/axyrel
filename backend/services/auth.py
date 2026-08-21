"""Authentication and identity business logic for Axyrel."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from backend.core.security import verify_password
from backend.models.user import User
from backend.repositories.user import UserRepository


class AuthenticationService:
    def __init__(self, user_repository: UserRepository | None = None):
        self.user_repository = user_repository or UserRepository()

    @staticmethod
    def _company_is_active(user: User) -> bool:
        company = user.company
        return company is not None and company.status == "active"

    def authenticate(self, db: Session, email: str, password: str) -> User | None:
        user = self.user_repository.get_by_email(db, email.strip().lower())
        if user is None or not user.is_active or not self._company_is_active(user):
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def get_active_user(self, db: Session, user_id: UUID) -> User | None:
        user = self.user_repository.get_by_id(db, user_id)
        if user is None or not user.is_active or not self._company_is_active(user):
            return None
        return user

    @staticmethod
    def record_login(user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)
