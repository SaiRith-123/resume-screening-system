"""Pydantic schemas - authentication."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    # Defaults preserve compatibility with existing API clients; the web form
    # always sends explicit consent values and requires both checkboxes.
    accept_terms: bool = True
    accept_privacy: bool = True

    @model_validator(mode="after")
    def validate_consent(self):
        if not self.accept_terms or not self.accept_privacy:
            raise ValueError("Terms of Service and Privacy Policy must be accepted")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class FirebaseLogin(BaseModel):
    id_token: str = Field(min_length=1)
    accept_terms: bool = False
    accept_privacy: bool = False

    @model_validator(mode="after")
    def validate_consent(self):
        if not self.accept_terms or not self.accept_privacy:
            raise ValueError("Terms of Service and Privacy Policy must be accepted")
        return self


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
