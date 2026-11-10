"""Institutional Campus Admin Diagnostics, Student Quota Controls, Cleanup & Migration APIs."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from backend.api.config import get_settings
from backend.api.database import get_database
from backend.api.schemas import (
    AdminOverviewResponse,
    AdminUserRecord,
    AdminUserUpdateRequest,
    CleanupRequest,
    CleanupResponse,
    MigrationStatusResponse,
    UserPublic,
)
from backend.authentication.security import require_admin_user, seed_default_institutional_accounts
from backend.rendering.cleanup import (
    collect_system_telemetry,
    compute_directory_sizes,
    purge_storage_caches,
)

router = APIRouter(prefix="/admin", tags=["Institutional Admin"])


@router.get("/overview", response_model=AdminOverviewResponse)
def get_admin_overview(_admin: UserPublic = Depends(require_admin_user)) -> AdminOverviewResponse:
    """Return live CPU/RAM/disk telemetry, directory storage audit, and render queue stats."""
    seed_default_institutional_accounts()
    db = get_database()
    settings = get_settings()
    users = db.list_users_with_usage()
    engine = "postgresql" if settings.DATABASE_URL.lower().startswith("postgres") else "sqlite"

    return AdminOverviewResponse(
        system=collect_system_telemetry(),
        storage=compute_directory_sizes(),
        active_users_count=sum(1 for u in users if u.is_active),
        total_users_count=len(users),
        total_projects_count=len(db.list_projects()),
        total_media_assets_count=len(db.list_media_assets()),
        render_queue=db.get_render_queue_counts(),
        database_engine=engine,
    )


@router.get("/users", response_model=list[AdminUserRecord])
def list_institutional_users(_admin: UserPublic = Depends(require_admin_user)) -> list[AdminUserRecord]:
    """List registered student & club admin accounts with storage usage and project counts."""
    seed_default_institutional_accounts()
    return get_database().list_users_with_usage()


@router.patch("/users/{user_id}", response_model=AdminUserRecord)
def update_institutional_user(
    user_id: str,
    payload: AdminUserUpdateRequest,
    admin_user: UserPublic = Depends(require_admin_user),
) -> AdminUserRecord:
    """Update a student's quota allocation, role, or activation status."""
    seed_default_institutional_accounts()
    if user_id == admin_user.id and payload.is_active is False:
        raise HTTPException(status_code=400, detail="Administrators cannot suspend their own active account.")
    if user_id == admin_user.id and payload.role == "student":
        raise HTTPException(status_code=400, detail="Administrators cannot demote their own active role.")

    quota_bytes = payload.storage_quota_bytes
    if quota_bytes is None and payload.storage_quota_gb is not None:
        quota_bytes = int(payload.storage_quota_gb * (1024**3))

    updated = get_database().update_user_admin(
        user_id,
        storage_quota_bytes=quota_bytes,
        role=payload.role,
        is_active=payload.is_active,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User account not found.")
    return updated


@router.post("/cleanup", response_model=CleanupResponse)
def trigger_storage_cleanup(
    payload: CleanupRequest,
    _admin: UserPublic = Depends(require_admin_user),
) -> CleanupResponse:
    """Purge expired proxy/segment caches and stale MP4 render outputs safely."""
    return purge_storage_caches(
        purge_cache=payload.purge_cache,
        purge_expired_renders=payload.purge_expired_renders,
        max_age_hours=payload.max_age_hours,
    )


@router.get("/migration-status", response_model=MigrationStatusResponse)
def get_migration_status(_admin: UserPublic = Depends(require_admin_user)) -> MigrationStatusResponse:
    """Report SQLite/PostgreSQL schema parity, table row counts, and migration CLI readiness."""
    settings = get_settings()
    ddl_path = Path(settings.BASE_DIR) / "backend" / "migrations" / "001_postgres_initial.sql"
    engine = "postgresql" if settings.DATABASE_URL.lower().startswith("postgres") else "sqlite"
    return MigrationStatusResponse(
        active_engine=engine,
        configured_database_url=settings.DATABASE_URL,
        schema_version="001_campus_v1",
        postgres_ddl_ready=ddl_path.is_file(),
        table_counts=get_database().get_schema_table_counts(),
    )

