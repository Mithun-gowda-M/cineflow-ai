"""Conversational timeline editing engine with deterministic parser and optional Ollama assist."""

from __future__ import annotations

import json
import re
import uuid
from typing import Optional

import httpx

from backend.ai_director.diff_engine import compute_timeline_diff
from backend.ai_director.ollama_client import check_ollama_status
from backend.api.config import get_settings
from backend.api.database import get_database
from backend.api.schemas import (
    AspectRatio,
    ColorGradePreset,
    ConversationalEditRequest,
    ConversationalEditResponse,
    MediaAsset,
    MediaClip,
    SpeedRampPreset,
    SubtitleCue,
    TimelinePlan,
    TransitionSpec,
    TransitionType,
)
from backend.audio_engine.analyzer import analyze_audio_file
from backend.audio_engine.beat_sync import align_timeline_to_beats

_ORDINALS = {
    "first": 0,
    "1st": 0,
    "opening": 0,
    "intro": 0,
    "second": 1,
    "2nd": 1,
    "third": 2,
    "3rd": 2,
    "fourth": 3,
    "4th": 3,
    "fifth": 4,
    "5th": 4,
}

_LUT_PATTERNS: list[tuple[tuple[str, ...], ColorGradePreset]] = [
    (("bleach", "gritty", "silver"), "bleach_bypass"),
    (("golden", "warm", "sunset", "festive"), "golden_hour"),
    (("teal", "orange", "blockbuster"), "cinematic_teal_orange"),
    (("moody", "dark", "noir"), "moody_dark"),
    (("vintage", "retro", "sepia"), "vintage_film"),
    (("black and white", "b&w", "monochrome", "grayscale"), "high_contrast_bw"),
    (("natural", "reset grade", "clean color"), "natural"),
]

_TRANSITION_PATTERNS: list[tuple[tuple[str, ...], TransitionType]] = [
    (("hard cut", "no transition", "remove transition"), "none"),
    (("wipe left", "wipe"), "wipe_left"),
    (("wipe right",), "wipe_right"),
    (("slide left", "slide"), "slide_left"),
    (("slide right",), "slide_right"),
    (("zoom in", "zoom"), "zoom_in"),
    (("zoom out",), "zoom_out"),
    (("fade from black",), "fade_from_black"),
    (("fade to black",), "fade_to_black"),
    (("crossfade", "dissolve", "fade"), "crossfade"),
]


def _reflow_timeline(timeline: TimelinePlan) -> TimelinePlan:
    cursor = 0.0
    reflowed: list[MediaClip] = []
    for idx, clip in enumerate(timeline.video_clips):
        overlap = 0.0
        if idx > 0 and clip.transition_in and clip.transition_in.type != "none":
            overlap = min(clip.transition_in.duration_seconds, clip.duration_seconds * 0.45, cursor * 0.45)
        t_start = round(max(0.0, cursor - overlap), 3)
        reflowed.append(clip.model_copy(update={"timeline_start_seconds": t_start}))
        cursor = round(t_start + clip.duration_seconds, 3)

    return timeline.model_copy(
        update={
            "video_clips": reflowed,
            "target_duration_seconds": max(0.5, round(cursor, 2)),
        }
    )


def _resolve_target_indices(lower: str, clips: list[MediaClip]) -> list[int]:
    if not clips:
        return []

    if any(w in lower for w in ("all clips", "every clip", "whole video", "entire timeline")):
        return list(range(len(clips)))

    matches: list[int] = []
    for m in re.finditer(r"(?:clip|shot|segment)\s*#?\s*(\d+)", lower):
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(clips) and idx not in matches:
            matches.append(idx)

    for word, idx in _ORDINALS.items():
        if re.search(rf"\b{re.escape(word)}\b", lower) and 0 <= idx < len(clips) and idx not in matches:
            matches.append(idx)

    if any(w in lower for w in ("last clip", "final clip", "outro", "ending")) and (len(clips) - 1) not in matches:
        matches.append(len(clips) - 1)

    if matches:
        return matches

    # Keyword match against existing clip filenames/tags (when NOT looking after "with ...")
    head = re.split(r"\b(?:with|to|for)\b", lower, maxsplit=1)[0]
    for idx, clip in enumerate(clips):
        haystack = f"{clip.source_filename} {' '.join(clip.tags)}".lower()
        for token in re.findall(r"[a-z]{3,}", head):
            if token not in {"trim", "cut", "make", "clip", "shot", "replace", "swap", "speed", "faster", "slower"}:
                if token in haystack:
                    return [idx]

    return [0]


