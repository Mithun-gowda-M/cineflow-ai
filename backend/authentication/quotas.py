"""Per-student storage quota calculation and upload capacity guardrails."""

from __future__ import annotations

from backend.api.database import get_database
from backend.api.schemas import QuotaStatusResponse, UserPublic
from backend.media_analysis.validator import MediaValidationError


def enforce_user_quota(user: UserPublic, incoming_bytes: int) -> None:
    """Reject uploads that would push a student account over its storage quota."""
    used = get_database().get_user_storage_bytes(user.id)
    if used + incoming_bytes > user.storage_quota_bytes:
        used_mb = used / (1024 * 1024)
        quota_mb = user.storage_quota_bytes / (1024 * 1024)
        raise MediaValidationError(
            f"Storage quota exceeded ({used_mb:.2f} MB used of {quota_mb:.2f} MB allocated).",
            status_code=413,
        )


def get_quota_status(user: UserPublic) -> QuotaStatusResponse:
    used = get_database().get_user_storage_bytes(user.id)
    quota = max(1, user.storage_quota_bytes)
    remaining = max(0, quota - used)
    pct = round(min(100.0, (used / float(quota)) * 100.0), 2)
    return QuotaStatusResponse(
        user_id=user.id,
        email=user.email,
        used_bytes=used,
        quota_bytes=quota,
        remaining_bytes=remaining,
        percent_used=pct,
    )

