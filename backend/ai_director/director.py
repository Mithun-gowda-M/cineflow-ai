"""AI Director orchestration combining Ollama LLM planning with deterministic fallback."""

from __future__ import annotations

from pathlib import Path

from backend.ai_director.intent_parser import parse_director_instruction
from backend.ai_director.ollama_client import check_ollama_status, plan_with_ollama
from backend.ai_director.sequencer import build_rule_based_storyboard, extract_candidates
from backend.ai_director.validator import validate_and_sanitize_timeline
from backend.api.database import get_database
from backend.api.schemas import (
    DirectorPlanRequest,
    DirectorPlanResponse,
    MediaAsset,
)
from backend.audio_engine.analyzer import analyze_audio_file
from backend.audio_engine.beat_sync import align_timeline_to_beats


class DirectorNoFootageError(ValueError):
    """Raised when the user requests an AI Director cut with zero usable visual media."""


async def generate_director_plan(request: DirectorPlanRequest) -> DirectorPlanResponse:
    """Parse creative prompt, generate storyboard & timeline, and validate safety constraints."""
    db = get_database()
    all_assets = db.list_media_assets()

    if request.media_ids:
        requested_set = set(request.media_ids)
        assets = [a for a in all_assets if a.id in requested_set]
    else:
        assets = all_assets

    if not assets:
        raise DirectorNoFootageError("No ingested media assets found. Upload videos or images first.")

    intent = parse_director_instruction(
        request.instruction,
        duration_override=request.target_duration_seconds,
        aspect_override=request.aspect_ratio,
    )

    candidates, audio_assets, extract_warnings = extract_candidates(assets)
    if not candidates:
        raise DirectorNoFootageError(
            "No video or image assets available in the selected media pool (only audio tracks found)."
        )

    assets_by_id: dict[str, MediaAsset] = {a.id: a for a in assets}
    engine_used = "rule_fallback"
    plan_warnings = list(extract_warnings)
    timeline = None
    storyboard = None

    if request.use_llm:
        ollama_ok, _models = await check_ollama_status()
        if ollama_ok:
            llm_result = await plan_with_ollama(
                project_id=request.project_id,
                instruction=request.instruction,
                intent=intent,
                candidates=candidates,
                audio_assets=audio_assets,
            )
            if llm_result is not None:
                raw_tl, raw_beats, llm_warnings = llm_result
                try:
                    timeline, storyboard, val_warnings = validate_and_sanitize_timeline(
                        raw_tl, raw_beats, assets_by_id
                    )
                    plan_warnings.extend(llm_warnings)
                    plan_warnings.extend(val_warnings)
                    engine_used = "ollama"
                except ValueError:
                    timeline = None

    if timeline is None or storyboard is None:
        raw_tl, raw_beats, rule_warnings = build_rule_based_storyboard(
            project_id=request.project_id,
            intent=intent,
            candidates=candidates,
            audio_assets=audio_assets,
            initial_warnings=plan_warnings,
        )
        timeline, storyboard, val_warnings = validate_and_sanitize_timeline(
            raw_tl, raw_beats, assets_by_id
        )
        plan_warnings = [*rule_warnings, *val_warnings]
        engine_used = "rule_fallback"

    if request.beat_sync and timeline.audio_tracks:
        primary_audio_id = timeline.audio_tracks[0].source_id
        audio_asset = assets_by_id.get(primary_audio_id)
        if audio_asset is not None:
            audio_analysis = audio_asset.audio_analysis
            if audio_analysis is None and Path(audio_asset.file_path).is_file():
                try:
                    audio_analysis = analyze_audio_file(Path(audio_asset.file_path))
                    updated_audio = audio_asset.model_copy(update={"audio_analysis": audio_analysis})
                    db.save_media_asset(updated_audio)
                    assets_by_id[primary_audio_id] = updated_audio
                except Exception:
                    audio_analysis = None
            if audio_analysis is not None and (
                audio_analysis.beat_timestamps or audio_analysis.downbeat_timestamps
            ):
                timeline, snapped_cuts, _beats_used = align_timeline_to_beats(
                    timeline=timeline,
                    beat_timestamps=audio_analysis.beat_timestamps,
                    downbeat_timestamps=audio_analysis.downbeat_timestamps,
                    assets_by_id=assets_by_id,
                )
                if snapped_cuts > 0:
                    plan_warnings.append(
                        f"Beat-synced {snapped_cuts} cut transition(s) to {round(audio_analysis.tempo_bpm)} BPM music."
                    )

    return DirectorPlanResponse(
        engine_used=engine_used,  # type: ignore[arg-type]
        intent=intent,
        storyboard=storyboard,
        timeline=timeline,
        warnings=list(dict.fromkeys(plan_warnings)),
    )