def _pick_replacement_asset(
    query: str,
    visual_assets: list[MediaAsset],
    used_source_ids: set[str],
    exclude_source_id: str,
) -> Optional[MediaAsset]:
    terms = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if t not in {"the", "a", "an", "with", "clip", "shot", "video", "image"}]
    best_score = -1.0
    best_asset: Optional[MediaAsset] = None

    for asset in visual_assets:
        if asset.id == exclude_source_id:
            continue
        score = asset.analysis.quality.overall_score * 0.25 if asset.analysis else 15.0
        haystack = " ".join(
            [
                asset.original_filename.lower(),
                *(t.lower() for t in asset.tags),
                *(t.lower() for t in (asset.analysis.semantic_tags if asset.analysis else [])),
                *(t.lower() for sc in asset.scenes for t in sc.tags),
            ]
        )
        matched_terms = sum(1 for term in terms if term in haystack)
        score += matched_terms * 40.0
        if asset.id not in used_source_ids:
            score += 12.0
        if asset.analysis and asset.analysis.duplicate_of_id:
            score -= 20.0
        if score > best_score and (matched_terms > 0 or not terms):
            best_score = score
            best_asset = asset

    if best_asset is not None:
        return best_asset

    # Fallback: pick highest-scoring unused visual asset if query terms didn't strictly match
    unused = [a for a in visual_assets if a.id != exclude_source_id and a.id not in used_source_ids]
    pool = unused or [a for a in visual_assets if a.id != exclude_source_id]
    if not pool:
        return None
    return max(pool, key=lambda a: a.analysis.quality.overall_score if a.analysis else 75.0)


def _max_dur_for_asset(asset: Optional[MediaAsset]) -> float:
    if asset is None or asset.media_kind == "image":
        return 10.0
    return max(0.5, float(asset.metadata.duration_seconds or 10.0))


def _clamp_clip_timing(clip: MediaClip, asset: Optional[MediaAsset], new_dur: float, new_speed: float) -> MediaClip:
    speed = round(max(0.25, min(4.0, new_speed)), 2)
    max_raw = _max_dur_for_asset(asset)
    avail_raw = max(0.5, max_raw - clip.start_time_seconds)
    raw_needed = max(0.5, min(avail_raw, new_dur * speed))
    end_t = round(clip.start_time_seconds + raw_needed, 3)
    eff_dur = round(max(0.5, raw_needed / speed), 3)
    return clip.model_copy(
        update={
            "playback_speed": speed,
            "end_time_seconds": end_t,
            "duration_seconds": eff_dur,
        }
    )


async def _try_ollama_edit_summary(instruction: str, timeline: TimelinePlan) -> Optional[dict]:
    """Optional Ollama structured edit extraction; returns validated action dict or None."""
    ok, _models = await check_ollama_status()
    if not ok:
        return None
    settings = get_settings()
    prompt = (
        "Convert this video editing instruction into JSON with optional keys: "
        "color_grade (natural|golden_hour|cinematic_teal_orange|moody_dark|vintage_film|bleach_bypass|high_contrast_bw), "
        "aspect_ratio (16:9|9:16|1:1|4:5|21:9), vignette (bool), film_grain (bool), "
        "speed_multiplier (float), trim_delta_seconds (float), clip_index_1based (int).\n"
        f"Current clips: {[{'idx': i+1, 'name': c.source_filename, 'dur': c.duration_seconds} for i, c in enumerate(timeline.video_clips)]}\n"
        f"Instruction: {instruction}\nReturn JSON only."
    )
    try:
        async with httpx.AsyncClient(timeout=min(6.0, settings.OLLAMA_TIMEOUT_SECONDS)) as client:
            res = await client.post(
                f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
            )
            if res.status_code == 200:
                raw = res.json().get("response", "{}")
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    return parsed
    except Exception:
        return None
    return None


