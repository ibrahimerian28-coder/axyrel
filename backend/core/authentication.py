"""Database-backed authentication dependencies for Axyrel."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import decode_access_token, oauth2_scheme
from backend.models.user import User
from backend.services.auth import AuthenticationService


AuthenticationDBSession = Annotated[Session, Depends(get_db)]
_authentication_service = AuthenticationService()


def get_current_user(
    db: AuthenticationDBSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    try:
        claims = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = claims.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has no subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(str(subject))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has an invalid subject",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = _authentication_service.get_active_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive, company is inactive, or user no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
