"""Security placeholders for future auth (password hashing, JWT)."""

from app.core.enums import UserRole


def hash_password(password: str) -> str:
    # Placeholder — replace with passlib/bcrypt before any real auth.
    return f"hashed:{password}"


def verify_password(password: str, password_hash: str) -> bool:
    return password_hash == f"hashed:{password}"


DEFAULT_ROLE = UserRole.VIEWER
