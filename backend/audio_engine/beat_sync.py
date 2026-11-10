"""Beat-synchronized timeline cut aligner using Librosa beat/downbeat timestamps."""

from __future__ import annotations

from typing import Optional

from backend.api.schemas import MediaAsset, MediaClip, TimelinePlan


def _nearest_beat(
    target_time: float,
    downbeats: list[float],
    beats: list[float],
    tolerance: float,
) -> Optional[float]:
    """Prefer snapping to downbeats within tolerance, falling back to regular beats."""
    if downbeats:
        closest_db = min(downbeats, key=lambda b: abs(b - target_time))
        if abs(closest_db - target_time) <= tolerance:
            return closest_db

    if beats:
        closest_b = min(beats, key=lambda b: abs(b - target_time))
        if abs(closest_b - target_time) <= tolerance:
            return closest_b

    return None


def align_timeline_to_beats(
    timeline: TimelinePlan,
    beat_timestamps: list[float],
    downbeat_timestamps: list[float],
    assets_by_id: dict[str, MediaAsset],
    *,
    tolerance_seconds: float = 0.35,
) -> tuple[TimelinePlan, int, list[float]]:
    """Snap sequential clip transitions toward musical beats while respecting source trim bounds."""
    if not beat_timestamps and not downbeat_timestamps:
        return timeline, 0, []

    aligned_clips: list[MediaClip] = []
    snapped_count = 0
    beats_used: list[float] = []
    cursor = 0.0

    for idx, clip in enumerate(timeline.video_clips):
        asset = assets_by_id.get(clip.source_id)
        max_source_dur = (
            10.0
            if (not asset or asset.media_kind == "image")
            else max(0.5, asset.metadata.duration_seconds or 10.0)
        )

        overlap = 0.0
        if idx > 0 and clip.transition_in and clip.transition_in.type != "none":
            overlap = min(clip.transition_in.duration_seconds, clip.duration_seconds * 0.45, cursor * 0.45)

        t_start = round(max(0.0, cursor - overlap), 3)
        current_end_on_timeline = t_start + clip.duration_seconds

        # Align intermediate cuts (keep final clip ending smoothly unless beat is nearby)
        snapped_beat = _nearest_beat(
            current_end_on_timeline,
            downbeat_timestamps,
            beat_timestamps,
            tolerance_seconds,
        )

        new_dur = clip.duration_seconds
        new_end_trim = clip.end_time_seconds

        if snapped_beat is not None and snapped_beat > t_start + 0.8:
            candidate_dur = round(snapped_beat - t_start, 3)
            needed_raw = candidate_dur * clip.playback_speed
            candidate_end_trim = round(clip.start_time_seconds + needed_raw, 3)

            if candidate_end_trim <= max_source_dur and candidate_dur >= 0.8:
                if abs(candidate_dur - clip.duration_seconds) >= 0.03:
                    snapped_count += 1
                    beats_used.append(snapped_beat)
                new_dur = candidate_dur
                new_end_trim = candidate_end_trim

        aligned_clips.append(
            clip.model_copy(
                update={
                    "timeline_start_seconds": t_start,
                    "duration_seconds": new_dur,
                    "end_time_seconds": new_end_trim,
                }
            )
        )
        cursor = round(t_start + new_dur, 3)

    updated_timeline = timeline.model_copy(
        update={
            "target_duration_seconds": max(0.5, round(cursor, 2)),
            "video_clips": aligned_clips,
        }
    )
    return updated_timeline, snapped_count, beats_used

