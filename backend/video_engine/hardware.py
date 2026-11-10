"""Hardware detection and adaptive encoding profile resolver."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from backend.api.config import get_settings
from backend.video_engine.ffmpeg_runner import FFmpegNotFoundError, resolve_binary

ProfileName = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class EncodingProfile:
    """Resolved processing profile for rendering and proxy generation."""

    profile: ProfileName
    cpu_cores: int
    free_disk_gb: float
    video_encoder: str
    preset: str
    crf: int
    proxy_height: int
    max_width: int
    max_concurrent_renders: int
    hw_accel_available: bool
    detected_encoders: tuple[str, ...]


def _probe_working_hw_encoder(ffmpeg_bin: str) -> tuple[str, list[str]]:
    """Verify which H.264 encoders actually initialize on the current host."""
    try:
        res = subprocess.run(
            [ffmpeg_bin, "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )
        encoders_output = res.stdout if res.returncode == 0 else ""
    except Exception:
        return "libx264", ["libx264"]

    candidates = ["h264_nvenc", "h264_qsv", "h264_amf"]
    listed = [enc for enc in candidates if enc in encoders_output]

    working: list[str] = []
    for enc in listed:
        try:
            test = subprocess.run(
                [
                    ffmpeg_bin,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=black:s=128x128:d=0.1",
                    "-frames:v",
                    "2",
                    "-c:v",
                    enc,
                    "-f",
                    "null",
                    "-",
                ],
                capture_output=True,
                timeout=8,
                shell=False,
            )
            if test.returncode == 0:
                working.append(enc)
        except Exception:
            continue

    if "libx264" in encoders_output or not working:
        working.append("libx264")

    return working[0], working


@lru_cache(maxsize=1)
def detect_hardware_profile(force_profile: str | None = None) -> EncodingProfile:
    """Detect CPU cores, disk space, and usable FFmpeg encoders."""
    settings = get_settings()
    cpu_cores = os.cpu_count() or 2

    try:
        disk = shutil.disk_usage(settings.DATA_DIR)
        free_disk_gb = round(disk.free / (1024**3), 2)
    except Exception:
        free_disk_gb = 0.0

    try:
        ffmpeg_bin = resolve_binary("ffmpeg")
        best_encoder, working_encoders = _probe_working_hw_encoder(ffmpeg_bin)
    except FFmpegNotFoundError:
        best_encoder, working_encoders = "libx264", ["libx264"]

    hw_accel_available = best_encoder != "libx264"

    selected = (force_profile or settings.HARDWARE_PROFILE or "auto").lower()
    if selected == "auto":
        if hw_accel_available and cpu_cores >= 8:
            selected = "high"
        elif cpu_cores >= 6:
            selected = "medium"
        else:
            selected = "low"

    if selected == "high":
        return EncodingProfile(
            profile="high",
            cpu_cores=cpu_cores,
            free_disk_gb=free_disk_gb,
            video_encoder=best_encoder,
            preset="p4" if best_encoder == "h264_nvenc" else "medium",
            crf=19,
            proxy_height=1080,
            max_width=3840,
            max_concurrent_renders=4,
            hw_accel_available=hw_accel_available,
            detected_encoders=tuple(working_encoders),
        )
    if selected == "medium":
        return EncodingProfile(
            profile="medium",
            cpu_cores=cpu_cores,
            free_disk_gb=free_disk_gb,
            video_encoder=best_encoder if hw_accel_available else "libx264",
            preset="fast" if not hw_accel_available else "p3",
            crf=21,
            proxy_height=720,
            max_width=1920,
            max_concurrent_renders=2,
            hw_accel_available=hw_accel_available,
            detected_encoders=tuple(working_encoders),
        )

    return EncodingProfile(
        profile="low",
        cpu_cores=cpu_cores,
        free_disk_gb=free_disk_gb,
        video_encoder="libx264",
        preset="veryfast",
        crf=23,
        proxy_height=540,
        max_width=1920,
        max_concurrent_renders=1,
        hw_accel_available=hw_accel_available,
        detected_encoders=tuple(working_encoders),
    )

