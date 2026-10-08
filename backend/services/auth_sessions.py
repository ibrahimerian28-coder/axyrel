"""Opaque 256-bit credentials with hash-only durable storage and no time expiry."""
import hashlib
import re
import secrets
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.models.auth_session import AuthSession
from backend.models.user import User

PREFIX = "axs_"


def credential_hash(credential: str) -> str | None:
    if not re.fullmatch(r"axs_[A-Za-z0-9_-]{43}", credential):
        return None
    return hashlib.sha256(credential.encode("ascii")).hexdigest()


def issue_session(db: Session, user: User) -> str:
    credential = PREFIX + secrets.token_urlsafe(32)
    db.add(AuthSession(user_id=user.id, company_id=user.company_id, secret_hash=credential_hash(credential)))
    return credential


def resolve_session(db: Session, credential: str) -> AuthSession | None:
    digest = credential_hash(credential)
    if digest is None:
        return None
    return db.scalar(select(AuthSession).where(AuthSession.secret_hash == digest, AuthSession.revoked_at.is_(None)))


def revoke_session(db: Session, credential: str) -> None:
    digest = credential_hash(credential)
    if digest is not None:
        db.execute(update(AuthSession).where(AuthSession.secret_hash == digest, AuthSession.revoked_at.is_(None)).values(revoked_at=datetime.now(timezone.utc)))
    db.commit()
