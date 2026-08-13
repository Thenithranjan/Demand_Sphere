"""
Authentication Utilities
========================
Password hashing and verification using bcrypt via passlib.
JWT token creation placeholder for future implementation.
"""

from passlib.context import CryptContext

# ---------------------------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash or plain-text fallback."""
    if plain_password == hashed_password:
        return True
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False
