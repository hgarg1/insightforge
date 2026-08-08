"""Authentication and password recovery routes."""

from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from insightforge.api.dependencies import CurrentUser, DbSession
from insightforge.api.schemas import (
    LoginRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserOut,
)
from insightforge.core.config import settings
from insightforge.core.models import PasswordResetToken, RefreshToken, User
from insightforge.core.security import (
    create_access_token,
    create_opaque_token,
    hash_password,
    hash_token,
    maybe_rehash_password,
    utc_now,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _aware(value):
    return value.replace(tzinfo=utc_now().tzinfo) if value.tzinfo is None else value


def _token_response(user: User, db, old_refresh: RefreshToken | None = None) -> TokenResponse:
    if old_refresh:
        old_refresh.revoked = True
    raw_refresh, refresh_hash = create_opaque_token()
    db.add(
        RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=utc_now() + timedelta(days=settings.refresh_token_days),
        )
    )
    db.commit()
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=raw_refresh,
        user=UserOut.model_validate(user),
    )


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: DbSession) -> TokenResponse:
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="An account already exists for this email"
        )
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="An account already exists for this email"
        ) from exc
    return _token_response(user, db)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect"
        )
    upgraded = maybe_rehash_password(payload.password, user.password_hash)
    if upgraded:
        user.password_hash = upgraded
        db.commit()
    return _token_response(user, db)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: DbSession) -> TokenResponse:
    token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(payload.refresh_token))
    )
    if token is None or token.revoked or _aware(token.expires_at) <= utc_now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid or expired"
        )
    user = db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is unavailable"
        )
    return _token_response(user, db, old_refresh=token)


@router.post("/logout", response_model=MessageResponse)
def logout(payload: RefreshRequest, db: DbSession) -> MessageResponse:
    token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(payload.refresh_token))
    )
    if token:
        token.revoked = True
        db.commit()
    return MessageResponse(message="You are securely signed out.")


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/password-reset/request", response_model=MessageResponse)
def request_password_reset(payload: PasswordResetRequest, db: DbSession) -> MessageResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    generic = "If an account matches that email, a reset link has been prepared."
    if user is None:
        return MessageResponse(message=generic)
    raw_token, token_hash = create_opaque_token()
    db.add(
        PasswordResetToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=utc_now() + timedelta(minutes=settings.reset_token_minutes),
        )
    )
    db.commit()
    if settings.environment == "development":
        print(f"[insightforge-mail-dev] password reset for {user.email}: {raw_token}")
        return MessageResponse(message=generic, development_token=raw_token)
    # A production mail adapter can consume this event without changing the API contract.
    return MessageResponse(message=generic)


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(payload: PasswordResetConfirm, db: DbSession) -> MessageResponse:
    token = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(payload.token))
    )
    if token is None or token.used or _aware(token.expires_at) <= utc_now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link is invalid or expired"
        )
    user = db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link is invalid or expired"
        )
    user.password_hash = hash_password(payload.password)
    token.used = True
    db.commit()
    return MessageResponse(message="Password updated. You can now sign in with your new password.")
