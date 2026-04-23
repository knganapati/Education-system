from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from src.database import get_db
from src.models import User, UserRole
from src.schemas import (
    SignupRequest, LoginRequest, MonitoringTokenRequest, 
    AuthResponse, TokenResponse, UserResponse
)
from src.auth import hash_password, verify_password, create_access_token, create_monitoring_token
from src.dependencies import get_current_user
from src.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: DBSession = Depends(get_db)):
    """Register a new user. Returns a JWT on success."""
    # Check for existing email
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A user with this email already exists.",
        )

    # Validate institution_id if provided
    if payload.institution_id is not None:
        institution = db.query(User).filter(
            User.id == payload.institution_id,
            User.role == UserRole.institution,
        ).first()
        if not institution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Institution with id {payload.institution_id} not found.",
            )

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        institution_id=payload.institution_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, role=user.role.value)
    return AuthResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: DBSession = Depends(get_db)):
    """Authenticate a user. Returns a signed JWT on success."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user_id=user.id, role=user.role.value)
    return AuthResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/monitoring-token", response_model=TokenResponse)
def get_monitoring_token(
    payload: MonitoringTokenRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Exchange a valid Monitoring Officer JWT + API key for a short-lived
    monitoring-scoped token (1 hour expiry).
    """
    if current_user.role != UserRole.monitoring_officer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only monitoring officers can obtain a monitoring token.",
        )

    if payload.key != settings.MONITORING_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    monitoring_token = create_monitoring_token(user_id=current_user.id)
    return TokenResponse(
        access_token=monitoring_token,
        token_type="bearer",
        expires_in_seconds=settings.MONITORING_TOKEN_EXPIRE_HOURS * 3600,
    )
