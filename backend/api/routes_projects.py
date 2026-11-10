"""Project creation, persistence, and timeline state CRUD endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from backend.api.config import utc_now_iso
from backend.api.database import get_database
from backend.api.schemas import (
    ProjectCreate,
    ProjectHistoryResponse,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(payload: ProjectCreate) -> ProjectResponse:
    now = utc_now_iso()
    project = ProjectResponse(
        id=f"proj_{uuid.uuid4().hex[:10]}",
        title=payload.title.strip(),
        description=payload.description,
        aspect_ratio=payload.aspect_ratio,
        target_duration_seconds=payload.target_duration_seconds,
        color_grade=payload.color_grade,
        timeline=None,
        created_at=now,
        updated_at=now,
    )
    return get_database().save_project(project)


@router.get("", response_model=list[ProjectResponse])
def list_projects() -> list[ProjectResponse]:
    return get_database().list_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str) -> ProjectResponse:
    proj = get_database().get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    return proj


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, payload: ProjectUpdate) -> ProjectResponse:
    db = get_database()
    existing = db.get_project(project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found.")

    updated = existing.model_copy(
        update={
            "title": payload.title.strip() if payload.title is not None else existing.title,
            "description": payload.description if payload.description is not None else existing.description,
            "aspect_ratio": payload.aspect_ratio if payload.aspect_ratio is not None else existing.aspect_ratio,
            "target_duration_seconds": (
                payload.target_duration_seconds
                if payload.target_duration_seconds is not None
                else existing.target_duration_seconds
            ),
            "color_grade": payload.color_grade if payload.color_grade is not None else existing.color_grade,
            "timeline": payload.timeline if payload.timeline is not None else existing.timeline,
            "updated_at": utc_now_iso(),
        }
    )
    return db.save_project(updated)


@router.delete("/{project_id}")
def delete_project(project_id: str) -> dict[str, str]:
    deleted = get_database().delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"status": "deleted", "id": project_id}


@router.get("/{project_id}/history", response_model=ProjectHistoryResponse)
def get_project_revision_history(project_id: str) -> ProjectHistoryResponse:
    """Return persistent timeline revisions and Undo/Redo state for a project."""
    return get_database().get_project_history(project_id)


@router.post("/{project_id}/undo", response_model=ProjectHistoryResponse)
def undo_project_timeline(project_id: str) -> ProjectHistoryResponse:
    """Step backwards one timeline revision in persistent SQLite history."""
    return get_database().step_project_revision(project_id, -1)


@router.post("/{project_id}/redo", response_model=ProjectHistoryResponse)
def redo_project_timeline(project_id: str) -> ProjectHistoryResponse:
    """Step forward one timeline revision in persistent SQLite history."""
    return get_database().step_project_revision(project_id, 1)

