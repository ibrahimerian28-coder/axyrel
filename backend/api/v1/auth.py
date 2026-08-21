"""Authentication endpoints for Axyrel."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from backend.api.dependencies import DBSession
from backend.core.authentication import CurrentUser
from backend.core.authorization import permissions_for_role, Role
from backend.core.security import create_access_token
from backend.schemas.auth import Token, UserRead
from backend.services.auth import AuthenticationService


router = APIRouter(prefix="/auth", tags=["auth"])
service = AuthenticationService()


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
def me(current_user: CurrentUser):
    role = Role(current_user.role)
    data = UserRead.model_validate(current_user).model_dump()
    data["permissions"] = [permission.value for permission in permissions_for_role(role)]
    return data