def _apply_deterministic_edit(
    instruction: str,
    timeline: TimelinePlan,
    assets_by_id: dict[str, MediaAsset],
) -> tuple[TimelinePlan, list[str], list[str]]:
    lower = instruction.strip().lower()
    clips = list(timeline.video_clips)
    subtitles = list(timeline.subtitles)
    effects = timeline.cinematic_effects.model_copy()
    color_grade: ColorGradePreset = timeline.color_grade
    aspect_ratio: AspectRatio = timeline.aspect_ratio
    ops: list[str] = []
    warnings: list[str] = []

    visual_assets = [a for a in assets_by_id.values() if a.media_kind in {"video", "image"}]
    targets = _resolve_target_indices(lower, clips)

    # 1. Remove / Delete clip
    if re.search(r"\b(remove|delete|drop)\s+(?:clip|shot|the\s+\w+\s+clip|last\s+clip)\b", lower) and "subtitle" not in lower and "vignette" not in lower and "grain" not in lower:
        if len(clips) > 1:
            for idx in sorted(set(targets), reverse=True):
                if len(clips) > 1 and 0 <= idx < len(clips):
                    removed = clips.pop(idx)
                    ops.append(f"Removed clip '{removed.source_filename or removed.clip_id}'")
        else:
            warnings.append("Cannot remove the only remaining clip on the timeline.")

    # 2. Reorder / Move clip ("move clip 3 before clip 1" / "swap clip 1 and clip 2")
    swap_pair = re.search(r"swap\s+(?:clip\s*)?(\d+)\s+(?:and|with)\s+(?:clip\s*)?(\d+)", lower)
    move_before = re.search(r"move\s+(?:clip\s*)?(\d+)\s+(?:before|to|in front of)\s+(?:clip\s*)?(\d+)", lower)
    if swap_pair:
        i, j = int(swap_pair.group(1)) - 1, int(swap_pair.group(2)) - 1
        if 0 <= i < len(clips) and 0 <= j < len(clips) and i != j:
            clips[i], clips[j] = clips[j], clips[i]
            ops.append(f"Swapped clip {i + 1} and clip {j + 1}")
    elif move_before:
        src_i, dst_i = int(move_before.group(1)) - 1, int(move_before.group(2)) - 1
        if 0 <= src_i < len(clips) and 0 <= dst_i < len(clips) and src_i != dst_i:
            moved = clips.pop(src_i)
            clips.insert(dst_i if src_i > dst_i else max(0, dst_i - 1), moved)
            ops.append(f"Moved clip {src_i + 1} before clip {dst_i + 1}")

    # 3. Replace clip with another asset ("replace clip 2 with the sunset")
    rep_match = re.search(r"\b(?:replace|swap|change)\b.+?\b(?:with|to|for)\s+(.+)$", lower)
    if rep_match and not swap_pair and "grade" not in lower and "lut" not in lower and "transition" not in lower and "9:16" not in lower and "16:9" not in lower:
        query_tail = rep_match.group(1)
        idx = targets[0] if targets else 0
        if 0 <= idx < len(clips) and visual_assets:
            used_ids = {c.source_id for i, c in enumerate(clips) if i != idx}
            candidate = _pick_replacement_asset(query_tail, visual_assets, used_ids, clips[idx].source_id)
            if candidate is not None:
                old_clip = clips[idx]
                max_dur = _max_dur_for_asset(candidate)
                new_end = round(min(max_dur, max(0.8, old_clip.duration_seconds * old_clip.playback_speed)), 3)
                eff_dur = round(max(0.5, new_end / old_clip.playback_speed), 3)
                clips[idx] = old_clip.model_copy(
                    update={
                        "source_id": candidate.id,
                        "source_filename": candidate.original_filename,
                        "source_url": candidate.source_url,
                        "thumbnail_url": candidate.thumbnail_url,
                        "start_time_seconds": 0.0,
                        "end_time_seconds": new_end,
                        "duration_seconds": eff_dur,
                        "tags": list(candidate.tags),
                    }
                )
                ops.append(f"Replaced clip {idx + 1} with '{candidate.original_filename}'")
            else:
                warnings.append(f"No distinct replacement asset matched '{query_tail.strip()}'.")

    # 4. Trim / Shorten / Extend duration
    trim_by = re.search(r"\b(?:trim|shorten|cut|reduce)\b.+?\bby\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds?)?", lower)
    set_dur = re.search(r"\b(?:set|make)\b.+?\b(?:to|duration)\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds?)\b", lower)
    if trim_by:
        delta = float(trim_by.group(1))
        for idx in targets:
            c = clips[idx]
            clips[idx] = _clamp_clip_timing(c, assets_by_id.get(c.source_id), max(0.5, c.duration_seconds - delta), c.playback_speed)
        ops.append(f"Trimmed {len(targets)} clip(s) by {delta:.1f}s")
    elif set_dur:
        target_len = float(set_dur.group(1))
        for idx in targets:
            c = clips[idx]
            clips[idx] = _clamp_clip_timing(c, assets_by_id.get(c.source_id), target_len, c.playback_speed)
        ops.append(f"Set target duration to {target_len:.1f}s on {len(targets)} clip(s)")

    # 5. Speed & Speed Ramps
    explicit_speed = re.search(r"\b(\d+(?:\.\d+)?)\s*x\b", lower)
    if explicit_speed:
        sp = max(0.25, min(4.0, float(explicit_speed.group(1))))
        for idx in targets:
            c = clips[idx]
            raw_dur = max(0.5, c.end_time_seconds - c.start_time_seconds)
            clips[idx] = _clamp_clip_timing(c, assets_by_id.get(c.source_id), raw_dur / sp, sp)
        ops.append(f"Set playback speed to {sp}x")
    elif any(w in lower for w in ("faster", "speed up", "energetic", "punchy")):
        apply_indices = list(range(len(clips))) if ("cut" in lower or "pace" in lower or "video" in lower) else targets
        for idx in apply_indices:
            c = clips[idx]
            sp = round(min(2.5, c.playback_speed * 1.25), 2)
            raw_dur = max(0.5, c.end_time_seconds - c.start_time_seconds)
            clips[idx] = _clamp_clip_timing(c, assets_by_id.get(c.source_id), max(0.7, (raw_dur / sp)), sp)
        ops.append("Accelerated pacing across clip cut")
    elif any(w in lower for w in ("slower", "slow down", "slow motion", "dramatic")):
        apply_indices = list(range(len(clips))) if ("cut" in lower or "pace" in lower or "video" in lower) else targets
        for idx in apply_indices:
            c = clips[idx]
            sp = round(max(0.5, c.playback_speed * 0.75), 2)
            raw_dur = max(0.5, c.end_time_seconds - c.start_time_seconds)
            clips[idx] = _clamp_clip_timing(c, assets_by_id.get(c.source_id), raw_dur / sp, sp)
        ops.append("Slowed down clip pacing cleanly")

    ramp_choice: Optional[SpeedRampPreset] = None
    if "fast to slow" in lower or "action ramp" in lower:
        ramp_choice = "fast_to_slow"
    elif "slow to fast" in lower:
        ramp_choice = "slow_to_fast"
    elif "ease in out" in lower or "smooth ramp" in lower:
        ramp_choice = "ease_in_out"
    elif "remove speed ramp" in lower or "linear speed" in lower:
        ramp_choice = "none"
    if ramp_choice is not None:
        for idx in targets:
            clips[idx] = clips[idx].model_copy(update={"speed_ramp": ramp_choice})
        ops.append(f"Applied speed ramp '{ramp_choice}'")

    # 6. Transitions
    for keywords, t_val in _TRANSITION_PATTERNS:
        if any(k in lower for k in keywords) and ("transition" in lower or any(k != "fade" for k in keywords)):
            for idx in targets:
                spec = None if t_val == "none" else TransitionSpec(type=t_val, duration_seconds=0.5)
                clips[idx] = clips[idx].model_copy(update={"transition_in": spec})
            ops.append(f"Updated transition to '{t_val}'")
            break

    # 7. Color Grade Preset
    if not rep_match or any(w in lower for w in ("grade", "grading", "lut", "color", "filter", "look", "bleach", "golden", "teal", "moody", "vintage", "monochrome", "black and white")):
        for keywords, preset in _LUT_PATTERNS:
            if any(k in lower for k in keywords):
                color_grade = preset
                ops.append(f"Changed global color grade to '{preset}'")
                break

    # 8. Cinematic Effects toggles
    if "vignette" in lower:
        enable = not any(w in lower for w in ("remove", "disable", "no vignette", "off"))
        effects = effects.model_copy(update={"vignette": enable})
        ops.append(f"{'Enabled' if enable else 'Disabled'} optical vignette")
    if "grain" in lower:
        enable = not any(w in lower for w in ("remove", "disable", "no grain", "off"))
        effects = effects.model_copy(update={"film_grain": enable})
        ops.append(f"{'Enabled' if enable else 'Disabled'} 35mm film grain")
    if "ken burns" in lower or "zoom on image" in lower:
        enable = not any(w in lower for w in ("remove", "disable", "off"))
        effects = effects.model_copy(update={"ken_burns_on_images": enable})
        ops.append(f"{'Enabled' if enable else 'Disabled'} Ken Burns motion")

    # 9. Aspect Ratio
    if any(w in lower for w in ("9:16", "vertical", "reel", "shorts")):
        aspect_ratio = "9:16"
        ops.append("Switched aspect ratio to 9:16 vertical")
    elif any(w in lower for w in ("16:9", "landscape", "youtube")):
        aspect_ratio = "16:9"
        ops.append("Switched aspect ratio to 16:9 landscape")
    elif any(w in lower for w in ("1:1", "square")):
        aspect_ratio = "1:1"
        ops.append("Switched aspect ratio to 1:1 square")
    elif any(w in lower for w in ("21:9", "anamorphic", "cinemascope")):
        aspect_ratio = "21:9"
        ops.append("Switched aspect ratio to 21:9 anamorphic")

    # 10. Subtitles commands
    if "remove subtitles" in lower or "clear subtitles" in lower or "no subtitles" in lower:
        subtitles = []
        ops.append("Cleared all subtitle cues")
    else:
        add_sub = re.search(r"add\s+(?:title|subtitle|caption)\s+['\"]([^'\"]+)['\"]", instruction, flags=re.IGNORECASE)
        if add_sub:
            title_txt = add_sub.group(1).strip()
            subtitles.append(
                SubtitleCue(
                    id=f"sub_{uuid.uuid4().hex[:8]}",
                    start_seconds=0.5,
                    end_seconds=3.5,
                    text=title_txt,
                    style="cinematic_gold_bottom",
                )
            )
            ops.append(f"Added title cue '{title_txt}'")

    updated = timeline.model_copy(
        update={
            "video_clips": clips,
            "subtitles": subtitles,
            "cinematic_effects": effects,
            "color_grade": color_grade,
            "aspect_ratio": aspect_ratio,
        }
    )
    updated = _reflow_timeline(updated)

    # 11. Beat Sync request
    if any(w in lower for w in ("beat sync", "beat-sync", "snap cuts", "sync to beat", "sync to music")):
        if updated.audio_tracks:
            aud_asset = assets_by_id.get(updated.audio_tracks[0].source_id)
            if aud_asset and aud_asset.audio_analysis is None:
                try:
                    from pathlib import Path

                    if Path(aud_asset.file_path).is_file():
                        analysis = analyze_audio_file(Path(aud_asset.file_path))
                        aud_asset = get_database().save_media_asset(aud_asset.model_copy(update={"audio_analysis": analysis}))
                        assets_by_id[aud_asset.id] = aud_asset
                except Exception:
                    pass
            if aud_asset and aud_asset.audio_analysis:
                updated, snapped, _used = align_timeline_to_beats(
                    updated,
                    aud_asset.audio_analysis.beat_timestamps,
                    aud_asset.audio_analysis.downbeat_timestamps,
                    assets_by_id,
                )
                ops.append(f"Beat-synced {snapped} cut transition(s)")

    if not ops:
        warnings.append(
            "No concrete timeline operation recognized. Try commands like 'Replace clip 2 with ...', 'Trim clip 1 by 1s', 'Make it faster', 'Change to golden hour', or 'Add vignette'."
        )

    return updated, ops, warnings


