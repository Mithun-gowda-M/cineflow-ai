"""Timeline safety validator enforcing source existence, trim bounds, and zero duplication."""

from __future__ import annotations

from backend.api.schemas import (
    MediaAsset,
    MediaClip,
    StoryboardBeat,
    TimelinePlan,
)


def validate_and_sanitize_timeline(
    timeline: TimelinePlan,
    storyboard: list[StoryboardBeat],
    assets_by_id: dict[str, MediaAsset],
) -> tuple[TimelinePlan, list[StoryboardBeat], list[str]]:
    """Verify every clip references valid ingested media, valid timestamps, and zero duplicates."""
    warnings: list[str] = []
    seen_segments: set[tuple[str, float, float]] = set()
    clean_clips: list[MediaClip] = []
    clean_beats: list[StoryboardBeat] = []
    beat_by_clip_id = {b.clip_id: b for b in storyboard}

    cursor = 0.0
    for clip in timeline.video_clips:
        asset = assets_by_id.get(clip.source_id)
        if not asset or asset.media_kind not in {"video", "image"}:
            warnings.append(f"Dropped clip '{clip.clip_id}': unknown or non-visual source '{clip.source_id}'.")
            continue

        max_source_dur = 10.0 if asset.media_kind == "image" else max(0.5, asset.metadata.duration_seconds or 10.0)
        start_s = max(0.0, min(clip.start_time_seconds, max_source_dur - 0.3))
        end_s = min(max_source_dur, max(start_s + 0.3, clip.end_time_seconds))

        seg_key = (clip.source_id, round(start_s, 2), round(end_s, 2))
        if seg_key in seen_segments:
            warnings.append(f"Blocked duplicate segment for source '{clip.source_id}' ({start_s:.1f}s-{end_s:.1f}s).")
            continue
        seen_segments.add(seg_key)

        speed = max(0.25, min(4.0, clip.playback_speed))
        eff_dur = round((end_s - start_s) / speed, 3)

        overlap = 0.0
        if clean_clips and clip.transition_in and clip.transition_in.type != "none":
            overlap = min(clip.transition_in.duration_seconds, eff_dur * 0.45, cursor * 0.45)
        t_start = round(max(0.0, cursor - overlap), 3)

        sanitized = clip.model_copy(
            update={
                "source_filename": clip.source_filename or asset.original_filename,
                "source_url": clip.source_url or asset.source_url,
                "thumbnail_url": clip.thumbnail_url or asset.thumbnail_url,
                "start_time_seconds": round(start_s, 3),
                "end_time_seconds": round(end_s, 3),
                "timeline_start_seconds": t_start,
                "duration_seconds": eff_dur,
                "playback_speed": round(speed, 2),
            }
        )
        clean_clips.append(sanitized)
        cursor = round(t_start + eff_dur, 3)

        beat = beat_by_clip_id.get(clip.clip_id)
        if beat:
            clean_beats.append(
                beat.model_copy(
                    update={
                        "beat_index": len(clean_beats) + 1,
                        "start_time_seconds": sanitized.start_time_seconds,
                        "end_time_seconds": sanitized.end_time_seconds,
                        "duration_seconds": sanitized.duration_seconds,
                        "playback_speed": sanitized.playback_speed,
                    }
                )
            )

    if not clean_clips:
        raise ValueError("Timeline validation removed all clips; no valid visual segments remained.")

    # Validate audio track references
    clean_audio = [
        cue
        for cue in timeline.audio_tracks
        if cue.source_id in assets_by_id and assets_by_id[cue.source_id].media_kind == "audio"
    ]

    # Clamp subtitles inside actual timeline length
    clean_subs = [
        sub.model_copy(update={"end_seconds": min(cursor, sub.end_seconds)})
        for sub in timeline.subtitles
        if sub.start_seconds < cursor and min(cursor, sub.end_seconds) > sub.start_seconds
    ]

    final_timeline = timeline.model_copy(
        update={
            "target_duration_seconds": max(0.5, round(cursor, 2)),
            "video_clips": clean_clips,
            "audio_tracks": clean_audio,
            "subtitles": clean_subs,
        }
    )
    return final_timeline, clean_beats, warnings

