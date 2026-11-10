"""Audio beat analysis, Librosa tempo/waveform endpoints, and beat-synchronized cut alignment."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.api.database import get_database
from backend.api.schemas import (
    AudioAnalysisResult,
    BeatSyncRequest,
    BeatSyncResponse,
    MediaAsset,
)
from backend.audio_engine.analyzer import analyze_audio_file
from backend.audio_engine.beat_sync import align_timeline_to_beats

router = APIRouter(prefix="/audio", tags=["Audio Intelligence"])


def _ensure_audio_analysis(asset: MediaAsset, *, force_refresh: bool = False) -> MediaAsset:
    """Compute and persist Librosa tempo/beat/waveform analysis when missing or refreshed."""
    if asset.media_kind not in {"audio", "video"}:
        raise HTTPException(status_code=422, detail="Audio analysis requires an audio or video asset.")
    if asset.media_kind == "video" and not asset.metadata.has_audio:
        raise HTTPException(status_code=422, detail="Selected video asset does not contain an audio stream.")

    if asset.audio_analysis is not None and not force_refresh:
        return asset

    file_path = Path(asset.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file missing on disk.")

    try:
        result = analyze_audio_file(file_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to decode audio stream: {exc}") from exc

    tags = list(asset.tags or [])
    if result.tempo_bpm > 0:
        bpm_tag = f"{round(result.tempo_bpm)} BPM"
        if bpm_tag not in tags:
            tags.append(bpm_tag)

    updated = asset.model_copy(update={"audio_analysis": result, "tags": tags})
    return get_database().save_media_asset(updated)


@router.post("/{media_id}/analyze", response_model=MediaAsset)
def analyze_audio_asset(media_id: str) -> MediaAsset:
    """Run Librosa tempo, beat, downbeat, and 64-bar waveform analysis on an audio/video asset."""
    asset = get_database().get_media_asset(media_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found.")
    return _ensure_audio_analysis(asset, force_refresh=True)


@router.get("/{media_id}/analysis", response_model=AudioAnalysisResult)
def get_audio_analysis(media_id: str) -> AudioAnalysisResult:
    """Return cached or freshly computed Librosa audio analysis for an asset."""
    asset = get_database().get_media_asset(media_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found.")
    ensured = _ensure_audio_analysis(asset, force_refresh=False)
    if ensured.audio_analysis is None:
        raise HTTPException(status_code=500, detail="Audio analysis did not return data.")
    return ensured.audio_analysis


@router.post("/beat-sync", response_model=BeatSyncResponse)
def sync_timeline_to_beats(request: BeatSyncRequest) -> BeatSyncResponse:
    """Snap sequential clip transitions toward musical downbeats/beats of the referenced soundtrack."""
    db = get_database()
    audio_asset = db.get_media_asset(request.audio_source_id)
    if not audio_asset:
        raise HTTPException(status_code=404, detail="Audio asset not found.")

    ensured_audio = _ensure_audio_analysis(audio_asset, force_refresh=False)
    analysis = ensured_audio.audio_analysis
    if analysis is None:
        raise HTTPException(status_code=500, detail="Failed to analyze reference audio track.")

    all_assets = {a.id: a for a in db.list_media_assets()}
    aligned_timeline, snapped_cuts, beats_used = align_timeline_to_beats(
        timeline=request.timeline,
        beat_timestamps=analysis.beat_timestamps,
        downbeat_timestamps=analysis.downbeat_timestamps,
        assets_by_id=all_assets,
        tolerance_seconds=request.tolerance_seconds,
    )

    return BeatSyncResponse(
        timeline=aligned_timeline,
        tempo_bpm=analysis.tempo_bpm,
        snapped_cuts=snapped_cuts,
        beat_timestamps_used=beats_used,
    )

