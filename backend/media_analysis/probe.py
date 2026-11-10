"""FFprobe metadata extraction for videos, images, and audio tracks."""

from __future__ import annotations

import json
import math
from pathlib import Path

from backend.api.schemas import MediaMetadata
from backend.video_engine.ffmpeg_runner import run_ffprobe_sync


def _parse_fraction(fraction_str: str | None) -> float:
    if not fraction_str or fraction_str in {"0/0", "N/A"}:
        return 0.0
    if "/" in fraction_str:
        num_s, den_s = fraction_str.split("/", 1)
        try:
            num, den = float(num_s), float(den_s)
            return round(num / den, 3) if den != 0 else 0.0
        except ValueError:
            return 0.0
    try:
        return round(float(fraction_str), 3)
    except ValueError:
        return 0.0


def _extract_rotation(video_stream: dict) -> int:
    tags = video_stream.get("tags") or {}
    if "rotate" in tags:
        try:
            return int(tags["rotate"])
        except (TypeError, ValueError):
            pass
    for sd in video_stream.get("side_data_list") or []:
        if "rotation" in sd:
            try:
                return abs(int(sd["rotation"]))
            except (TypeError, ValueError):
                pass
    return 0


def _compute_aspect_ratio(width: int, height: int) -> str:
    if width <= 0 or height <= 0:
        return "16:9"
    ratio = width / height
    known = [
        ("16:9", 16 / 9),
        ("9:16", 9 / 16),
        ("1:1", 1.0),
        ("4:5", 4 / 5),
        ("4:3", 4 / 3),
        ("21:9", 21 / 9),
    ]
    for label, target in known:
        if abs(ratio - target) < 0.04:
            return label
    divisor = math.gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def probe_media_file(file_path: Path, is_image: bool = False) -> MediaMetadata:
    """Inspect a local media file with ffprobe and return structured `MediaMetadata`."""
    proc = run_ffprobe_sync(
        [
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ]
    )
    payload = json.loads(proc.stdout or "{}")
    streams = payload.get("streams") or []
    fmt = payload.get("format") or {}

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    width = int(video_stream.get("width", 0)) if video_stream else 0
    height = int(video_stream.get("height", 0)) if video_stream else 0
    rotation = _extract_rotation(video_stream) if video_stream else 0
    if rotation in {90, 270} and width > 0 and height > 0:
        width, height = height, width

    fps = 0.0
    if video_stream and not is_image:
        fps = _parse_fraction(video_stream.get("avg_frame_rate")) or _parse_fraction(
            video_stream.get("r_frame_rate")
        )

    duration_raw = (
        (video_stream.get("duration") if video_stream else None)
        or (audio_stream.get("duration") if audio_stream else None)
        or fmt.get("duration")
    )
    try:
        duration_seconds = 0.0 if is_image else round(float(duration_raw or 0.0), 3)
    except (TypeError, ValueError):
        duration_seconds = 0.0

    try:
        bitrate_kbps = int(int(fmt.get("bit_rate", 0)) / 1000)
    except (TypeError, ValueError):
        bitrate_kbps = 0

    return MediaMetadata(
        width=width,
        height=height,
        fps=fps,
        duration_seconds=duration_seconds,
        codec=str(video_stream.get("codec_name", "")) if video_stream else "",
        audio_codec=str(audio_stream.get("codec_name")) if audio_stream else None,
        has_audio=audio_stream is not None,
        audio_channels=int(audio_stream.get("channels", 0)) if audio_stream else 0,
        sample_rate=int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,
        bitrate_kbps=bitrate_kbps,
        aspect_ratio=_compute_aspect_ratio(width, height) if width and height else "16:9",
        rotation=rotation,
    )

