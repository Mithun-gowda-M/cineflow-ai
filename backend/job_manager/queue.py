"""Async render job manager with concurrency throttling, progress updates, and cancellation."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Optional

from backend.api.config import get_settings, utc_now_iso
from backend.api.database import get_database
from backend.api.schemas import RenderJobStatus, RenderRequest
from backend.rendering.renderer import execute_render_job, resolve_timeline_sources
from backend.video_engine.hardware import detect_hardware_profile


class RenderJobManager:
    """Manages asynchronous FFmpeg render tasks and tracks live subprocesses."""

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._processes: dict[str, dict] = {}
        self._cancelled: set[str] = set()
        self._semaphore: Optional[asyncio.Semaphore] = None

    def _get_semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            limit = max(1, detect_hardware_profile().max_concurrent_renders)
            self._semaphore = asyncio.Semaphore(limit)
        return self._semaphore

    def submit(self, request: RenderRequest) -> RenderJobStatus:
        """Validate referenced sources upfront and enqueue background FFmpeg render."""
        # Fail fast with validation error if referenced media assets do not exist
        resolve_timeline_sources(request)

        db = get_database()
        now = utc_now_iso()
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = RenderJobStatus(
            job_id=job_id,
            project_id=request.timeline.project_id,
            status="queued",
            progress_percent=0.0,
            current_step="Queued for rendering...",
            resolution=request.resolution,
            created_at=now,
            updated_at=now,
        )
        db.create_render_job(job)

        task = asyncio.create_task(self._run_job(job_id, request))
        self._tasks[job_id] = task
        return job

    async def _run_job(self, job_id: str, request: RenderRequest) -> None:
        db = get_database()
        settings = get_settings()
        sem = self._get_semaphore()
        process_holder: dict = {}
        stats_holder: dict = {}
        self._processes[job_id] = process_holder

        def on_progress(pct: float, step: str) -> None:
            if job_id in self._cancelled:
                return
            db.update_render_job(
                job_id,
                status="processing",
                progress_percent=round(pct, 1),
                current_step=step,
            )

        try:
            async with sem:
                if job_id in self._cancelled:
                    return
                db.update_render_job(
                    job_id,
                    status="processing",
                    progress_percent=2.0,
                    current_step="Initializing render worker...",
                )
                output_path, file_size = await execute_render_job(
                    job_id=job_id,
                    request=request,
                    on_progress=on_progress,
                    process_holder=process_holder,
                    stats_holder=stats_holder,
                )
                if job_id in self._cancelled:
                    output_path.unlink(missing_ok=True)
                    return

                db.update_render_job(
                    job_id,
                    status="completed",
                    progress_percent=100.0,
                    current_step="Export Complete! Broadcast MP4 Ready.",
                    output_path=str(output_path),
                    output_video_url=f"/api/v1/render/{job_id}/download",
                    output_file_size_bytes=file_size,
                    segment_cache_hits=stats_holder.get("segment_cache_hits", 0),
                    segment_cache_misses=stats_holder.get("segment_cache_misses", 0),
                    partial_rerender_used=stats_holder.get("partial_rerender_used", False),
                )
        except asyncio.CancelledError:
            partial = settings.RENDER_DIR / f"{job_id}.mp4"
            partial.unlink(missing_ok=True)
            db.update_render_job(
                job_id,
                status="cancelled",
                current_step="Render cancelled by user",
                error_message="Job cancelled.",
            )
        except Exception as exc:
            if job_id not in self._cancelled:
                partial = settings.RENDER_DIR / f"{job_id}.mp4"
                partial.unlink(missing_ok=True)
                db.update_render_job(
                    job_id,
                    status="failed",
                    current_step="Render failed",
                    error_message=str(exc),
                )
        finally:
            self._tasks.pop(job_id, None)
            self._processes.pop(job_id, None)
            self._cancelled.discard(job_id)

    async def cancel(self, job_id: str) -> Optional[RenderJobStatus]:
        """Cancel a queued or running render job and terminate its FFmpeg subprocess."""
        db = get_database()
        job = db.get_render_job(job_id)
        if not job:
            return None
        if job.status in {"completed", "failed", "cancelled"}:
            return job

        self._cancelled.add(job_id)
        holder = self._processes.get(job_id) or {}
        proc = holder.get("process")
        if proc and proc.returncode is None:
            try:
                proc.terminate()
            except ProcessLookupError:
                pass

        task = self._tasks.get(job_id)
        if task and not task.done():
            task.cancel()

        return db.update_render_job(
            job_id,
            status="cancelled",
            current_step="Render cancelled by user",
            error_message="Cancelled by user request.",
        )


_manager_instance: Optional[RenderJobManager] = None


def get_job_manager() -> RenderJobManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = RenderJobManager()
    return _manager_instance

