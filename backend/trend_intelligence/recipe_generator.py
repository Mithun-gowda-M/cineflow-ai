"""Original abstract style recipe generator, curated studio presets, and timeline style applier."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from backend.ai_director.diff_engine import compute_timeline_diff
from backend.ai_director.intent_parser import parse_director_instruction
from backend.api.config import utc_now_iso
from backend.api.database import get_database
from backend.api.schemas import (
    AspectRatio,
    CinematicEffects,
    ColorGradePreset,
    CutCadence,
    MediaAsset,
    MediaClip,
    MediaMetadata,
    MotionProfile,
    PacingStyle,
    SpeedRampPreset,
    StyleAnalyzeUrlRequest,
    StyleApplyRequest,
    StyleApplyResponse,
    StyleRecipe,
    TimelinePlan,
    TransitionSpec,
    TransitionType,
    TrendSafetyAudit,
)
from backend.trend_intelligence.analyzer import analyze_reference_video
from backend.trend_intelligence.safety import validate_safe_reference_url

_BUILTIN_RECIPES: list[dict] = [
    {
        "id": "recipe_bmsit_aftermovie",
        "name": "BMSIT Cultural Fest Aftermovie",
        "description": "High-impact 4-act campus recap curve with teal & orange glow and dynamic climax speed ramps.",
        "cuts_per_minute": 24.0,
        "avg_shot_duration_seconds": 2.5,
        "cut_cadence": "moderate",
        "motion_velocity_score": 68.0,
        "motion_profile": "dynamic_burst",
        "color_mood": "warm_golden",
        "recommended_color_grade": "cinematic_teal_orange",
        "recommended_aspect_ratio": "16:9",
        "recommended_pacing": "dynamic_arc",
        "recommended_speed_ramp": "fast_to_slow",
        "recommended_transition": "crossfade",
        "cinematic_effects": {"vignette": True, "film_grain": False, "ken_burns_on_images": True},
        "dominant_palette": ["#0B0D13", "#E5B869", "#38BDF8"],
        "prompt_hint": "Dynamic 4-act festive aftermovie with dramatic slow hook, rising crowd energy, and climax ramp.",
    },
    {
        "id": "recipe_viral_reel_9x16",
        "name": "Viral 9:16 Rapid Hook Reel",
        "description": "Ultra-fast vertical beat-driven pacing tuned for YouTube Shorts and Instagram Reels.",
        "cuts_per_minute": 44.0,
        "avg_shot_duration_seconds": 1.35,
        "cut_cadence": "rapid",
        "motion_velocity_score": 84.0,
        "motion_profile": "high_velocity",
        "color_mood": "bright",
        "recommended_color_grade": "cinematic_teal_orange",
        "recommended_aspect_ratio": "9:16",
        "recommended_pacing": "fast",
        "recommended_speed_ramp": "slow_to_fast",
        "recommended_transition": "zoom_in",
        "cinematic_effects": {"vignette": False, "film_grain": False, "ken_burns_on_images": True},
        "dominant_palette": ["#38BDF8", "#E5B869", "#11141E"],
        "prompt_hint": "Fast-paced 9:16 vertical reel with rapid cuts and dynamic zoom transitions.",
    },
    {
        "id": "recipe_golden_travelogue",
        "name": "Golden Hour Travelogue",
        "description": "Warm sunset highlights, smooth glide pacing, and atmospheric wide framing.",
        "cuts_per_minute": 16.0,
        "avg_shot_duration_seconds": 3.75,
        "cut_cadence": "moderate",
        "motion_velocity_score": 42.0,
        "motion_profile": "smooth_glide",
        "color_mood": "warm_golden",
        "recommended_color_grade": "golden_hour",
        "recommended_aspect_ratio": "16:9",
        "recommended_pacing": "dynamic_arc",
        "recommended_speed_ramp": "ease_in_out",
        "recommended_transition": "crossfade",
        "cinematic_effects": {"vignette": False, "film_grain": False, "ken_burns_on_images": True},
        "dominant_palette": ["#E5B869", "#B45309", "#1E293B"],
        "prompt_hint": "Warm golden hour visual storytelling with smooth crossfade transitions.",
    },
    {
        "id": "recipe_bleach_docu",
        "name": "Gritty Hackathon Docu-Cut",
        "description": "Anamorphic 21:9 framing with silver-retained bleach bypass contrast and 35mm texture.",
        "cuts_per_minute": 20.0,
        "avg_shot_duration_seconds": 3.0,
        "cut_cadence": "moderate",
        "motion_velocity_score": 61.0,
        "motion_profile": "dynamic_burst",
        "color_mood": "low_light",
        "recommended_color_grade": "bleach_bypass",
        "recommended_aspect_ratio": "21:9",
        "recommended_pacing": "dynamic_arc",
        "recommended_speed_ramp": "fast_to_slow",
        "recommended_transition": "wipe_left",
        "cinematic_effects": {"vignette": True, "film_grain": True, "ken_burns_on_images": True},
        "dominant_palette": ["#111827", "#6B7280", "#F3F4F6"],
        "prompt_hint": "Widescreen bleach bypass documentary style with optical vignette and 35mm film grain.",
    },
    {
        "id": "recipe_vintage_memories",
        "name": "Warm 35mm Nostalgia Recap",
        "description": "Deliberate emotive cut durations with subtle film grain and vintage warm fade transitions.",
        "cuts_per_minute": 12.0,
        "avg_shot_duration_seconds": 4.8,
        "cut_cadence": "deliberate",
        "motion_velocity_score": 28.0,
        "motion_profile": "smooth_glide",
        "color_mood": "balanced",
        "recommended_color_grade": "vintage_film",
        "recommended_aspect_ratio": "16:9",
        "recommended_pacing": "slow",
        "recommended_speed_ramp": "ease_in_out",
        "recommended_transition": "crossfade",
        "cinematic_effects": {"vignette": True, "film_grain": True, "ken_burns_on_images": True},
        "dominant_palette": ["#92400E", "#D97706", "#1F2937"],
        "prompt_hint": "Emotional unhurried vintage 35mm recap with soft dissolves and gentle vignette.",
    },
]


def ensure_builtin_recipes_seeded() -> list[StyleRecipe]:
    """Ensure curated royalty-free baseline style recipes exist in SQLite."""
    db = get_database()
    existing = db.list_style_recipes()
    existing_ids = {r.id for r in existing}
    created_any = False

    for spec in _BUILTIN_RECIPES:
        if spec["id"] in existing_ids:
            continue
        recipe = StyleRecipe(
            id=spec["id"],
            name=spec["name"],
            description=spec["description"],
            source_type="builtin",
            is_builtin=True,
            reference_label="Curated CINEFLOW Preset",
            cuts_per_minute=spec["cuts_per_minute"],
            avg_shot_duration_seconds=spec["avg_shot_duration_seconds"],
            cut_cadence=spec["cut_cadence"],
            motion_velocity_score=spec["motion_velocity_score"],
            motion_profile=spec["motion_profile"],
            color_mood=spec["color_mood"],
            recommended_color_grade=spec["recommended_color_grade"],
            recommended_aspect_ratio=spec["recommended_aspect_ratio"],
            recommended_pacing=spec["recommended_pacing"],
            recommended_speed_ramp=spec["recommended_speed_ramp"],
            recommended_transition=spec["recommended_transition"],
            cinematic_effects=CinematicEffects(**spec["cinematic_effects"]),
            dominant_palette=list(spec["dominant_palette"]),
            prompt_hint=spec["prompt_hint"],
            safety_audit=TrendSafetyAudit(),
            created_at=utc_now_iso(),
        )
        db.save_style_recipe(recipe)
        created_any = True

    return db.list_style_recipes() if created_any else existing


def create_recipe_from_video(
    video_path: Path,
    *,
    recipe_name: Optional[str] = None,
    reference_label: str = "Uploaded Reference Clip",
    metadata: Optional[MediaMetadata] = None,
) -> StyleRecipe:
    """Analyze a local reference clip and generate a clean copyright-safe StyleRecipe."""
    ensure_builtin_recipes_seeded()
    telemetry = analyze_reference_video(video_path, metadata=metadata)
    clean_name = (
        recipe_name.strip()
        if recipe_name and recipe_name.strip()
        else f"Custom {telemetry.recommended_color_grade.replace('_', ' ').title()} ({telemetry.cut_cadence.title()})"
    )
    prompt_hint = (
        f"{telemetry.cut_cadence.capitalize()} {telemetry.recommended_aspect_ratio} edit averaging "
        f"{telemetry.avg_shot_duration_seconds:.1f}s per shot ({telemetry.cuts_per_minute:.0f} cuts/min) "
        f"with {telemetry.recommended_color_grade.replace('_', ' ')} grading and {telemetry.recommended_speed_ramp.replace('_', ' ')} motion curve."
    )

    recipe = StyleRecipe(
        id=f"recipe_{uuid.uuid4().hex[:10]}",
        name=clean_name[:160],
        description=(
            f"Extracted {telemetry.cuts_per_minute:.1f} cuts/min, "
            f"{telemetry.motion_velocity_score:.0f}/100 motion velocity, and {telemetry.color_mood} color mood."
        ),
        source_type="uploaded_reference",
        is_builtin=False,
        reference_label=reference_label[:160],
        cuts_per_minute=telemetry.cuts_per_minute,
        avg_shot_duration_seconds=telemetry.avg_shot_duration_seconds,
        cut_cadence=telemetry.cut_cadence,
        motion_velocity_score=telemetry.motion_velocity_score,
        motion_profile=telemetry.motion_profile,
        color_mood=telemetry.color_mood,
        recommended_color_grade=telemetry.recommended_color_grade,
        recommended_aspect_ratio=telemetry.recommended_aspect_ratio,
        recommended_pacing=telemetry.recommended_pacing,
        recommended_speed_ramp=telemetry.recommended_speed_ramp,
        recommended_transition=telemetry.recommended_transition,
        cinematic_effects=telemetry.cinematic_effects,
        dominant_palette=telemetry.dominant_palette,
        prompt_hint=prompt_hint,
        safety_audit=TrendSafetyAudit(
            copyright_safe=True,
            media_downloaded=False,
            private_scraping_blocked=True,
            raw_frames_retained=False,
            compliance_note="Extracted numeric cut, velocity, and palette rules only; source frames discarded.",
        ),
        created_at=utc_now_iso(),
    )
    return get_database().save_style_recipe(recipe)


def create_recipe_from_url_pattern(request: StyleAnalyzeUrlRequest) -> StyleRecipe:
    """Validate URL safety and derive an original style recipe without downloading external video/audio."""
    ensure_builtin_recipes_seeded()
    cleaned_url, url_hints = validate_safe_reference_url(request.reference_url)
    notes = request.style_notes.strip()
    combined_desc = f"{notes} {'vertical 9:16 fast reel' if url_hints['format_hint'] == 'vertical_short' else ''}".strip()

    parsed_intent = parse_director_instruction(combined_desc or "Create a dynamic cinematic edit")
    lower = combined_desc.lower()

    is_vertical = url_hints["format_hint"] == "vertical_short" or parsed_intent.aspect_ratio == "9:16"
    aspect: AspectRatio = "9:16" if is_vertical else parsed_intent.aspect_ratio
    pacing: PacingStyle = "fast" if is_vertical or parsed_intent.pacing == "fast" else parsed_intent.pacing
    grade: ColorGradePreset = (
        "bleach_bypass"
        if "bleach" in lower
        else parsed_intent.color_grade
    )

    if pacing == "fast":
        cuts_pm, avg_shot, cadence, vel, m_prof = 38.0, 1.55, "rapid", 78.0, "high_velocity"
        ramp: SpeedRampPreset = "slow_to_fast"
        trans: TransitionType = "zoom_in"
    elif pacing == "slow":
        cuts_pm, avg_shot, cadence, vel, m_prof = 12.0, 4.8, "deliberate", 30.0, "smooth_glide"
        ramp = "ease_in_out"
        trans = "crossfade"
    else:
        cuts_pm, avg_shot, cadence, vel, m_prof = 22.0, 2.7, "moderate", 58.0, "dynamic_burst"
        ramp = "fast_to_slow"
        trans = "crossfade"

    vignette = "vignette" in lower or grade in {"moody_dark", "bleach_bypass"}
    grain = "grain" in lower or grade in {"vintage_film", "bleach_bypass"}

    name = (
        request.recipe_name.strip()
        if request.recipe_name and request.recipe_name.strip()
        else f"{url_hints['domain']} ({aspect} {cadence.title()})"
    )

    recipe = StyleRecipe(
        id=f"recipe_{uuid.uuid4().hex[:10]}",
        name=name[:160],
        description=(
            f"Zero-download style blueprint derived for {url_hints['domain']} "
            f"({cuts_pm:.0f} cuts/min, {grade.replace('_', ' ')} look)."
        ),
        source_type="url_pattern",
        is_builtin=False,
        reference_label=cleaned_url[:240],
        cuts_per_minute=cuts_pm,
        avg_shot_duration_seconds=avg_shot,
        cut_cadence=cadence,  # type: ignore[arg-type]
        motion_velocity_score=vel,
        motion_profile=m_prof,  # type: ignore[arg-type]
        color_mood=grade,
        recommended_color_grade=grade,
        recommended_aspect_ratio=aspect,
        recommended_pacing=pacing,
        recommended_speed_ramp=ramp,
        recommended_transition=trans,
        cinematic_effects=CinematicEffects(vignette=vignette, film_grain=grain),
        dominant_palette=["#0B0D13", "#E5B869", "#38BDF8"],
        prompt_hint=f"{cadence.capitalize()} {aspect} recipe inspired cleanly without stream download.",
        safety_audit=TrendSafetyAudit(
            copyright_safe=True,
            media_downloaded=False,
            private_scraping_blocked=True,
            raw_frames_retained=False,
            compliance_note="Zero external media downloaded or scraped; only safe URL metadata and abstract rules used.",
        ),
        created_at=utc_now_iso(),
    )
    return get_database().save_style_recipe(recipe)


def apply_style_recipe_to_timeline(
    recipe: StyleRecipe,
    request: StyleApplyRequest,
    assets_by_id: dict[str, MediaAsset],
) -> StyleApplyResponse:
    """Apply abstract pacing, look, transition, and speed-ramp rules safely onto a timeline."""
    db = get_database()
    before = request.timeline
    updated_clips: list[MediaClip] = []
    changes: list[str] = []
    cursor = 0.0

    clip_count = len(before.video_clips)
    for idx, clip in enumerate(before.video_clips):
        asset = assets_by_id.get(clip.source_id)
        max_source = (
            10.0
            if (asset is None or asset.media_kind == "image")
            else max(0.5, float(asset.metadata.duration_seconds or 10.0))
        )

        # Tune shot length gently toward recipe's avg_shot_duration_seconds within asset limits
        desired_dur = max(0.8, min(clip.duration_seconds, recipe.avg_shot_duration_seconds)) if recipe.cut_cadence == "rapid" else clip.duration_seconds
        avail_raw = max(0.5, max_source - clip.start_time_seconds)
        raw_needed = round(min(avail_raw, desired_dur * clip.playback_speed), 3)
        eff_dur = round(max(0.5, raw_needed / clip.playback_speed), 3)
        new_end = round(clip.start_time_seconds + raw_needed, 3)

        # Apply speed ramp selectively onto centerpiece/climax shots (or clip 0 when single-clip)
        apply_ramp: SpeedRampPreset = (
            recipe.recommended_speed_ramp
            if ((idx > 0 and idx == clip_count - 1) or clip_count == 1 or (idx == 1 and clip_count >= 2))
            else clip.speed_ramp
        )
        new_trans = (
            clip.transition_in
            if idx == 0
            else TransitionSpec(type=recipe.recommended_transition, duration_seconds=0.4)
        )
        overlap = 0.4 if (idx > 0 and recipe.recommended_transition != "none" and eff_dur > 1.2 and cursor > 1.0) else 0.0
        t_start = round(max(0.0, cursor - overlap), 3)

        updated_clips.append(
            clip.model_copy(
                update={
                    "timeline_start_seconds": t_start,
                    "end_time_seconds": new_end,
                    "duration_seconds": eff_dur,
                    "speed_ramp": apply_ramp,
                    "transition_in": new_trans,
                }
            )
        )
        cursor = round(t_start + eff_dur, 3)

    updated = before.model_copy(
        update={
            "aspect_ratio": recipe.recommended_aspect_ratio,
            "color_grade": recipe.recommended_color_grade,
            "cinematic_effects": recipe.cinematic_effects.model_copy(),
            "video_clips": updated_clips,
            "target_duration_seconds": max(0.5, round(cursor, 2)),
        }
    )
    changes.append(f"Applied Trend Style Recipe '{recipe.name}'")
    changes.append(
        f"Set LUT '{recipe.recommended_color_grade}', ratio {recipe.recommended_aspect_ratio}, cadence '{recipe.cut_cadence}'"
    )

    diff = compute_timeline_diff(before, updated)

    revision_index = 0
    history_count = 0
    can_undo = False
    can_redo = False

    if request.record_history:
        existing_hist = db.get_project_history(request.project_id)
        if existing_hist.total_revisions == 0:
            db.push_timeline_revision(
                request.project_id,
                before,
                "Initial Timeline",
                compute_timeline_diff(before, before),
            )
        hist = db.push_timeline_revision(
            request.project_id,
            updated,
            f"Style Recipe: {recipe.name}",
            diff,
        )
        revision_index = hist.active_revision_index
        history_count = hist.total_revisions
        can_undo = hist.can_undo
        can_redo = hist.can_redo

    return StyleApplyResponse(
        recipe=recipe,
        timeline=updated,
        diff=diff,
        changes_applied=changes,
        revision_index=revision_index,
        history_count=history_count,
        can_undo=can_undo,
        can_redo=can_redo,
    )

