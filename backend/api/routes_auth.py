"""Institutional student registration, JWT login, profile, and quota endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from backend.api.config import get_settings
from backend.api.database import get_database
from backend.api.schemas import (
    AuthTokenResponse,
    LoginRequest,
    QuotaStatusResponse,
    RegisterRequest,
    UserPublic,
)
from backend.authentication.quotas import get_quota_status
from backend.authentication.security import (
    create_access_token,
    get_current_user,
    hash_password,
    row_to_user_public,
    seed_default_institutional_accounts,
    validate_college_domain,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Quotas"])


@router.post("/register", response_model=AuthTokenResponse, status_code=201)
def register_student(payload: RegisterRequest) -> AuthTokenResponse:
    """Register a new student or club member account and issue a signed JWT token."""
    seed_default_institutional_accounts()
    db = get_database()
    clean_email = validate_college_domain(payload.email)
    if db.get_user_by_email(clean_email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    # Never allow self-escalation directly to global 'admin' via public signup
    safe_role = "club_lead" if payload.role == "club_lead" else "student"
    quota_bytes = int(get_settings().USER_STORAGE_QUOTA_GB * (1024**3))
    user_row = db.create_user(
        user_id=f"usr_{uuid.uuid4().hex[:10]}",
        full_name=payload.full_name,
        email=clean_email,
        department=payload.department,
        role=safe_role,
        password_hash=hash_password(payload.password),
        storage_quota_bytes=quota_bytes,
    )
    user = row_to_user_public(user_row)
    token, expires_in = create_access_token(user.id, user.email, user.role)
    return AuthTokenResponse(
        access_token=token,
        expires_in_seconds=expires_in,
        user=user,
    )


@router.post("/login", response_model=AuthTokenResponse)
def login_user(payload: LoginRequest) -> AuthTokenResponse:
    """Authenticate an institutional email & password and issue a Bearer JWT."""
    seed_default_institutional_accounts()
    db = get_database()
    row = db.get_user_by_email(payload.email)
    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not bool(row["is_active"]):
        raise HTTPException(status_code=403, detail="Account suspended. Contact BMSIT club administrator.")

    user = row_to_user_public(row)
    token, expires_in = create_access_token(user.id, user.email, user.role)
    return AuthTokenResponse(
        access_token=token,
        expires_in_seconds=expires_in,
        user=user,
    )


@router.get("/me", response_model=UserPublic)
def get_authenticated_profile(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    """Return active authenticated student/admin identity and live storage utilization."""
    return current_user


@router.get("/quota", response_model=QuotaStatusResponse)
def get_authenticated_quota(current_user: UserPublic = Depends(get_current_user)) -> QuotaStatusResponse:
    """Return live storage usage and remaining quota bytes for the authenticated student."""
    return get_quota_status(current_user)

