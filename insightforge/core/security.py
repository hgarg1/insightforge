"""Password hashing, JWT access tokens, and opaque token helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from insightforge.core.config import settings

password_hasher = PasswordHasher()
ALGORITHM = "HS256"
PASSWORD_REQUIREMENTS = (
    ("length", "12 or more characters"),
    ("uppercase", "an uppercase letter"),
    ("lowercase", "a lowercase letter"),
    ("number", "a number"),
    ("symbol", "a symbol"),
)


def password_requirement_status(password: str) -> dict[str, bool]:
    """Return each password-policy check for UI feedback and API validation."""

    return {
        "length": len(password) >= 12,
        "uppercase": any(character.isupper() for character in password),
        "lowercase": any(character.islower() for character in password),
        "number": any(character.isdigit() for character in password),
        "symbol": any(not character.isalnum() and not character.isspace() for character in password),
    }


def password_requirements(password: str) -> tuple[str, ...]:
    checks = password_requirement_status(password)
    return tuple(label for key, label in PASSWORD_REQUIREMENTS if not checks[key])


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    try:
        return password_hasher.verify(encoded, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


def maybe_rehash_password(password: str, encoded: str) -> str | None:
    try:
        return (
            password_hasher.hash(password) if password_hasher.check_needs_rehash(encoded) else None
        )
    except (InvalidHashError, VerificationError):
        return None


def create_access_token(user_id: str) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    if payload.get("type") != "access" or not payload.get("sub"):
        raise jwt.InvalidTokenError("Invalid access token")
    return payload


def create_opaque_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(48)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(UTC)
