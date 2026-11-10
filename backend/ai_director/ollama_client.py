"""Local Ollama open-weight LLM client for structured AI Director planning."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

import httpx

from backend.api.config import get_settings
from backend.api.schemas import (
    AudioTrackCue,
    ColorGradePreset,
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
from backend.ai_director.sequencer import CandidateSegment

_VALID_ACTS: set[str] = {"Opening Hook", "Rising Action", "Climax", "Emotional Resolution"}
_VALID_TRANSITIONS: set[str] = {
    "none",
    "crossfade",
    "fade_from_black",
    "fade_to_black",
    "slide_left",
    "slide_right",
    "wipe_left",
    "wipe_right",
    "zoom_in",
    "zoom_out",
}
_VALID_GRADES: set[str] = {
    "natural",
    "cinematic_teal_orange",
    "golden_hour",
    "moody_dark",
    "vintage_film",
    "high_contrast_bw",
}


async def check_ollama_status() -> tuple[bool, list[str]]:
    """Probe the configured local Ollama daemon without blocking if offline."""
    settings = get_settings()
    base = settings.OLLAMA_BASE_URL.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(f"{base}/api/tags")
            if res.status_code != 200:
                return False, []
            payload = res.json()
            models = [str(m.get("name", "")) for m in (payload.get("models") or []) if m.get("name")]
            return True, models
    except Exception:
        return False, []


def _extract_json_block(raw_text: str) -> Optional[dict[str, Any]]:
    cleaned = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, flags=re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


async def plan_with_ollama(
    project_id: str,
    instruction: str,
    intent: DirectorIntent,
    candidates: list[CandidateSegment],
    audio_assets: list[MediaAsset],
) -> Optional[tuple[TimelinePlan, list[StoryboardBeat], list[str]]]:
    """Request a structured JSON storyboard from local Ollama; return None on unavailability or invalid schema."""
    if not candidates:
        return None

    settings = get_settings()
    base = settings.OLLAMA_BASE_URL.rstrip("/")

    catalog = [
        {
            "candidate_id": c.candidate_id,
            "filename": c.filename,
            "kind": c.media_kind,
            "duration_seconds": c.raw_duration,
            "quality_score": c.quality_score,
            "motion": c.motion_level,
            "tags": c.tags[:8],
        }
        for c in candidates[:35]
    ]

    system_prompt = (
        "You are CINEFLOW AI Director, an expert cinematic film editor. "
        "Select and order unique clips from the provided JSON media catalog to fulfill the user's creative vision. "
        "STRICT RULES: Never invent candidate_id values; never repeat the same candidate_id; "
        "use valid JSON only with keys: title, color_grade, clips (array of {candidate_id, act, playback_speed, transition_in, rationale})."
    )
    user_payload = {
        "instruction": instruction,
        "parsed_intent": intent.model_dump(),
        "available_media": catalog,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            res = await client.post(
                f"{base}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "stream": False,
                    "format": "json",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(user_payload)},
                    ],
                },
            )
            if res.status_code != 200:
                return None
            data = res.json()
    except Exception:
        return None

    content = ((data.get("message") or {}).get("content") or "") if isinstance(data, dict) else ""
    parsed = _extract_json_block(content)
    if not parsed or not isinstance(parsed.get("clips"), list):
        return None

    cand_by_id = {c.candidate_id: c for c in candidates}
    used_ids: set[str] = set()
    clips: list[MediaClip] = []
    beats: list[StoryboardBeat] = []
    warnings: list[str] = []

    cursor = 0.0
    for item in parsed["clips"]:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("candidate_id", ""))
        cand = cand_by_id.get(cid)
        if not cand or cid in used_ids:
            continue
        used_ids.add(cid)

        if cursor >= intent.target_duration_seconds - 0.3:
            break

        act_raw = str(item.get("act", "Rising Action"))
        act: StoryAct = act_raw if act_raw in _VALID_ACTS else "Rising Action"  # type: ignore[assignment]

        try:
            speed = float(item.get("playback_speed", 1.0))
        except (TypeError, ValueError):
            speed = 1.0
        speed = max(0.5, min(2.0, round(speed, 2)))

        trans_raw = str(item.get("transition_in", "crossfade"))
        trans_in: TransitionType = (
            trans_raw if trans_raw in _VALID_TRANSITIONS else "crossfade"  # type: ignore[assignment]
        )

        eff_dur = min(round(cand.raw_duration / speed, 3), max(0.5, intent.target_duration_seconds - cursor))
        raw_needed = min(cand.raw_duration, round(eff_dur * speed, 3))
        end_s = round(cand.start_seconds + raw_needed, 3)

        overlap = 0.4 if (clips and trans_in != "none" and eff_dur > 1.2 and cursor > 1.2) else 0.0
        t_start = round(max(0.0, cursor - overlap), 3)

        clip_id = f"dir_clip_{len(clips) + 1:02d}"
        clips.append(
            MediaClip(
                clip_id=clip_id,
                source_id=cand.source_id,
                source_filename=cand.filename,
                source_url=cand.source_url,
                thumbnail_url=cand.thumbnail_url,
                start_time_seconds=cand.start_seconds,
                end_time_seconds=end_s,
                timeline_start_seconds=t_start,
                duration_seconds=eff_dur,
                playback_speed=speed,
                transition_in=TransitionSpec(type=trans_in, duration_seconds=0.4 if trans_in != "none" else 0.0),
                quality_score=cand.quality_score,
                tags=cand.tags,
            )
        )
        beats.append(
            StoryboardBeat(
                beat_index=len(beats) + 1,
                act=act,
                clip_id=clip_id,
                source_id=cand.source_id,
                title=cand.filename,
                start_time_seconds=cand.start_seconds,
                end_time_seconds=end_s,
                duration_seconds=eff_dur,
                playback_speed=speed,
                transition_in=trans_in,
                rationale=str(item.get("rationale") or f"Selected by Ollama ({settings.OLLAMA_MODEL}).")[:280],
            )
        )
        cursor = round(t_start + eff_dur, 3)

    if not clips:
        return None

    grade_raw = str(parsed.get("color_grade", intent.color_grade))
    grade: ColorGradePreset = (
        grade_raw if grade_raw in _VALID_GRADES else intent.color_grade  # type: ignore[assignment]
    )
    title = str(parsed.get("title") or intent.title_suggestion).strip()[:160] or intent.title_suggestion

    actual_dur = round(cursor, 2)
    if actual_dur + 2.0 < intent.target_duration_seconds:
        warnings.append(
            f"Requested {intent.target_duration_seconds:.1f}s, assembled {actual_dur:.1f}s from {len(clips)} unique clip(s) without artificial duplication."
        )

    audio_cues: list[AudioTrackCue] = []
    if audio_assets:
        best_aud = audio_assets[0]
        aud_dur = min(actual_dur, best_aud.metadata.duration_seconds or actual_dur)
        if aud_dur >= 0.5:
            audio_cues.append(
                AudioTrackCue(
                    id="dir_music_01",
                    name=best_aud.original_filename,
                    source_id=best_aud.id,
                    source_url=best_aud.source_url,
                    volume=0.8,
                    start_time_seconds=0.0,
                    timeline_start_seconds=0.0,
                    duration_seconds=round(aud_dur, 3),
                    ducking_enabled=True,
                    duck_volume=0.35,
                )
            )

    subtitles = (
        [
            SubtitleCue(
                id="dir_sub_01",
                start_seconds=0.5,
                end_seconds=min(3.8, round(actual_dur - 0.3, 2)),
                text=title,
                style="bold_center_reel" if intent.aspect_ratio == "9:16" else "cinematic_gold_bottom",
            )
        ]
        if actual_dur >= 3.0
        else []
    )

    timeline = TimelinePlan(
        version="1.0",
        project_id=project_id,
        title=title,
        aspect_ratio=intent.aspect_ratio,
        target_duration_seconds=max(0.5, actual_dur),
        fps=30,
        color_grade=grade,
        video_clips=clips,
        audio_tracks=audio_cues,
        subtitles=subtitles,
    )
    return timeline, beats, warnings
