"""Salted scrypt password hashing, HS256 JWT tokens, and FastAPI RBAC dependencies."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.api.config import get_settings
from backend.api.database import get_database
from backend.api.schemas import UserPublic, UserRole

_BEARER_SCHEME = HTTPBearer(auto_error=False)


def hash_password(plain_password: str) -> str:
    """Hash a password using OWASP-recommended salted scrypt key derivation."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        plain_password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=32,
    )
    return f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored salted scrypt digest in constant time."""
    try:
        scheme, n_s, r_s, p_s, salt_hex, digest_hex = stored_hash.split("$")
        if scheme != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        derived = hashlib.scrypt(
            plain_password.encode("utf-8"),
            salt=salt,
            n=int(n_s),
            r=int(r_s),
            p=int(p_s),
            dklen=len(expected),
        )
        return hmac.compare_digest(derived, expected)
    except Exception:
        return False


def validate_college_domain(email: str) -> str:
    """Normalize email and enforce college domain policy when configured."""
    norm = email.strip().lower()
    if "@" not in norm or "." not in norm.split("@", 1)[1]:
        raise HTTPException(status_code=400, detail="Invalid email address format.")
    settings = get_settings()
    if settings.RESTRICT_COLLEGE_EMAIL_DOMAIN:
        allowed = {d.strip().lower() for d in settings.ALLOWED_AUTH_DOMAINS.split(",") if d.strip()}
        domain = norm.split("@", 1)[1]
        if domain not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Registration restricted to approved institutional domains ({', '.join(sorted(allowed))}).",
            )
    return norm


def create_access_token(user_id: str, email: str, role: str) -> tuple[str, int]:
    """Issue a signed HS256 JWT token and return `(token, expires_in_seconds)`."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_seconds = max(60, int(settings.JWT_EXPIRE_MINUTES) * 60)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_seconds)).timestamp()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_seconds


def decode_access_token(token: str) -> dict:
    """Decode and validate an HS256 JWT token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Session token has expired. Please log in again.") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token.") from exc


def row_to_user_public(row: dict) -> UserPublic:
    used = get_database().get_user_storage_bytes(row["id"])
    return UserPublic(
        id=row["id"],
        full_name=row["full_name"],
        email=row["email"],
        department=row["department"],
        role=row["role"],
        storage_quota_bytes=int(row["storage_quota_bytes"]),
        used_storage_bytes=used,
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
    )


def seed_default_institutional_accounts() -> None:
    """Idempotently seed baseline student and admin accounts for local/campus onboarding."""
    db = get_database()
    settings = get_settings()
    default_quota = int(settings.USER_STORAGE_QUOTA_GB * (1024**3))

    if not db.get_user_by_email("student.innovator@bmsit.in"):
        db.create_user(
            user_id="usr_student_demo",
            full_name="BMSIT Student Innovator",
            email="student.innovator@bmsit.in",
            department="Computer Science & Engineering",
            role="student",
            password_hash=hash_password("bmsit2026cineflow"),
            storage_quota_bytes=default_quota,
        )

    if not db.get_user_by_email("media.club@bmsit.in"):
        db.create_user(
            user_id="usr_admin_club",
            full_name="BMSIT Media Club Admin",
            email="media.club@bmsit.in",
            department="Media & Robotics Club",
            role="admin",
            password_hash=hash_password("bmsit2026admin"),
            storage_quota_bytes=default_quota * 2,
        )


def _resolve_user_from_credentials(creds: Optional[HTTPAuthorizationCredentials]) -> UserPublic:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Authentication credentials required.")
    payload = decode_access_token(creds.credentials)
    user_id = str(payload.get("sub", ""))
    row = get_database().get_user_by_id(user_id)
    if not row:
        raise HTTPException(status_code=401, detail="Authenticated user account no longer exists.")
    if not bool(row["is_active"]):
        raise HTTPException(status_code=403, detail="Account has been suspended by campus administrator.")
    return row_to_user_public(row)


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_BEARER_SCHEME),
) -> UserPublic:
    """Strictly require a valid, active JWT-authenticated user."""
    return _resolve_user_from_credentials(creds)


def get_optional_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_BEARER_SCHEME),
) -> Optional[UserPublic]:
    """Authenticate Bearer tokens when supplied, enforcing auth only when campus lock is enabled."""
    if creds is not None and creds.credentials:
        return _resolve_user_from_credentials(creds)
    if get_settings().REQUIRE_AUTH_FOR_MEDIA:
        raise HTTPException(status_code=401, detail="Institutional sign-in required for workspace actions.")
    return None


def require_admin_user(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    """Restrict administrative endpoints strictly to club_lead or admin roles."""
    allowed_roles: set[UserRole] = {"admin", "club_lead"}
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: institutional club_lead or admin role required.",
        )
    return current_user

