"""Unit tests for copyright-safe reference URL validation, SSRF defense, and CV style analysis."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.trend_intelligence.analyzer import analyze_reference_video
from backend.trend_intelligence.safety import TrendSafetyError, validate_safe_reference_url
from backend.video_engine.ffmpeg_runner import run_ffmpeg_sync


@pytest.mark.parametrize(
    "bad_url",
    [
        "file:///C:/Windows/win.ini",
        "ftp://example.com/clip.mp4",
        "javascript:alert(1)",
        "http://localhost:8000/api/v1/media",
        "http://127.0.0.1:8000/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://192.168.1.10/private.mp4",
        "http://10.0.0.5/internal",
        "https://user:secret@example.com/video",
        "https://service.internal/feed",
    ],
)
def test_url_safety_blocks_ssrf_and_non_http_schemes(bad_url: str) -> None:
    with pytest.raises(TrendSafetyError):
        validate_safe_reference_url(bad_url)


def test_url_safety_accepts_public_url_and_detects_vertical_hint() -> None:
    url, hints = validate_safe_reference_url("https://example.com/shorts/campus-fest-recap")
    assert url.startswith("https://")
    assert hints["domain"] == "example.com"
    assert hints["format_hint"] == "vertical_short"


def test_analyze_reference_video_extracts_cut_frequency_velocity_and_warm_mood(tmp_path: Path) -> None:
    # Build a synthetic 4.5s multi-cut clip: 1.5s warm amber -> 1.5s high-motion testsrc -> 1.5s cool dark slate
    ref_mp4 = tmp_path / "reference_multicut.mp4"
    run_ffmpeg_sync(
        [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=#F59E0B:s=640x360:r=30:d=1.5",
            "-f",
            "lavfi",
            "-i",
            "testsrc=s=640x360:r=30:d=1.5",
            "-f",
            "lavfi",
            "-i",
            "color=c=#EA580C:s=640x360:r=30:d=1.5",
            "-filter_complex",
            "[0:v][1:v][2:v]concat=n=3:v=1:a=0[vout]",
            "-map",
            "[vout]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(ref_mp4),
        ],
        timeout=30,
    )

    metrics = analyze_reference_video(ref_mp4)
    assert metrics.duration_seconds >= 4.0
    assert metrics.cuts_count >= 1
    assert metrics.cuts_per_minute > 10.0
    assert metrics.motion_velocity_score >= 8.0
    assert metrics.recommended_aspect_ratio == "16:9"
    assert len(metrics.dominant_palette) >= 1
    assert metrics.color_mood in {"warm_golden", "balanced", "bright", "low_light"}


def test_analyze_portrait_dark_reference_video(tmp_path: Path) -> None:
    ref_vert = tmp_path / "reference_vert_dark.mp4"
    run_ffmpeg_sync(
        [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=#0B0D13:s=360x640:r=30:d=2.0",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(ref_vert),
        ],
        timeout=20,
    )
    metrics = analyze_reference_video(ref_vert)
    assert metrics.recommended_aspect_ratio == "9:16"
    assert metrics.color_mood == "low_light"
    assert metrics.cinematic_effects.vignette is True

