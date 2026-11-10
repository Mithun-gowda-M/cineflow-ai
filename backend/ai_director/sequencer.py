"""Deterministic 4-act narrative clip sequencer with strict anti-duplication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.api.schemas import (
    AudioTrackCue,
    DirectorIntent,
    MediaAsset,
    MediaClip,
    StoryAct,
    StoryboardBeat,
    SubtitleCue,
    TimelinePlan,
    TransitionSpec,
    TransitionType,
)


@dataclass
class CandidateSegment:
    """Selectable visual unit (either a PySceneDetect scene or full asset)."""

    candidate_id: str
    source_id: str
    filename: str
    source_url: str
    thumbnail_url: Optional[str]
    media_kind: str
    start_seconds: float
    end_seconds: float
    quality_score: float
    sharpness_score: float
    motion_level: str
    tags: list[str]
    is_duplicate: bool

    @property
    def raw_duration(self) -> float:
        return max(0.5, round(self.end_seconds - self.start_seconds, 3))


def extract_candidates(assets: list[MediaAsset]) -> tuple[list[CandidateSegment], list[MediaAsset], list[str]]:
    """Convert analyzed media assets into ranked visual candidates + audio assets."""
    warnings: list[str] = []
    visual_candidates: list[CandidateSegment] = []
    audio_assets: list[MediaAsset] = []

    for asset in assets:
        if asset.media_kind == "audio":
            audio_assets.append(asset)
            continue

        is_dup = bool(asset.analysis and asset.analysis.duplicate_of_id)
        overall_q = asset.analysis.quality.overall_score if asset.analysis else 75.0
        sharp_q = asset.analysis.quality.sharpness_score if asset.analysis else 75.0
        motion = asset.analysis.quality.motion_intensity if asset.analysis else "static"

        if asset.media_kind == "image":
            visual_candidates.append(
                CandidateSegment(
                    candidate_id=asset.id,
                    source_id=asset.id,
                    filename=asset.original_filename,
                    source_url=asset.source_url,
                    thumbnail_url=asset.thumbnail_url,
                    media_kind="image",
                    start_seconds=0.0,
                    end_seconds=4.0,
                    quality_score=overall_q,
                    sharpness_score=sharp_q,
                    motion_level="static",
                    tags=list(asset.tags),
                    is_duplicate=is_dup,
                )
            )
            continue

        # Video asset: prefer detected sub-scenes when available
        usable_scenes = [s for s in asset.scenes if s.duration_seconds >= 0.6]
        if usable_scenes:
            for sc in usable_scenes:
                merged_tags = list(dict.fromkeys([*asset.tags, *sc.tags]))
                visual_candidates.append(
                    CandidateSegment(
                        candidate_id=sc.scene_id,
                        source_id=asset.id,
                        filename=f"{asset.original_filename} (Scene {sc.scene_index})",
                        source_url=asset.source_url,
                        thumbnail_url=sc.thumbnail_url or asset.thumbnail_url,
                        media_kind="video",
                        start_seconds=sc.start_seconds,
                        end_seconds=sc.end_seconds,
                        quality_score=sc.quality_score,
                        sharpness_score=sc.sharpness_score,
                        motion_level=sc.motion_level,
                        tags=merged_tags,
                        is_duplicate=is_dup,
                    )
                )
        else:
            dur = max(1.0, asset.metadata.duration_seconds or 4.0)
            visual_candidates.append(
                CandidateSegment(
                    candidate_id=asset.id,
                    source_id=asset.id,
                    filename=asset.original_filename,
                    source_url=asset.source_url,
                    thumbnail_url=asset.thumbnail_url,
                    media_kind="video",
                    start_seconds=0.0,
                    end_seconds=round(dur, 3),
                    quality_score=overall_q,
                    sharpness_score=sharp_q,
                    motion_level=motion,
                    tags=list(asset.tags),
                    is_duplicate=is_dup,
                )
            )

    # Filter out perceptual near-duplicates first; only retain if zero primary shots exist
    non_dups = [c for c in visual_candidates if not c.is_duplicate]
    if non_dups:
        excluded_dup_count = len(visual_candidates) - len(non_dups)
        if excluded_dup_count > 0:
            warnings.append(f"Excluded {excluded_dup_count} near-duplicate shot(s) automatically.")
        visual_candidates = non_dups

    # Prefer sharp, non-shaky shots unless total pool is scarce
    clean_shots = [
        c
        for c in visual_candidates
        if c.quality_score >= 38.0 and "Blurry" not in c.tags and c.motion_level != "shaky"
    ]
    if clean_shots:
        skipped = len(visual_candidates) - len(clean_shots)
        if skipped > 0:
            warnings.append(f"Filtered out {skipped} low-quality/blurry or shaky segment(s).")
        visual_candidates = clean_shots

    return visual_candidates, audio_assets, warnings


def _act_affinity(cand: CandidateSegment, act: StoryAct, intent: DirectorIntent) -> float:
    tags_lower = {t.lower() for t in cand.tags}
    name_lower = cand.filename.lower()
    score = cand.quality_score * 0.65

    # Theme keyword alignment
    for kw in intent.theme_keywords:
        if kw in tags_lower or kw in name_lower:
            score += 12.0

    if act == "Opening Hook":
        if any(t in tags_lower for t in ("diya", "establishing", "landscape", "golden-warm")):
            score += 26.0
        if cand.motion_level in {"static", "smooth"}:
            score += 10.0
        if intent.outro_style == "emotional" and any(t in tags_lower for t in ("emotional", "sunset")):
            score -= 16.0
    elif act == "Climax":
        climax_terms = set(intent.climax_keywords) | {"fireworks", "action", "celebration", "high-fps"}
        if any(t in tags_lower or t in name_lower for t in climax_terms):
            score += 28.0
        if cand.motion_level == "action":
            score += 12.0
    elif act == "Emotional Resolution":
        if any(t in tags_lower or t in name_lower for t in ("sunset", "emotional", "portrait", "people", "golden-warm")):
            score += 25.0
        if cand.motion_level in {"static", "smooth"}:
            score += 8.0
    else:  # Rising Action
        if any(t in tags_lower for t in ("people", "group", "rangoli", "celebration", "travel")):
            score += 14.0

    return score


def _speed_and_transition_for_act(
    act: StoryAct,
    intent: DirectorIntent,
    is_first: bool,
    is_last: bool,
) -> tuple[float, TransitionType, Optional[TransitionType], str]:
    if is_first:
        speed = 0.8 if intent.intro_style == "slow_dramatic" else (1.15 if intent.pacing == "fast" else 1.0)
        rationale = (
            "Slow dramatic opening hook to establish mood and draw viewer focus."
            if intent.intro_style == "slow_dramatic"
            else "High-quality opening establishing shot."
        )
        t_out: Optional[TransitionType] = "fade_to_black" if is_last else None
        return speed, "fade_from_black", t_out, rationale

    if act == "Climax":
        speed = 1.25 if (intent.pacing == "fast" or intent.climax_keywords) else 1.0
        trans: TransitionType = "zoom_in" if intent.climax_keywords else "wipe_left"
        t_out = "fade_to_black" if is_last else None
        return speed, trans, t_out, "High-energy climax beat matched to dynamic motion/highlights."

    if act == "Emotional Resolution" or is_last:
        speed = 0.8 if intent.outro_style == "emotional" or intent.pacing == "slow" else 1.0
        trans = "crossfade"
        t_out = "fade_to_black" if is_last else None
        rationale = "Warm, unhurried closing beat for an emotional landing." if speed < 1.0 else "Clean narrative resolution."
        return speed, trans, t_out, rationale

    speed = 1.15 if intent.pacing == "fast" else 1.0
    return speed, "crossfade", None, "Rising narrative momentum maintaining visual variety."


def build_rule_based_storyboard(
    project_id: str,
    intent: DirectorIntent,
    candidates: list[CandidateSegment],
    audio_assets: list[MediaAsset],
    initial_warnings: Optional[list[str]] = None,
) -> tuple[TimelinePlan, list[StoryboardBeat], list[str]]:
    """Assemble a 4-act storyboard and `TimelinePlan` deterministically without duplicating footage."""
    warnings = list(initial_warnings or [])
    if not candidates:
        raise ValueError("No usable video or image footage available to generate an editing plan.")

    remaining = list(candidates)
    selected_acts: list[tuple[StoryAct, CandidateSegment]] = []
    target_dur = intent.target_duration_seconds

    # Determine act sequence budget based on number of unique segments
    n = len(remaining)
    if n == 1:
        selected_acts.append(("Opening Hook", remaining.pop(0)))
    elif n == 2:
        hook = max(remaining, key=lambda c: _act_affinity(c, "Opening Hook", intent))
        remaining.remove(hook)
        outro = remaining.pop(0)
        selected_acts.extend([("Opening Hook", hook), ("Emotional Resolution", outro)])
    else:
        # Reserve Climax and Emotional Resolution anchors before selecting Opening Hook
        climax = max(remaining, key=lambda c: _act_affinity(c, "Climax", intent))
        remaining.remove(climax)

        outro = max(remaining, key=lambda c: _act_affinity(c, "Emotional Resolution", intent))
        remaining.remove(outro)

        hook = max(remaining, key=lambda c: _act_affinity(c, "Opening Hook", intent))
        remaining.remove(hook)

        # Remaining items go into Rising Action (sorted by affinity), then place Climax -> Outro
        rising = sorted(remaining, key=lambda c: _act_affinity(c, "Rising Action", intent), reverse=True)
        selected_acts.append(("Opening Hook", hook))
        for r in rising:
            selected_acts.append(("Rising Action", r))
        selected_acts.append(("Climax", climax))
        selected_acts.append(("Emotional Resolution", outro))

    # Build MediaClips while strictly respecting target duration without duplicating clips
    clips: list[MediaClip] = []
    storyboard: list[StoryboardBeat] = []
    cursor = 0.0
    used_intervals: set[tuple[str, float, float]] = set()

    for idx, (act, cand) in enumerate(selected_acts):
        if cursor >= target_dur - 0.3:
            break

        interval_key = (cand.source_id, round(cand.start_seconds, 2), round(cand.end_seconds, 2))
        if interval_key in used_intervals:
            continue
        used_intervals.add(interval_key)

        is_first = len(clips) == 0
        is_last = idx == len(selected_acts) - 1

        speed, trans_in, trans_out, rationale = _speed_and_transition_for_act(
            act, intent, is_first, is_last
        )

        # In fast climax cuts, cap overly long clips cleanly unless target_duration requires full length
        raw_avail = cand.raw_duration
        max_clip_raw = raw_avail
        if act == "Climax" and intent.climax_keywords and raw_avail > 5.0 and target_dur <= 90.0:
            max_clip_raw = 4.5

        remaining_budget = max(0.5, target_dur - cursor)
        eff_dur = min(round(max_clip_raw / speed, 3), remaining_budget)
        if eff_dur < 0.6:
            break

        raw_needed = round(min(raw_avail, eff_dur * speed), 3)
        clip_end = round(cand.start_seconds + raw_needed, 3)

        overlap = 0.4 if (not is_first and trans_in != "none" and eff_dur > 1.2 and cursor > 1.2) else 0.0
        timeline_start = round(max(0.0, cursor - overlap), 3)

        clip_id = f"dir_clip_{len(clips) + 1:02d}"
        clips.append(
            MediaClip(
                clip_id=clip_id,
                source_id=cand.source_id,
                source_filename=cand.filename,
                source_url=cand.source_url,
                thumbnail_url=cand.thumbnail_url,
                start_time_seconds=cand.start_seconds,
                end_time_seconds=clip_end,
                timeline_start_seconds=timeline_start,
                duration_seconds=eff_dur,
                playback_speed=speed,
                transition_in=TransitionSpec(type=trans_in, duration_seconds=0.4 if trans_in != "none" else 0.0),
                transition_out=(
                    TransitionSpec(type=trans_out, duration_seconds=0.5) if trans_out else None
                ),
                quality_score=cand.quality_score,
                tags=cand.tags,
            )
        )
        storyboard.append(
            StoryboardBeat(
                beat_index=len(storyboard) + 1,
                act=act,
                clip_id=clip_id,
                source_id=cand.source_id,
                title=cand.filename,
                start_time_seconds=cand.start_seconds,
                end_time_seconds=clip_end,
                duration_seconds=eff_dur,
                playback_speed=speed,
                transition_in=trans_in,
                rationale=f"{rationale} (Quality: {cand.quality_score:.0f}/100)",
            )
        )

        cursor = round(timeline_start + eff_dur, 3)

    # Ensure final clip closes cleanly with fade_to_black if emotional/cinematic
    if clips and clips[-1].transition_out is None and intent.outro_style == "emotional":
        clips[-1] = clips[-1].model_copy(
            update={"transition_out": TransitionSpec(type="fade_to_black", duration_seconds=0.6)}
        )

    actual_duration = round(cursor, 2)
    if actual_duration + 2.0 < target_dur:
        warnings.append(
            f"Requested {target_dur:.1f}s, assembled {actual_duration:.1f}s from {len(clips)} unique source clip(s) "
            "without artificial duplication."
        )

    # Background music selection
    audio_cues: list[AudioTrackCue] = []
    if audio_assets:
        best_audio = audio_assets[0]
        aud_dur = min(actual_duration, best_audio.metadata.duration_seconds or actual_duration)
        if aud_dur >= 0.5:
            audio_cues.append(
                AudioTrackCue(
                    id="dir_music_01",
                    name=best_audio.original_filename,
                    source_id=best_audio.id,
                    source_url=best_audio.source_url,
                    volume=0.8,
                    start_time_seconds=0.0,
                    timeline_start_seconds=0.0,
                    duration_seconds=round(aud_dur, 3),
                    ducking_enabled=True,
                    duck_volume=0.35,
                )
            )

    subtitles: list[SubtitleCue] = []
    if actual_duration >= 3.0:
        subtitles.append(
            SubtitleCue(
                id="dir_sub_01",
                start_seconds=0.5,
                end_seconds=min(3.8, round(actual_duration - 0.3, 2)),
                text=intent.title_suggestion,
                style="bold_center_reel" if intent.aspect_ratio == "9:16" else "cinematic_gold_bottom",
            )
        )

    timeline = TimelinePlan(
        version="1.0",
        project_id=project_id,
        title=intent.title_suggestion,
        aspect_ratio=intent.aspect_ratio,
        target_duration_seconds=max(0.5, actual_duration),
        fps=30,
        color_grade=intent.color_grade,
        video_clips=clips,
        audio_tracks=audio_cues,
        subtitles=subtitles,
    )
    return timeline, storyboard, warnings
