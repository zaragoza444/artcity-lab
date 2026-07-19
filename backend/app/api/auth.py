from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

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


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: str = Field(..., min_length=3)
    full_name: str
    password: str = Field(..., min_length=8)
    role: str = UserRole.VIEWER.value


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    write_audit(
        db,
        action="login",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        ip_address=client_ip(request),
    )
    db.commit()
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
        role=user.role,
        email=user.email,
        full_name=user.full_name,
        user_id=user.id,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    data = safe_decode(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.get(User, data.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid user")
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
        role=user.role,
        email=user.email,
        full_name=user.full_name,
        user_id=user.id,
    )


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
    created = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(created)
    write_audit(
        db,
        action="create_user",
        resource_type="user",
        resource_id=None,
        user_id=user.id,
        detail={"email": payload.email, "role": payload.role},
        ip_address=client_ip(request),
    )
    db.commit()
    db.refresh(created)
    return created
