"""Render job submission, progress polling, cancellation, and MP4 download endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.api.database import get_database
from backend.api.schemas import RenderJobStatus, RenderRequest
from backend.job_manager.queue import get_job_manager
from backend.rendering.renderer import RenderSourceError

router = APIRouter(prefix="/render", tags=["Rendering"])


@router.post("", response_model=RenderJobStatus, status_code=202)
async def submit_render(request: RenderRequest) -> RenderJobStatus:
    """Validate timeline media references and enqueue an async FFmpeg MP4 render."""
    try:
        return get_job_manager().submit(request)
    except RenderSourceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{job_id}", response_model=RenderJobStatus)
async def get_render_status(job_id: str) -> RenderJobStatus:
    """Return live progress and status for a render job."""
    job = get_database().get_render_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found.")
    return job


@router.post("/{job_id}/cancel", response_model=RenderJobStatus)
async def cancel_render(job_id: str) -> RenderJobStatus:
    """Cancel an in-flight or queued render job."""
    job = await get_job_manager().cancel(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found.")
    return job


@router.get("/{job_id}/download")
async def download_rendered_mp4(job_id: str) -> FileResponse:
    """Stream the rendered MP4 artifact for a completed job."""
    db = get_database()
    job = db.get_render_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found.")
    if job.status != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Render job is not completed (current status: {job.status}).",
        )

    output_path_str = db.get_render_output_path(job_id)
    if not output_path_str or not Path(output_path_str).is_file():
        raise HTTPException(status_code=404, detail="Rendered MP4 file missing on disk.")

    return FileResponse(
        path=output_path_str,
        media_type="video/mp4",
        filename=f"cineflow_{job.project_id}_{job.resolution}.mp4",
    )

