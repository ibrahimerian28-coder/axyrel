"""Authentication security primitives for Axyrel.

Task 21 establishes password hashing and JWT token foundations.
User lookup, authorization, and tenant context are intentionally deferred
until their dedicated tasks.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.security import OAuth2PasswordBearer

from .config import settings

ALGORITHM = "HS256"
PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000
SALT_BYTES = 16

# Login endpoint will be introduced with the authentication API layer.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


def hash_password(password: str) -> str:
    """Return a salted PBKDF2 password hash suitable for database storage."""
    salt = os.urandom(SALT_BYTES)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    key_text = base64.urlsafe_b64encode(derived_key).decode("ascii").rstrip("=")
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt_text}${key_text}"


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify a plain password against a stored Axyrel password hash."""
    try:
        scheme, iterations_text, salt_text, key_text = encoded_hash.split("$", 3)
        if scheme != PASSWORD_SCHEME:
            return False
        iterations = int(iterations_text)
        salt = base64.urlsafe_b64decode(salt_text + "==")
        expected_key = base64.urlsafe_b64decode(key_text + "==")
    except (TypeError, ValueError):
        return False

    actual_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_key, expected_key)


def create_access_token(
    subject: str,
    *,
    expires_minutes: int | None = None,
    role: str | None = None,
    permissions: list[str] | None = None,
) -> str:
    """Create a signed JWT access token with optional authorization claims."""
    lifetime = expires_minutes or settings.access_token_expire_minutes
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=lifetime)
    payload: dict[str, object] = {"sub": subject, "exp": expires_at}
    if role is not None:
        payload["role"] = role
    if permissions is not None:
        payload["permissions"] = permissions
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, object]:
    """Decode and validate an Axyrel access token."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
