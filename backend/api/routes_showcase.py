"""Hackathon showcase project seeding and live benchmark report endpoints."""

from __future__ import annotations

import subprocess
import sys
from typing import Optional

from anyio import to_thread
from fastapi import APIRouter, Body, Depends, HTTPException

from backend.api.config import _default_repo_root
from backend.api.schemas import (
    ShowcaseBenchmarkReport,
    ShowcaseLoadRequest,
    ShowcaseLoadResponse,
    ShowcaseStatusResponse,
    UserPublic,
)
from backend.authentication.security import get_optional_current_user
from backend.benchmarking.runner import load_saved_benchmark_report
from backend.showcase.seeder import get_showcase_status, seed_showcase_project

router = APIRouter(prefix="/showcase", tags=["Hackathon Showcase"])


def _run_benchmark_subprocess() -> ShowcaseBenchmarkReport:
    """Execute the benchmark suite in an isolated child process so server DB/cache stay untouched."""
    repo_root = _default_repo_root()
    res = subprocess.run(
        [sys.executable, "-m", "backend.benchmarking.runner"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=180,
        shell=False,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"Benchmark execution exited with code {res.returncode}: {res.stderr.strip() or res.stdout.strip()}"
        )
    report = load_saved_benchmark_report()
    if report is None:
        raise RuntimeError("Benchmark completed but BENCHMARK_REPORT.json was not produced.")
    return report


@router.get("/status", response_model=ShowcaseStatusResponse)
def showcase_status() -> ShowcaseStatusResponse:
    """Report Full-HD sample media readiness, seeded project state, and benchmark status."""
    return get_showcase_status()


@router.post("/load", response_model=ShowcaseLoadResponse)
async def load_showcase_project(
    payload: Optional[ShowcaseLoadRequest] = Body(default=None),
    current_user: Optional[UserPublic] = Depends(get_optional_current_user),
) -> ShowcaseLoadResponse:
    """Ingest sample HD footage into the active studio library and prepare the BMSIT showcase timeline."""
    force_reset = bool(payload.force_reset) if payload else False
    owner_id = current_user.id if current_user else None
    try:
        return await to_thread.run_sync(
            lambda: seed_showcase_project(force_reset=force_reset, owner_id=owner_id)
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load showcase project: {exc}") from exc


@router.get("/benchmarks", response_model=ShowcaseBenchmarkReport)
async def get_benchmark_report() -> ShowcaseBenchmarkReport:
    """Return the latest verified hardware & FFmpeg benchmark report (running once if not yet generated)."""
    saved = load_saved_benchmark_report()
    if saved is not None:
        return saved
    try:
        return await to_thread.run_sync(_run_benchmark_subprocess)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Benchmark evaluation failed: {exc}") from exc


@router.post("/benchmarks/run", response_model=ShowcaseBenchmarkReport)
async def trigger_benchmark_run() -> ShowcaseBenchmarkReport:
    """Execute a fresh isolated host hardware & pipeline benchmark pass and return measured metrics."""
    try:
        return await to_thread.run_sync(_run_benchmark_subprocess)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Benchmark evaluation failed: {exc}") from exc

