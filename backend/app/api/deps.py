"""FastAPI dependencies (auth, db)."""
from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AuthError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    auth_cookie: str | None = Cookie(default=None, alias="rss_session"),
    db: Session = Depends(get_db),
) -> User:
    token = token or auth_cookie
    if not token:
        raise AuthError("Not authenticated")
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise AuthError("Invalid or expired token")
    user = UserRepository.get(db, int(payload["sub"]))
    if user is None or not user.is_active:
        raise AuthError("User not found or inactive")
    return user
