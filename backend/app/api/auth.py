from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import CurrentUser, client_ip
from app.core.enums import UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    safe_decode,
    verify_password,
)
from app.models import User
from app.services.audit import write_audit

router = APIRouter(prefix="/api/auth", tags=["auth"])

_PHONE_RE = re.compile(r"^\+?[0-9]{8,15}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_phone(raw: str) -> str:
    cleaned = re.sub(r"[\s\-()]", "", (raw or "").strip())
    if not _PHONE_RE.match(cleaned):
        raise ValueError("Phone must be 8–15 digits, optional leading +")
    return cleaned


def _normalize_email(raw: str) -> str:
    email = (raw or "").strip().lower()
    if not _EMAIL_RE.match(email):
        raise ValueError("Invalid email address")
    return email


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)

    @field_validator("email", "password", mode="before")
    @classmethod
    def strip_creds(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    email: str
    full_name: str
    user_id: str
    phone_number: Optional[str] = None
    email_verified: bool = False
    phone_verified: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    phone_number: Optional[str] = None
    email_verified_at: Optional[datetime] = None
    phone_verified_at: Optional[datetime] = None
    account_state: Optional[str] = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: str = Field(..., min_length=3)
    full_name: str
    password: str = Field(..., min_length=8)
    role: str = UserRole.VIEWER.value
    phone_number: Optional[str] = None


class SignupRequest(BaseModel):
    email: str = Field(..., min_length=3)
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    phone_number: str = Field(..., min_length=8, max_length=32)
    accept_terms: bool = False

    @field_validator("email", mode="before")
    @classmethod
    def email_ok(cls, v: object) -> object:
        if isinstance(v, str):
            return _normalize_email(v)
        return v

    @field_validator("phone_number", mode="before")
    @classmethod
    def phone_ok(cls, v: object) -> object:
        if isinstance(v, str):
            return _normalize_phone(v)
        return v

    @field_validator("full_name", mode="before")
    @classmethod
    def name_ok(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


class SignupResponse(BaseModel):
    user_id: str
    email: str
    phone_number: str
    full_name: str
    account_state: str
    message: str
    email_token: Optional[str] = None
    phone_code: Optional[str] = None
    verify_email_path: str = "/api/auth/verify-email"
    verify_phone_path: str = "/api/auth/verify-phone"


class VerifyEmailRequest(BaseModel):
    email: str
    token: str

    @field_validator("email", mode="before")
    @classmethod
    def email_ok(cls, v: object) -> object:
        if isinstance(v, str):
            return _normalize_email(v)
        return v


class VerifyPhoneRequest(BaseModel):
    email: str
    code: str

    @field_validator("email", mode="before")
    @classmethod
    def email_ok(cls, v: object) -> object:
        if isinstance(v, str):
            return _normalize_email(v)
        return v


class VerifyStatusOut(BaseModel):
    email: str
    email_verified: bool
    phone_verified: bool
    account_state: str
    can_login: bool


def _issue_tokens(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
        role=user.role,
        email=user.email,
        full_name=user.full_name,
        user_id=user.id,
        phone_number=user.phone_number,
        email_verified=bool(user.email_verified_at),
        phone_verified=bool(user.phone_verified_at),
    )


def _customer_can_login(user: User) -> bool:
    settings = get_settings()
    if user.email == settings.default_admin_email.lower():
        return True
    if user.role in {UserRole.SUPER_ADMIN.value, UserRole.ADMINISTRATOR.value}:
        return True
    if settings.signup_require_email_verify and not user.email_verified_at:
        return False
    if settings.signup_require_phone_verify and settings.signup_require_phone and not user.phone_verified_at:
        return False
    return True


def _authenticate(db: Session, email: str, password: str) -> User:
    settings = get_settings()
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        if user.email == settings.default_admin_email.lower():
            user.is_active = True
            db.add(user)
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    if not _customer_can_login(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verify email and phone before signing in",
        )
    return user


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, request: Request, db: Session = Depends(get_db)) -> SignupResponse:
    settings = get_settings()
    if not payload.accept_terms:
        raise HTTPException(status_code=400, detail="accept_terms must be true")
    if settings.signup_require_phone and not payload.phone_number:
        raise HTTPException(status_code=400, detail="phone_number is required")

    email = payload.email
    phone = payload.phone_number
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if phone and db.query(User).filter(User.phone_number == phone).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    email_token = secrets.token_urlsafe(24)
    phone_code = f"{secrets.randbelow(1_000_000):06d}"
    now = datetime.now(timezone.utc)

    user = User(
        id=str(uuid4()),
        email=email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=UserRole.EDITOR.value,
        is_active=True,
        phone_number=phone,
        email_verify_token=email_token,
        phone_verify_code=phone_code,
        account_state="registered_unverified",
        email_verified_at=None if settings.signup_require_email_verify else now,
        phone_verified_at=None if settings.signup_require_phone_verify else now,
    )
    if not settings.signup_require_email_verify and not settings.signup_require_phone_verify:
        user.account_state = "active"

    db.add(user)
    db.flush()  # persist user before audit_logs FK to users.id
    write_audit(
        db,
        action="customer_signup",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        detail={"email": email, "phone": phone},
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(user)

    return SignupResponse(
        user_id=user.id,
        email=user.email,
        phone_number=user.phone_number or "",
        full_name=user.full_name,
        account_state=user.account_state,
        message="Account created. Verify email and phone to activate production access.",
        email_token=email_token if settings.signup_expose_codes else None,
        phone_code=phone_code if settings.signup_expose_codes else None,
    )


@router.post("/verify-email", response_model=VerifyStatusOut)
def verify_email(payload: VerifyEmailRequest, request: Request, db: Session = Depends(get_db)) -> VerifyStatusOut:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.email_verify_token or user.email_verify_token != payload.token.strip():
        raise HTTPException(status_code=400, detail="Invalid email verification token")
    user.email_verified_at = datetime.now(timezone.utc)
    user.email_verify_token = None
    if user.phone_verified_at or not get_settings().signup_require_phone_verify:
        user.account_state = "active"
    else:
        user.account_state = "pending_phone_verification"
    db.add(user)
    write_audit(
        db,
        action="verify_email",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        ip_address=client_ip(request),
    )
    db.commit()
    return VerifyStatusOut(
        email=user.email,
        email_verified=True,
        phone_verified=bool(user.phone_verified_at),
        account_state=user.account_state,
        can_login=_customer_can_login(user),
    )


@router.post("/verify-phone", response_model=VerifyStatusOut)
def verify_phone(payload: VerifyPhoneRequest, request: Request, db: Session = Depends(get_db)) -> VerifyStatusOut:
    user = db.query(User).filter(User.email == payload.email).first()
    code = payload.code.strip()
    if not user or not user.phone_verify_code or user.phone_verify_code != code:
        raise HTTPException(status_code=400, detail="Invalid phone verification code")
    user.phone_verified_at = datetime.now(timezone.utc)
    user.phone_verify_code = None
    if user.email_verified_at or not get_settings().signup_require_email_verify:
        user.account_state = "active"
    else:
        user.account_state = "pending_email_verification"
    db.add(user)
    write_audit(
        db,
        action="verify_phone",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        ip_address=client_ip(request),
    )
    db.commit()
    return VerifyStatusOut(
        email=user.email,
        email_verified=bool(user.email_verified_at),
        phone_verified=True,
        account_state=user.account_state,
        can_login=_customer_can_login(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user = _authenticate(db, payload.email, payload.password)
    write_audit(
        db,
        action="login",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        ip_address=client_ip(request),
    )
    db.commit()
    return _issue_tokens(user)


@router.post("/token")
def token(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """OAuth2 password flow for Swagger Authorize (username = email)."""
    user = _authenticate(db, form.username, form.password)
    write_audit(
        db,
        action="login",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        detail={"via": "oauth2_token"},
        ip_address=client_ip(request),
    )
    db.commit()
    issued = _issue_tokens(user)
    return {"access_token": issued.access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    data = safe_decode(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.get(User, data.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid user")
    if not _customer_can_login(user):
        raise HTTPException(status_code=403, detail="Verify email and phone before signing in")
    return _issue_tokens(user)


class UserActiveUpdate(BaseModel):
    is_active: bool = True


@router.patch("/users/{user_id}/active", response_model=UserOut)
def set_user_active(
    user_id: str,
    payload: UserActiveUpdate,
    actor: CurrentUser,
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    if actor.role not in {UserRole.SUPER_ADMIN.value, UserRole.ADMINISTRATOR.value}:
        raise HTTPException(status_code=403, detail="Admin only")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.is_active = payload.is_active
    db.add(target)
    write_audit(
        db,
        action="set_user_active",
        resource_type="user",
        resource_id=target.id,
        user_id=actor.id,
        detail={"is_active": payload.is_active, "email": target.email},
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(target)
    return target


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(user: CurrentUser, db: Session = Depends(get_db)) -> list[User]:
    if user.role not in {UserRole.SUPER_ADMIN.value, UserRole.ADMINISTRATOR.value}:
        raise HTTPException(status_code=403, detail="Admin only")
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, user: CurrentUser, request: Request, db: Session = Depends(get_db)) -> User:
    if user.role not in {UserRole.SUPER_ADMIN.value, UserRole.ADMINISTRATOR.value}:
        raise HTTPException(status_code=403, detail="Admin only")
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    phone = None
    if payload.phone_number:
        try:
            phone = _normalize_phone(payload.phone_number)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if db.query(User).filter(User.phone_number == phone).first():
            raise HTTPException(status_code=400, detail="Phone number already registered")
    now = datetime.now(timezone.utc)
    created = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
        phone_number=phone,
        email_verified_at=now,
        phone_verified_at=now if phone else None,
        account_state="active",
    )
    db.add(created)
    write_audit(
        db,
        action="create_user",
        resource_type="user",
        resource_id=None,
        user_id=user.id,
        detail={"email": payload.email, "role": payload.role, "phone": phone},
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(created)
    return created
