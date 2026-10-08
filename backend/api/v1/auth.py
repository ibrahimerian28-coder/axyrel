"""Authentication endpoints for Axyrel."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from backend.api.dependencies import DBSession
from backend.core.authentication import CurrentAuthContext
from backend.core.authorization import permissions_for_role, Role
from backend.core.security import create_access_token
from backend.schemas.auth import Token, UserRead
from backend.services.auth import AuthenticationService
from backend.services.auth_sessions import issue_session, revoke_session
from backend.core.security import oauth2_scheme
from uuid import UUID
from datetime import datetime, timezone
from backend.models.auth_session import AuthSession
from sqlalchemy import update


router = APIRouter(prefix="/auth", tags=["auth"])
service = AuthenticationService()


@router.post("/sessions", response_model=Token)
def browser_login(db: DBSession, form_data: OAuth2PasswordRequestForm = Depends()):
    user = service.authenticate(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    Role(user.role)
    credential = issue_session(db, user)
    service.record_login(user)
    db.commit()
    return Token(access_token=credential)


@router.post("/sessions/logout", status_code=204)
def browser_logout(db: DBSession, token: str = Depends(oauth2_scheme)):
    # Idempotent, including already-revoked or disabled accounts. JWTs are untouched.
    revoke_session(db, token)


@router.delete("/sessions/{session_id}", status_code=204)
def security_revoke(session_id: UUID, db: DBSession, context: CurrentAuthContext):
    if context.user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator permission required")
    # Scope the update to the authenticated tenant; never disclose foreign sessions.
    db.execute(update(AuthSession).where(AuthSession.id == session_id, AuthSession.company_id == context.company_id, AuthSession.revoked_at.is_(None)).values(revoked_at=datetime.now(timezone.utc)))
    db.commit()


@router.post("/login", response_model=Token)
def login(db: DBSession, form_data: OAuth2PasswordRequestForm = Depends()):
    user = service.authenticate(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        role = Role(user.role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User has an invalid application role",
        ) from exc

    service.record_login(user)
    db.commit()

    token = create_access_token(
        str(user.id),
        role=role.value,
        permissions=[permission.value for permission in permissions_for_role(role)],
    )
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
def me(context: CurrentAuthContext):
    current_user = context.user
    role = Role(current_user.role)
    data = UserRead.model_validate(current_user).model_dump()
    data["permissions"] = [permission.value for permission in permissions_for_role(role)]
    return data
