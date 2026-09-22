"""User repository."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User


class UserRepository:
    @staticmethod
    def get(db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email.lower()))

    @staticmethod
    def create(db: Session, email: str, full_name: str, password: str, role: str = "recruiter") -> User:
        accepted_at = datetime.now(timezone.utc)
        user = User(
            email=email.lower(),
            full_name=full_name,
            hashed_password=hash_password(password),
            role=role,
            terms_accepted_at=accepted_at,
            privacy_accepted_at=accepted_at,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User | None:
        user = UserRepository.get_by_email(db, email)
        if user and verify_password(password, user.hashed_password):
            return user
        return None
