"""High-level timeline resolution, FFmpeg rendering execution, and MP4 output verification."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from backend.api.config import get_settings
from backend.api.database import get_database
from backend.api.schemas import RenderRequest
from backend.audio_engine.mixer import ResolvedAudioSource
from backend.media_analysis.probe import probe_media_file
from backend.rendering.segment_cache import prepare_cached_segments
from backend.video_engine.ffmpeg_runner import (
    FFmpegExecutionError,
    run_ffmpeg_with_progress,
)
from backend.video_engine.filtergraph import (
    ResolvedVideoSource,
    build_render_command,
    resolve_canvas_dimensions,
)
from backend.video_engine.hardware import detect_hardware_profile
from backend.video_engine.typography import generate_ass_file


class RenderSourceError(ValueError):
    """Raised when a timeline references missing or invalid media assets."""


def resolve_timeline_sources(
    request: RenderRequest,
) -> tuple[list[ResolvedVideoSource], list[ResolvedAudioSource]]:
    """Resolve and verify all source assets referenced in a timeline."""
    db = get_database()
    resolved_clips: list[ResolvedVideoSource] = []
    for clip in sorted(request.timeline.video_clips, key=lambda c: c.timeline_start_seconds):
        asset = db.get_media_asset(clip.source_id)
        if not asset:
            raise RenderSourceError(f"Referenced video/image asset '{clip.source_id}' was not found.")
        if asset.media_kind not in {"video", "image"}:
            raise RenderSourceError(f"Asset '{clip.source_id}' is '{asset.media_kind}', expected video or image.")
        if not Path(asset.file_path).is_file():
            raise RenderSourceError(f"Source file missing on disk for asset '{clip.source_id}'.")
        resolved_clips.append(ResolvedVideoSource(clip=clip, asset=asset))

    resolved_audio: list[ResolvedAudioSource] = []
    for cue in request.timeline.audio_tracks:
        asset = db.get_media_asset(cue.source_id)
        if not asset:
            raise RenderSourceError(f"Referenced audio asset '{cue.source_id}' was not found.")
        if not Path(asset.file_path).is_file():
            raise RenderSourceError(f"Audio file missing on disk for asset '{cue.source_id}'.")
        resolved_audio.append(ResolvedAudioSource(cue=cue, file_path=asset.file_path))

    return resolved_clips, resolved_audio


def _choose_encoder(preference: str) -> tuple[str, str, int]:
    profile = detect_hardware_profile()
    if preference == "cpu":
        return "libx264", "fast", 21
    if preference in {"nvenc", "qsv", "amf"}:
        candidate = f"h264_{preference}"
        if candidate in profile.detected_encoders:
            return candidate, profile.preset, profile.crf
    return profile.video_encoder, profile.preset, profile.crf


async def execute_render_job(
    job_id: str,
    request: RenderRequest,
    on_progress: Callable[[float, str], None],
    process_holder: Optional[dict] = None,
    stats_holder: Optional[dict] = None,
) -> tuple[Path, int]:
    """Execute full FFmpeg render and verify the resulting MP4 with FFprobe."""
    settings = get_settings()
    output_path = settings.RENDER_DIR / f"{job_id}.mp4"

    on_progress(5.0, "Validating timeline & probing source assets...")
    resolved_clips, resolved_audio = resolve_timeline_sources(request)

    encoder, preset, quality = _choose_encoder(request.encoder_preference)
    render_timeline = request.timeline
    render_clips = resolved_clips
    cache_hits = 0
    cache_misses = len(resolved_clips)

    if request.partial_cache:
        on_progress(9.0, "Checking per-clip partial render segment cache...")
        render_timeline, render_clips, cache_hits, cache_misses = await prepare_cached_segments(
            timeline=request.timeline,
            resolved_clips=resolved_clips,
            resolution=request.resolution,
            encoder=encoder,
            preset=preset,
            quality=quality,
            process_holder=process_holder,
        )

    if stats_holder is not None:
        stats_holder["segment_cache_hits"] = cache_hits
        stats_holder["segment_cache_misses"] = cache_misses
        stats_holder["partial_rerender_used"] = bool(request.partial_cache and cache_hits > 0)

    subtitle_ass_path: Optional[Path] = None
    if render_timeline.subtitles:
        width, height = resolve_canvas_dimensions(render_timeline.aspect_ratio, request.resolution)
        subtitle_ass_path = settings.CACHE_DIR / f"{job_id}.ass"
        generate_ass_file(render_timeline.subtitles, width, height, subtitle_ass_path)

    cache_label = f" ({cache_hits}/{len(resolved_clips)} segments cached)" if request.partial_cache else ""
    on_progress(12.0, f"Building FFmpeg complex filtergraph ({encoder}){cache_label}...")
    try:
        cmd_args, expected_duration = build_render_command(
            timeline=render_timeline,
            resolved_clips=render_clips,
            resolved_audio=resolved_audio,
            output_path=str(output_path),
            resolution=request.resolution,
            encoder=encoder,
            preset=preset,
            quality=quality,
            subtitle_ass_path=subtitle_ass_path,
        )

        try:
            await run_ffmpeg_with_progress(
                args=cmd_args,
                total_duration_seconds=expected_duration,
                on_progress=on_progress,
                process_holder=process_holder,
            )
        except FFmpegExecutionError:
            # Automatic safe CPU fallback if hardware encoder rejected a filter or stream format
            if encoder != "libx264":
                on_progress(15.0, f"Hardware encoder '{encoder}' unavailable for stream; falling back to CPU libx264...")
                fallback_args, expected_duration = build_render_command(
                    timeline=render_timeline,
                    resolved_clips=render_clips,
                    resolved_audio=resolved_audio,
                    output_path=str(output_path),
                    resolution=request.resolution,
                    encoder="libx264",
                    preset="fast",
                    quality=21,
                    subtitle_ass_path=subtitle_ass_path,
                )
                await run_ffmpeg_with_progress(
                    args=fallback_args,
                    total_duration_seconds=expected_duration,
                    on_progress=on_progress,
                    process_holder=process_holder,
                )
            else:
                raise
    finally:
        if subtitle_ass_path is not None:
            subtitle_ass_path.unlink(missing_ok=True)

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError("Render completed without producing a valid non-empty MP4 output.")

    on_progress(98.0, "Verifying rendered MP4 streams with FFprobe...")
    verified_meta = probe_media_file(output_path, is_image=False)
    if verified_meta.width <= 0 or verified_meta.height <= 0 or verified_meta.duration_seconds <= 0:
        raise RuntimeError("Rendered MP4 verification failed: invalid video stream dimensions or duration.")

    file_size = output_path.stat().st_size
    on_progress(100.0, "Export Complete! Broadcast MP4 Ready.")
    return output_path, file_size

