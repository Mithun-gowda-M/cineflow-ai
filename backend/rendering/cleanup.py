"""Automated disk accounting, TTL cache cleanup policies, and psutil system diagnostics."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import psutil

from backend.api.config import get_settings, utc_now_iso
from backend.api.schemas import (
    CleanupResponse,
    DirectoryStorageBreakdown,
    SystemResourceTelemetry,
)
from backend.video_engine.hardware import detect_hardware_profile


def _dir_bytes(root: Path, *, exclude_subdir: Optional[Path] = None) -> int:
    if not root.is_dir():
        return 0
    total = 0
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        if exclude_subdir is not None and exclude_subdir in item.parents:
            continue
        total += item.stat().st_size
    return total


def compute_directory_sizes() -> DirectoryStorageBreakdown:
    settings = get_settings()
    seg_dir = settings.CACHE_DIR / "segments"
    uploads = _dir_bytes(settings.UPLOAD_DIR)
    proxies = _dir_bytes(settings.PROXY_DIR)
    renders = _dir_bytes(settings.RENDER_DIR)
    cache_other = _dir_bytes(settings.CACHE_DIR, exclude_subdir=seg_dir)
    segments = _dir_bytes(seg_dir)
    total = uploads + proxies + renders + cache_other + segments
    return DirectoryStorageBreakdown(
        uploads_bytes=uploads,
        proxies_bytes=proxies,
        renders_bytes=renders,
        cache_bytes=cache_other,
        segment_cache_bytes=segments,
        total_managed_bytes=total,
    )


def collect_system_telemetry() -> SystemResourceTelemetry:
    hw = detect_hardware_profile()
    cpu_pct = float(psutil.cpu_percent(interval=0.05))
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage(str(get_settings().DATA_DIR.resolve()))
    return SystemResourceTelemetry(
        cpu_percent=round(cpu_pct, 1),
        cpu_cores=hw.cpu_cores,
        memory_used_gb=round(vm.used / (1024**3), 2),
        memory_total_gb=round(vm.total / (1024**3), 2),
        memory_percent=round(float(vm.percent), 1),
        disk_free_gb=round(disk.free / (1024**3), 2),
        disk_total_gb=round(disk.total / (1024**3), 2),
        hardware_encoder=hw.video_encoder,
    )


def purge_storage_caches(
    *,
    purge_cache: bool = True,
    purge_expired_renders: bool = True,
    max_age_hours: int = 24,
) -> CleanupResponse:
    """Delete expired temp caches and rendered exports without touching user source uploads."""
    settings = get_settings()
    cutoff = time.time() - (max_age_hours * 3600) if max_age_hours > 0 else float("inf")
    files_removed = 0
    freed_bytes = 0

    def _clean_tree(folder: Path, *, temp_only: bool = False) -> None:
        nonlocal files_removed, freed_bytes
        if not folder.is_dir():
            return
        for item in folder.rglob("*"):
            if not item.is_file():
                continue
            stat = item.stat()
            is_temp = item.suffix.lower() in {".ass", ".tmp"} or ".tmp." in item.name
            if temp_only and not is_temp and stat.st_mtime > cutoff:
                continue
            if max_age_hours == 0 or stat.st_mtime <= cutoff or is_temp:
                freed_bytes += stat.st_size
                item.unlink(missing_ok=True)
                files_removed += 1

    if purge_cache:
        _clean_tree(settings.CACHE_DIR, temp_only=False)
    if purge_expired_renders:
        _clean_tree(settings.RENDER_DIR, temp_only=False)

    return CleanupResponse(
        files_removed=files_removed,
        freed_bytes=freed_bytes,
        post_cleanup_storage=compute_directory_sizes(),
        executed_at=utc_now_iso(),
    )
