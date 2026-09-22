"""Auth endpoints (spec §20, §22). Rate-limited against brute force."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone

import firebase_admin
from fastapi import APIRouter, Depends, Response, status
from firebase_admin import auth as firebase_auth
from firebase_admin import exceptions as firebase_exceptions
from sqlalchemy.orm import Session

from app.core.errors import AuthError, ValidationAppError
from app.core.config import settings
from app.core.ratelimit import rate_limit
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import FirebaseLogin, Token, UserLogin, UserOut, UserRegister
from app.schemas.common import MessageOut
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _verify_firebase_token(id_token: str) -> dict:
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            options = {"projectId": settings.FIREBASE_PROJECT_ID} if settings.FIREBASE_PROJECT_ID else None
            firebase_admin.initialize_app(options=options)
        except (ValueError, firebase_exceptions.FirebaseError) as exc:
            raise AuthError("Firebase sign-in is not configured on the server") from exc
    try:
        return firebase_auth.verify_id_token(id_token)
    except (ValueError, firebase_exceptions.FirebaseError) as exc:
        raise AuthError("The Firebase sign-in could not be verified") from exc


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(rate_limit("auth"))])
def register(payload: UserRegister, response: Response, db: Session = Depends(get_db)) -> Token:
    if UserRepository.get_by_email(db, payload.email):
        raise ValidationAppError("Email already registered")
    user = UserRepository.create(db, payload.email, payload.full_name, payload.password)
    token = create_access_token(user.id)
    result = Token(access_token=token, user=UserOut.model_validate(user))
    _set_session_cookie(response, token)
    return result


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit("auth"))])
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)) -> Token:
    user = UserRepository.authenticate(db, payload.email, payload.password)
    if user is None:
        raise AuthError("Invalid email or password")
    token = create_access_token(user.id)
    result = Token(access_token=token, user=UserOut.model_validate(user))
    _set_session_cookie(response, token)
    return result


@router.post("/firebase", response_model=Token, dependencies=[Depends(rate_limit("auth"))])
def firebase_login(payload: FirebaseLogin, response: Response, db: Session = Depends(get_db)) -> Token:
    """Exchange a verified Firebase identity for the app's normal JWT."""
    decoded = _verify_firebase_token(payload.id_token)

    email = str(decoded.get("email", "")).strip().lower()
    if not email or decoded.get("email_verified") is not True:
        raise AuthError("A verified email address is required")

    user = UserRepository.get_by_email(db, email)
    if user is None:
        display_name = str(decoded.get("name") or email.split("@", 1)[0])[:255]
        user = User(
            email=email,
            full_name=display_name,
            # Firebase owns credential verification; this is never used for
            # Firebase sign-in and only satisfies the local schema.
            hashed_password=secrets.token_urlsafe(32),
            terms_accepted_at=datetime.now(timezone.utc),
            privacy_accepted_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not user.is_active:
        raise AuthError("User not found or inactive")

    token = create_access_token(user.id)
    result = Token(access_token=token, user=UserOut.model_validate(user))
    _set_session_cookie(response, token)
    return result


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        "rss_session", token, httponly=True, secure=settings.is_production,
        samesite="lax", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/",
    )


@router.post("/logout", response_model=MessageOut)
def logout(response: Response) -> MessageOut:
    response.delete_cookie("rss_session", path="/")
    return MessageOut(message="Signed out")


@router.post("/data-deletion-request", response_model=MessageOut)
def data_deletion_request(db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)) -> MessageOut:
    db.delete(user)
    db.commit()
    return MessageOut(message="Your account and associated data were deleted.")
