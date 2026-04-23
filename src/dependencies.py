from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.orm import Session as DBSession
from src.database import get_db
from src.auth import decode_token
from src.models import User, UserRole

# Security scheme for extracting Bearer tokens
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: DBSession = Depends(get_db),
) -> User:
    """
    Extract and validate the JWT from the Authorization header.
    Returns the authenticated User object.
    Raises 401 if token is missing, expired, or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
        )

    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token. Please log in again.",
        )

    # Reject monitoring-scoped tokens on regular endpoints
    if payload.get("token_type") == "monitoring":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Monitoring tokens cannot be used on regular endpoints.",
        )

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user


def get_monitoring_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: DBSession = Depends(get_db),
) -> User:
    """
    Extract and validate a monitoring-scoped JWT token.
    Only accepts tokens with token_type='monitoring' and role='monitoring_officer'.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid monitoring token.",
        )

    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Monitoring token has expired. Please request a new one.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid monitoring token.",
        )

    # Verify this is a monitoring-scoped token
    if payload.get("token_type") != "monitoring":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This endpoint requires a monitoring-scoped token. Use POST /auth/monitoring-token to obtain one.",
        )

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    # Dynamic Permission check even for monitoring tokens
    permissions = ROLE_PERMISSIONS.get(user.role, [])
    if "view_live_logs" not in permissions:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account lacks monitoring logs permission.",
        )

    return user



# ─── Dynamic RBAC Configuration ──────────────────────────────────────────────

ROLE_PERMISSIONS = {
    UserRole.student: ["mark_attendance", "join_batch", "view_self_stats"],
    UserRole.trainer: ["create_session", "manage_batch", "view_assigned_stats"],
    UserRole.institution: ["manage_institution_batches", "view_institution_summary"],
    UserRole.programme_manager: ["view_global_summary", "view_institution_summary"],
    UserRole.monitoring_officer: ["view_live_logs"]
}


class PermissionChecker:
    """
    Dynamic RBAC dependency. Checks if the current user's role has the required permission.
    Usage: Depends(PermissionChecker("create_session"))
    """

    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        permissions = ROLE_PERMISSIONS.get(user.role, [])
        if self.required_permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: '{self.required_permission}'. Your role '{user.role.value}' does not have this capability.",
            )
        return user


# Legacy support for specific role requirements
class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(r.value for r in self.allowed_roles)}.",
            )
        return user

