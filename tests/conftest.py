"""Shared pytest fixtures for isolated API, security, and real FFmpeg rendering tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api import config as config_mod
from backend.api import database as db_mod
from backend.job_manager import queue as queue_mod
from backend.video_engine.ffmpeg_runner import clear_binary_cache, run_ffmpeg_sync
from backend.video_engine.hardware import detect_hardware_profile


@pytest.fixture()
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolate storage directories and SQLite database per test in a temporary directory."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "data" / "uploads"))
    monkeypatch.setenv("PROXY_DIR", str(tmp_path / "data" / "proxies"))
    monkeypatch.setenv("RENDER_DIR", str(tmp_path / "data" / "renders"))
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "data" / "cache"))
    monkeypatch.setenv("PROJECTS_DIR", str(tmp_path / "data" / "projects"))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "data" / "cineflow_test.db"))
    monkeypatch.setenv("HARDWARE_PROFILE", "low")

    config_mod.get_settings.cache_clear()
    detect_hardware_profile.cache_clear()
    clear_binary_cache()
    db_mod._db_instance = None
    queue_mod._manager_instance = None

    settings = config_mod.get_settings()
    settings.ensure_directories()
    db_mod.get_database()

    from backend.api.main import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client, settings, tmp_path

    db_mod._db_instance = None
    queue_mod._manager_instance = None
    config_mod.get_settings.cache_clear()
    detect_hardware_profile.cache_clear()


def create_synthetic_video(
    out_path: Path,
    *,
    width: int = 640,
    height: int = 360,
    duration: float = 2.0,
    with_audio: bool = True,
) -> Path:
    """Generate a valid synthetic MP4 clip via FFmpeg lavfi sources."""
    args = [
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"testsrc=size={width}x{height}:rate=30:duration={duration}",
    ]
    if with_audio:
        args.extend(["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={duration}"])
        args.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest"])
    else:
        args.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-an"])
    args.append(str(out_path))
    run_ffmpeg_sync(args, timeout=30)
    return out_path


def create_synthetic_image(out_path: Path, *, width: int = 800, height: int = 600) -> Path:
    """Generate a valid PNG test image via FFmpeg lavfi color source."""
    run_ffmpeg_sync(
        [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c=#E5B869:s={width}x{height}",
            "-frames:v",
            "1",
            str(out_path),
        ],
        timeout=20,
    )
    return out_path


def create_synthetic_audio(out_path: Path, *, duration: float = 5.0) -> Path:
    """Generate a valid stereo WAV track via FFmpeg lavfi sine source."""
    run_ffmpeg_sync(
        [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=220:sample_rate=48000:duration={duration}",
            "-ac",
            "2",
            str(out_path),
        ],
        timeout=20,
    )
    return out_path

