"""Thumbnail and lightweight 720p proxy generation via FFmpeg."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from backend.api.config import get_settings
from backend.video_engine.ffmpeg_runner import FFmpegExecutionError, run_ffmpeg_sync
from backend.video_engine.hardware import detect_hardware_profile


def generate_thumbnail(source_path: Path, media_id: str, duration_seconds: float, is_image: bool = False) -> Optional[Path]:
    """Extract a 480px JPEG thumbnail for fast media browser preview."""
    settings = get_settings()
    thumb_path = settings.PROXY_DIR / f"{media_id}_thumb.jpg"

    if is_image:
        args = [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source_path),
            "-vf",
            "scale=480:-2",
            "-q:v",
            "3",
            str(thumb_path),
        ]
    else:
        seek_sec = min(1.0, round(duration_seconds * 0.25, 2)) if duration_seconds > 0.2 else 0.0
        args = [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(seek_sec),
            "-i",
            str(source_path),
            "-frames:v",
            "1",
            "-vf",
            "scale=480:-2",
            "-q:v",
            "3",
            str(thumb_path),
        ]

    try:
        run_ffmpeg_sync(args, timeout=60)
        return thumb_path if thumb_path.is_file() else None
    except FFmpegExecutionError:
        return None


def generate_video_proxy(source_path: Path, media_id: str, has_audio: bool) -> Optional[Path]:
    """Create a lightweight H.264 `+faststart` scrubbing proxy capped by hardware profile height."""
    settings = get_settings()
    profile = detect_hardware_profile()
    proxy_path = settings.PROXY_DIR / f"{media_id}_proxy.mp4"
    target_h = profile.proxy_height

    args = [
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source_path),
        "-vf",
        f"scale=-2:'min(ih,{target_h})',fps=30,format=yuv420p",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "26",
    ]
    if has_audio:
        args.extend(["-c:a", "aac", "-b:a", "96k"])
    else:
        args.append("-an")
    args.extend(["-movflags", "+faststart", str(proxy_path)])

    try:
        run_ffmpeg_sync(args, timeout=240)
        return proxy_path if proxy_path.is_file() else None
    except FFmpegExecutionError:
        return None

