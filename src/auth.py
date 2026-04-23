from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from src.config import settings

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(user_id: int, role: str, expires_hours: int = None) -> str:
    """
    Create a standard JWT access token.
    
    Payload structure:
    {
        "user_id": int,
        "role": str,
        "token_type": "access",
        "iat": int (Unix timestamp),
        "exp": int (Unix timestamp)
    }
    """
    if expires_hours is None:
        expires_hours = settings.ACCESS_TOKEN_EXPIRE_HOURS

    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "role": role,
        "token_type": "access",
        "iat": now,
        "exp": now + timedelta(hours=expires_hours),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_monitoring_token(user_id: int) -> str:
    """
    Create a short-lived monitoring-scoped JWT token.
    
    Payload structure:
    {
        "user_id": int,
        "role": "monitoring_officer",
        "token_type": "monitoring",
        "scope": "read:monitoring",
        "iat": int (Unix timestamp),
        "exp": int (Unix timestamp, 1 hour from now)
    }
    """
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "role": "monitoring_officer",
        "token_type": "monitoring",
        "scope": "read:monitoring",
        "iat": now,
        "exp": now + timedelta(hours=settings.MONITORING_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises jwt.ExpiredSignatureError if expired.
    Raises jwt.InvalidTokenError for any other issue.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
