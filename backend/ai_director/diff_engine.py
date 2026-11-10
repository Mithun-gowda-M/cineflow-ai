"""Timeline diff calculator comparing pre-edit and post-edit timelines cleanly."""

from __future__ import annotations

from backend.api.schemas import (
    CinematicEffects,
    ColorGradePreset,
    MediaClip,
    TimelineDiffSummary,
    TimelinePlan,
)


def _clip_content_signature(
    clip: MediaClip,
    *,
    global_grade: ColorGradePreset,
    effects: CinematicEffects,
) -> tuple:
    return (
        clip.source_id,
        round(clip.start_time_seconds, 3),
        round(clip.end_time_seconds, 3),
        round(clip.duration_seconds, 3),
        round(clip.playback_speed, 3),
        clip.speed_ramp,
        clip.color_grade or global_grade,
        clip.transition_in.model_dump() if clip.transition_in else None,
        clip.transition_out.model_dump() if clip.transition_out else None,
        effects.ken_burns_on_images,
    )


def _describe_clip_delta(old: MediaClip, new: MediaClip) -> list[str]:
    notes: list[str] = []
    if old.source_id != new.source_id:
        old_name = old.source_filename or old.source_id
        new_name = new.source_filename or new.source_id
        notes.append(f"Replaced clip '{old.clip_id}' ({old_name} -> {new_name})")
        return notes

    if abs(old.duration_seconds - new.duration_seconds) >= 0.05 or abs(old.start_time_seconds - new.start_time_seconds) >= 0.05:
        notes.append(
            f"Adjusted timing of '{new.source_filename or new.clip_id}' "
            f"({old.duration_seconds:.1f}s -> {new.duration_seconds:.1f}s)"
        )
    if abs(old.playback_speed - new.playback_speed) >= 0.02:
        notes.append(
            f"Changed speed of '{new.source_filename or new.clip_id}' "
            f"({old.playback_speed:.2f}x -> {new.playback_speed:.2f}x)"
        )
    if old.speed_ramp != new.speed_ramp:
        notes.append(f"Changed speed ramp on '{new.clip_id}': {old.speed_ramp} -> {new.speed_ramp}")
    if old.transition_in != new.transition_in:
        old_t = old.transition_in.type if old.transition_in else "none"
        new_t = new.transition_in.type if new.transition_in else "none"
        notes.append(f"Changed transition on '{new.clip_id}': {old_t} -> {new_t}")
    if old.color_grade != new.color_grade:
        notes.append(f"Changed clip grade on '{new.clip_id}': {old.color_grade} -> {new.color_grade}")
    return notes


def compute_timeline_diff(before: TimelinePlan, after: TimelinePlan) -> TimelineDiffSummary:
    """Compare two timelines and report structural changes plus affected segment indices."""
    before_by_id = {c.clip_id: c for c in before.video_clips}
    after_by_id = {c.clip_id: c for c in after.video_clips}

    global_visual_changed = (
        before.aspect_ratio != after.aspect_ratio
        or before.fps != after.fps
        or before.color_grade != after.color_grade
        or before.cinematic_effects.vignette != after.cinematic_effects.vignette
        or before.cinematic_effects.film_grain != after.cinematic_effects.film_grain
        or before.cinematic_effects.ken_burns_on_images != after.cinematic_effects.ken_burns_on_images
    )
    subtitles_changed = [s.model_dump() for s in before.subtitles] != [s.model_dump() for s in after.subtitles]
    audio_changed = [a.model_dump() for a in before.audio_tracks] != [a.model_dump() for a in after.audio_tracks]

    added_ids: list[str] = []
    removed_ids: list[str] = [c.clip_id for c in before.video_clips if c.clip_id not in after_by_id]
    modified_ids: list[str] = []
    shifted_ids: list[str] = []
    unchanged_ids: list[str] = []
    affected_indices: list[int] = []
    changes: list[str] = []

    for idx, new_clip in enumerate(after.video_clips):
        old_clip = before_by_id.get(new_clip.clip_id)
        if old_clip is None:
            added_ids.append(new_clip.clip_id)
            affected_indices.append(idx)
            changes.append(f"Added clip '{new_clip.source_filename or new_clip.clip_id}' at position {idx + 1}")
            continue

        old_sig = _clip_content_signature(
            old_clip, global_grade=before.color_grade, effects=before.cinematic_effects
        )
        new_sig = _clip_content_signature(
            new_clip, global_grade=after.color_grade, effects=after.cinematic_effects
        )
        if old_sig != new_sig or before.aspect_ratio != after.aspect_ratio or before.fps != after.fps:
            modified_ids.append(new_clip.clip_id)
            affected_indices.append(idx)
            deltas = _describe_clip_delta(old_clip, new_clip)
            if deltas:
                changes.extend(deltas)
        elif abs(old_clip.timeline_start_seconds - new_clip.timeline_start_seconds) > 0.02:
            shifted_ids.append(new_clip.clip_id)
        else:
            unchanged_ids.append(new_clip.clip_id)

    for rem_id in removed_ids:
        rem = before_by_id[rem_id]
        changes.append(f"Removed clip '{rem.source_filename or rem_id}'")

    before_order = [c.clip_id for c in before.video_clips if c.clip_id in after_by_id]
    after_order = [c.clip_id for c in after.video_clips if c.clip_id in before_by_id]
    if before_order != after_order:
        changes.append("Reordered timeline clip sequence")

    if before.aspect_ratio != after.aspect_ratio:
        changes.append(f"Changed aspect ratio: {before.aspect_ratio} -> {after.aspect_ratio}")
    if before.color_grade != after.color_grade:
        changes.append(f"Changed color grade: {before.color_grade} -> {after.color_grade}")
    if before.cinematic_effects.vignette != after.cinematic_effects.vignette:
        changes.append(f"{'Enabled' if after.cinematic_effects.vignette else 'Disabled'} vignette")
    if before.cinematic_effects.film_grain != after.cinematic_effects.film_grain:
        changes.append(f"{'Enabled' if after.cinematic_effects.film_grain else 'Disabled'} film grain")
    if before.cinematic_effects.ken_burns_on_images != after.cinematic_effects.ken_burns_on_images:
        changes.append(
            f"{'Enabled' if after.cinematic_effects.ken_burns_on_images else 'Disabled'} Ken Burns motion"
        )
    if subtitles_changed:
        changes.append(f"Updated subtitles ({len(before.subtitles)} -> {len(after.subtitles)} cue(s))")
    if audio_changed:
        changes.append("Updated background audio track cues")

    if not changes and shifted_ids:
        changes.append(f"Shifted {len(shifted_ids)} downstream clip(s)")

    return TimelineDiffSummary(
        added_clip_ids=added_ids,
        removed_clip_ids=removed_ids,
        modified_clip_ids=modified_ids,
        shifted_clip_ids=shifted_ids,
        unchanged_clip_ids=unchanged_ids,
        global_visual_changed=global_visual_changed,
        subtitles_changed=subtitles_changed,
        audio_changed=audio_changed,
        affected_segment_indices=affected_indices,
        changes=list(dict.fromkeys(changes)),
    )

