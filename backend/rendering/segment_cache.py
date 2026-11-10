"""SHA-256 per-clip intermediate segment caching for fast partial timeline re-rendering."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional

from backend.api.config import get_settings
from backend.api.schemas import (
    ColorGradePreset,
    MediaAsset,
    MediaClip,
    ResolutionPreset,
    TimelinePlan,
)
from backend.media_analysis.probe import probe_media_file
from backend.video_engine.ffmpeg_runner import run_ffmpeg_with_progress
from backend.video_engine.filtergraph import (
    ResolvedVideoSource,
    build_render_command,
    resolve_canvas_dimensions,
)


def compute_segment_cache_key(
    item: ResolvedVideoSource,
    *,
    width: int,
    height: int,
    fps: int,
    effective_grade: ColorGradePreset,
    ken_burns_on_images: bool,
    apply_fade_in: bool,
    apply_fade_out: bool,
) -> str:
    """Compute a deterministic SHA-256 fingerprint for a single normalized timeline clip."""
    src_path = Path(item.asset.file_path)
    stat = src_path.stat()
    payload = {
        "v": 1,
        "source_id": item.asset.id,
        "file_size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "media_kind": item.asset.media_kind,
        "has_audio": item.asset.metadata.has_audio,
        "start_s": round(item.clip.start_time_seconds, 3),
        "end_s": round(item.clip.end_time_seconds, 3),
        "speed": round(item.clip.playback_speed, 3),
        "speed_ramp": item.clip.speed_ramp,
        "grade": effective_grade,
        "ken_burns": ken_burns_on_images if item.asset.media_kind == "image" else False,
        "width": width,
        "height": height,
        "fps": fps,
        "fade_in": (
            round(item.clip.transition_in.duration_seconds, 3)
            if apply_fade_in and item.clip.transition_in
            else 0.0
        ),
        "fade_out": (
            round(item.clip.transition_out.duration_seconds, 3)
            if apply_fade_out and item.clip.transition_out
            else 0.0
        ),
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def _prune_segment_cache(cache_dir: Path, max_bytes: int) -> None:
    if max_bytes <= 0 or not cache_dir.is_dir():
        return
    files = [p for p in cache_dir.glob("*.mp4") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    if total <= max_bytes:
        return
    for oldest in sorted(files, key=lambda p: p.stat().st_mtime):
        sz = oldest.stat().st_size
        oldest.unlink(missing_ok=True)
        total -= sz
        if total <= max_bytes:
            break


async def prepare_cached_segments(
    *,
    timeline: TimelinePlan,
    resolved_clips: list[ResolvedVideoSource],
    resolution: ResolutionPreset,
    encoder: str,
    preset: str,
    quality: int,
    process_holder: Optional[dict] = None,
) -> tuple[TimelinePlan, list[ResolvedVideoSource], int, int]:
    """Ensure normalized intermediate MP4s exist per clip, returning rewritten stitch inputs and hit/miss counts."""
    settings = get_settings()
    seg_dir = settings.CACHE_DIR / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)

    width, height = resolve_canvas_dimensions(timeline.aspect_ratio, resolution)
    hits = 0
    misses = 0
    stitched_clips: list[MediaClip] = []
    stitched_sources: list[ResolvedVideoSource] = []

    for idx, item in enumerate(resolved_clips):
        clip = item.clip
        eff_grade = clip.color_grade or timeline.color_grade
        apply_fade_in = bool(idx == 0 and clip.transition_in and clip.transition_in.type == "fade_from_black")
        apply_fade_out = bool(
            idx == len(resolved_clips) - 1 and clip.transition_out and clip.transition_out.type == "fade_to_black"
        )

        seg_key = compute_segment_cache_key(
            item,
            width=width,
            height=height,
            fps=timeline.fps,
            effective_grade=eff_grade,
            ken_burns_on_images=timeline.cinematic_effects.ken_burns_on_images,
            apply_fade_in=apply_fade_in,
            apply_fade_out=apply_fade_out,
        )
        seg_path = seg_dir / f"{seg_key}.mp4"

        if seg_path.is_file() and seg_path.stat().st_size > 1024:
            hits += 1
        else:
            misses += 1
            single_clip = clip.model_copy(
                update={
                    "timeline_start_seconds": 0.0,
                    "transition_in": clip.transition_in if apply_fade_in else None,
                    "transition_out": clip.transition_out if apply_fade_out else None,
                    "color_grade": eff_grade,
                }
            )
            single_tl = TimelinePlan(
                project_id=timeline.project_id,
                title="seg_cache",
                aspect_ratio=timeline.aspect_ratio,
                fps=timeline.fps,
                color_grade=eff_grade,
                cinematic_effects=timeline.cinematic_effects.model_copy(
                    update={
                        "vignette": False,
                        "film_grain": False,
                        "audio_ducking": False,
                        "loudness_normalize": False,
                    }
                ),
                video_clips=[single_clip],
            )
            tmp_seg = seg_dir / f"{seg_key}.{idx}.tmp.mp4"
            # Render intermediate normalized clip cleanly using high quality fast libx264 intermediate
            seg_cmd, seg_dur = build_render_command(
                timeline=single_tl,
                resolved_clips=[ResolvedVideoSource(clip=single_clip, asset=item.asset)],
                resolved_audio=[],
                output_path=str(tmp_seg),
                resolution=resolution,
                encoder="libx264",
                preset="veryfast",
                quality=15,
            )
            try:
                await run_ffmpeg_with_progress(
                    args=seg_cmd,
                    total_duration_seconds=seg_dur,
                    on_progress=lambda _p, _s: None,
                    process_holder=process_holder,
                )
                tmp_seg.replace(seg_path)
            finally:
                tmp_seg.unlink(missing_ok=True)

        probed_seg = probe_media_file(seg_path, is_image=False)
        seg_actual_dur = max(0.2, round(probed_seg.duration_seconds, 3))

        # Preserve downstream crossfade/wipe transitions while avoiding duplicate edge fade_from/to_black
        next_trans_in = None if apply_fade_in else clip.transition_in
        next_trans_out = None if apply_fade_out else clip.transition_out

        rebound_clip = clip.model_copy(
            update={
                "start_time_seconds": 0.0,
                "end_time_seconds": seg_actual_dur,
                "duration_seconds": seg_actual_dur,
                "playback_speed": 1.0,
                "speed_ramp": "none",
                "color_grade": "natural",
                "transition_in": next_trans_in,
                "transition_out": next_trans_out,
            }
        )
        rebound_asset: MediaAsset = item.asset.model_copy(
            update={
                "media_kind": "video",
                "file_path": str(seg_path),
                "metadata": probed_seg.model_copy(update={"has_audio": item.asset.metadata.has_audio}),
            }
        )
        stitched_clips.append(rebound_clip)
        stitched_sources.append(ResolvedVideoSource(clip=rebound_clip, asset=rebound_asset))

    _prune_segment_cache(seg_dir, settings.MAX_SEGMENT_CACHE_MB * 1024 * 1024)

    stitched_timeline = timeline.model_copy(
        update={
            "color_grade": "natural",
            "video_clips": stitched_clips,
        }
    )
    return stitched_timeline, stitched_sources, hits, misses

