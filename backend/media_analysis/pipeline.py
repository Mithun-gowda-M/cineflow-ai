"""Unified AI Media Intelligence pipeline and natural-language clip search engine."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, Optional

from backend.api.config import utc_now_iso
from backend.api.database import get_database
from backend.api.schemas import (
    AudioAnalysisResult,
    DetectedScene,
    MediaAnalysisResult,
    MediaAsset,
    MediaKind,
    MediaMetadata,
    QualityBreakdown,
)
from backend.audio_engine.analyzer import analyze_audio_file
from backend.media_analysis.cv_analyzer import analyze_image_file, analyze_video_segment
from backend.media_analysis.deduplicator import (
    compute_media_dhash,
    find_best_duplicate_match,
)
from backend.media_analysis.probe import probe_media_file
from backend.media_analysis.proxy import generate_thumbnail, generate_video_proxy
from backend.media_analysis.scene_detector import detect_video_scenes
from backend.media_analysis.scoring import compute_quality_breakdown
from backend.media_analysis.tagger import generate_semantic_tags
from backend.media_analysis.validator import MediaValidationError

_STOP_WORDS = {
    "find",
    "show",
    "get",
    "me",
    "the",
    "most",
    "best",
    "top",
    "clips",
    "clip",
    "shots",
    "shot",
    "videos",
    "video",
    "photos",
    "photo",
    "images",
    "with",
    "for",
    "of",
    "and",
    "all",
}


def analyze_media_asset(asset: MediaAsset, *, existing_assets: Optional[list[MediaAsset]] = None) -> MediaAsset:
    """Run full CV analysis, scene splitting, semantic tagging, and duplicate detection on an asset."""
    db = get_database()
    file_path = Path(asset.file_path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Source media file missing on disk: {file_path}")

    existing = existing_assets if existing_assets is not None else db.list_media_assets()

    if asset.media_kind == "audio":
        audio_analysis: Optional[AudioAnalysisResult] = None
        bpm_tags = ["Audio", "Soundtrack"]
        try:
            audio_analysis = analyze_audio_file(file_path)
            if audio_analysis.tempo_bpm > 0:
                bpm_tags.append(f"{round(audio_analysis.tempo_bpm)} BPM")
        except Exception:
            audio_analysis = None

        breakdown = QualityBreakdown(
            sharpness_score=100.0,
            exposure_score=100.0,
            stability_score=100.0,
            composition_score=100.0,
            overall_score=95.0,
            explanation=(
                f"Audio analyzed via Librosa ({audio_analysis.tempo_bpm:.1f} BPM, "
                f"{len(audio_analysis.beat_timestamps)} beats); ready for tempo & mix alignment."
                if audio_analysis and audio_analysis.tempo_bpm > 0
                else "Audio stream verified via FFprobe; ready for tempo & mix alignment."
            ),
        )
        analysis = MediaAnalysisResult(
            quality=breakdown,
            semantic_tags=bpm_tags,
            analyzed_at=utc_now_iso(),
        )
        updated = asset.model_copy(
            update={
                "analysis": analysis,
                "audio_analysis": audio_analysis,
                "tags": ["audio", *(tag for tag in bpm_tags if tag.lower() != "audio")],
                "scenes": [],
            }
        )
        return db.save_media_asset(updated)

    is_image = asset.media_kind == "image"
    if is_image:
        metrics = analyze_image_file(file_path)
        scenes: list[DetectedScene] = []
    else:
        metrics = analyze_video_segment(file_path, max_samples=10)
        scenes = detect_video_scenes(
            video_path=file_path,
            media_id=asset.id,
            original_filename=asset.original_filename,
            metadata=asset.metadata,
        )

    breakdown = compute_quality_breakdown(metrics, is_image=is_image)
    semantic_tags = generate_semantic_tags(
        asset.original_filename,
        asset.metadata,
        metrics,
        is_image=is_image,
    )

    dhash = compute_media_dhash(file_path, is_image=is_image)
    dup_id, similarity = find_best_duplicate_match(asset.id, dhash, existing)

    merged_tags: list[str] = []
    for t in [asset.media_kind, *semantic_tags]:
        if t not in merged_tags:
            merged_tags.append(t)
    if dup_id and "Near-Duplicate" not in merged_tags:
        merged_tags.append("Near-Duplicate")

    analysis = MediaAnalysisResult(
        quality=breakdown,
        semantic_tags=semantic_tags,
        perceptual_hash=dhash,
        duplicate_of_id=dup_id,
        similarity_percent=similarity,
        analyzed_at=utc_now_iso(),
    )

    updated = asset.model_copy(
        update={
            "tags": merged_tags,
            "analysis": analysis,
            "scenes": scenes,
        }
    )
    return db.save_media_asset(updated)


def search_and_rank_media(
    assets: list[MediaAsset],
    *,
    query: str = "",
    tag: Optional[str] = None,
    min_quality: float = 0.0,
    exclude_duplicates: bool = False,
    sort_by: Literal["auto", "quality", "sharpness", "brightness"] = "auto",
) -> list[MediaAsset]:
    """Filter and rank media assets by natural query keywords, semantic tags, and quality metrics."""
    raw_tokens = [t for t in re.split(r"[^a-z0-9]+", query.lower()) if t]
    search_terms = [t for t in raw_tokens if t not in _STOP_WORDS]

    # Infer sort preference from natural-language modifiers when sort_by == "auto"
    effective_sort = sort_by
    if effective_sort == "auto":
        if any(w in raw_tokens for w in ("brightest", "bright", "sunny", "luminous")):
            effective_sort = "brightness"
        elif any(w in raw_tokens for w in ("sharpest", "sharp", "crisp", "focused")):
            effective_sort = "sharpness"
        else:
            effective_sort = "quality"

    scored: list[tuple[float, MediaAsset]] = []
    for asset in assets:
        quality = asset.analysis.quality.overall_score if asset.analysis else 70.0
        sharpness = asset.analysis.quality.sharpness_score if asset.analysis else 70.0
        brightness = asset.analysis.quality.mean_luminance if asset.analysis else 128.0
        is_dup = bool(asset.analysis and asset.analysis.duplicate_of_id)

        if quality < min_quality:
            continue
        if exclude_duplicates and is_dup:
            continue
        if tag and tag.lower() != "all":
            if not any(t.lower() == tag.lower() for t in asset.tags):
                continue

        # Keyword relevance matching against tags, filename, explanation, and scene tags
        relevance = 0.0
        if search_terms:
            haystack = " ".join(
                [
                    asset.original_filename.lower(),
                    " ".join(t.lower() for t in asset.tags),
                    asset.analysis.quality.explanation.lower() if asset.analysis else "",
                    " ".join(st.lower() for sc in asset.scenes for st in sc.tags),
                ]
            )
            matched = sum(1 for term in search_terms if term in haystack)
            if matched == 0:
                continue
            relevance = (matched / len(search_terms)) * 100.0

        metric_score = (
            brightness if effective_sort == "brightness" else sharpness if effective_sort == "sharpness" else quality
        )
        rank_key = relevance * 2.0 + metric_score
        scored.append((rank_key, asset))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [asset for _, asset in scored]


def finalize_local_media_ingest(
    *,
    dest_path: Path,
    media_id: str,
    original_filename: str,
    stored_filename: str,
    media_kind: MediaKind,
    mime_type: str,
    total_bytes: int,
    owner_id: Optional[str] = None,
    run_analysis: bool = True,
    cleanup_on_probe_error: bool = True,
) -> MediaAsset:
    """Probe media on disk, generate thumbnail/proxy, persist SQLite row, and optionally run CV/Audio analysis."""
    db = get_database()
    try:
        metadata: MediaMetadata = probe_media_file(dest_path, is_image=(media_kind == "image"))
    except Exception as exc:
        if cleanup_on_probe_error:
            dest_path.unlink(missing_ok=True)
        raise MediaValidationError(f"Failed to probe media stream: {exc}", status_code=422) from exc

    thumbnail_url: Optional[str] = None
    proxy_url: Optional[str] = None
    proxy_path_str: Optional[str] = None

    if media_kind in {"video", "image"}:
        thumb_path = generate_thumbnail(
            dest_path,
            media_id,
            metadata.duration_seconds,
            is_image=(media_kind == "image"),
        )
        if thumb_path:
            thumbnail_url = f"/static/proxies/{thumb_path.name}"

    if media_kind == "video":
        proxy_path = generate_video_proxy(dest_path, media_id, metadata.has_audio)
        if proxy_path:
            proxy_path_str = str(proxy_path)
            proxy_url = f"/static/proxies/{proxy_path.name}"

    tags = [media_kind]
    if metadata.width and metadata.height:
        tags.append("portrait" if metadata.height > metadata.width else "landscape")
    if metadata.fps >= 50:
        tags.append("high-fps")

    asset = MediaAsset(
        id=media_id,
        owner_id=owner_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        media_kind=media_kind,
        mime_type=mime_type,
        file_size_bytes=total_bytes,
        file_path=str(dest_path),
        source_url=f"/static/uploads/{stored_filename}",
        thumbnail_url=thumbnail_url,
        proxy_url=proxy_url,
        proxy_path=proxy_path_str,
        metadata=metadata,
        tags=tags,
        created_at=utc_now_iso(),
    )
    saved = db.save_media_asset(asset)
    if run_analysis:
        saved = analyze_media_asset(saved)
    return saved