async def apply_conversational_edit(request: ConversationalEditRequest) -> ConversationalEditResponse:
    """Apply an iterative natural-language edit, calculate diff, and persist revision history."""
    db = get_database()
    assets_by_id = {a.id: a for a in db.list_media_assets()}
    before = request.timeline
    engine_used = "rule_fallback"

    llm_patch = await _try_ollama_edit_summary(request.instruction, before) if request.use_llm else None
    updated, ops, warnings = _apply_deterministic_edit(request.instruction, before, assets_by_id)

    if llm_patch and not ops:
        # Apply validated scalar fallback hints from Ollama when regex missed phrasing
        extra_ops: list[str] = []
        valid_grades = {"natural", "golden_hour", "cinematic_teal_orange", "moody_dark", "vintage_film", "bleach_bypass", "high_contrast_bw"}
        if llm_patch.get("color_grade") in valid_grades:
            updated = updated.model_copy(update={"color_grade": llm_patch["color_grade"]})
            extra_ops.append(f"Changed global color grade to '{llm_patch['color_grade']}'")
        if isinstance(llm_patch.get("vignette"), bool):
            eff = updated.cinematic_effects.model_copy(update={"vignette": llm_patch["vignette"]})
            updated = updated.model_copy(update={"cinematic_effects": eff})
            extra_ops.append(f"{'Enabled' if llm_patch['vignette'] else 'Disabled'} optical vignette")
        if extra_ops:
            ops.extend(extra_ops)
            warnings = []
            engine_used = "ollama"

    diff = compute_timeline_diff(before, updated)

    revision_index = 0
    history_count = 0
    can_undo = False
    can_redo = False

    if request.record_history and ops:
        existing_history = db.get_project_history(request.project_id)
        if existing_history.total_revisions == 0:
            init_diff = compute_timeline_diff(before, before)
            db.push_timeline_revision(request.project_id, before, "Initial Timeline", init_diff)
        saved_hist = db.push_timeline_revision(
            request.project_id,
            updated,
            request.instruction,
            diff,
        )
        revision_index = saved_hist.active_revision_index
        history_count = saved_hist.total_revisions
        can_undo = saved_hist.can_undo
        can_redo = saved_hist.can_redo

    return ConversationalEditResponse(
        engine_used=engine_used,  # type: ignore[arg-type]
        instruction=request.instruction,
        timeline=updated,
        diff=diff,
        operations_applied=ops,
        warnings=list(dict.fromkeys(warnings)),
        revision_index=revision_index,
        history_count=history_count,
        can_undo=can_undo,
        can_redo=can_redo,
    )

