"""FastAPI dependencies for auth and RBAC."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.enums import UserRole
from app.core.security import safe_decode
from app.models import User

bearer = HTTPBearer(auto_error=False)


def get_current_user_optional(
    request: Request,
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> Optional[User]:
    # Bearer header preferred; query token supports browser ZIP/manifest downloads.
    raw = creds.credentials if creds else (
        request.query_params.get("access_token") or request.query_params.get("token")
    )
    if not raw:
        return None
    payload = safe_decode(raw)
    if not payload or payload.get("type") != "access":
        return None
    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active:
        return None
    return user


def get_current_user(
    user: Annotated[Optional[User], Depends(get_current_user_optional)],
) -> User:
    settings = get_settings()
    if user:
        return user
    if not settings.auth_required:
        # Dev bypass: return synthetic super admin when auth disabled
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required (set a valid Bearer token)",
        )
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def require_roles(*roles: UserRole):
    allowed = {r.value for r in roles}

    def _checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed and user.role != UserRole.SUPER_ADMIN.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return _checker


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]


def client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None
