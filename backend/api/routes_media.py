"""Media upload, FFprobe inspection, proxy generation, and asset CRUD endpoints."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from backend.api.config import get_settings, utc_now_iso
from backend.api.database import get_database
from backend.api.schemas import (
    DetectedScene,
    MediaAsset,
    MediaMetadata,
    MediaSearchResponse,
    MediaUploadResponse,
    UserPublic,
)
from backend.authentication.quotas import enforce_user_quota
from backend.authentication.security import get_optional_current_user
from backend.media_analysis.pipeline import analyze_media_asset, search_and_rank_media
from backend.media_analysis.probe import probe_media_file
from backend.media_analysis.proxy import generate_thumbnail, generate_video_proxy
from backend.media_analysis.validator import (
    MediaValidationError,
    classify_extension,
    generate_storage_identity,
    sanitize_filename,
    validate_file_size,
    verify_magic_bytes,
)

router = APIRouter(prefix="/media", tags=["Media"])


async def _ingest_single_upload(
    upload: UploadFile,
    *,
    run_analysis: bool = True,
    owner: Optional[UserPublic] = None,
) -> MediaAsset:
    settings = get_settings()
    db = get_database()

    clean_original = sanitize_filename(upload.filename or "")
    ext, media_kind, mime_type = classify_extension(clean_original)
    media_id, stored_filename = generate_storage_identity(ext)
    dest_path = settings.UPLOAD_DIR / stored_filename

    # Stream file in chunks while checking header magic bytes and enforcing size & user quota limits
    first_chunk = await upload.read(64)
    verify_magic_bytes(first_chunk, ext)

    total_bytes = len(first_chunk)
    validate_file_size(total_bytes)
    if owner is not None:
        enforce_user_quota(owner, total_bytes)

    try:
        with dest_path.open("wb") as out_file:
            out_file.write(first_chunk)
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                validate_file_size(total_bytes)
                if owner is not None:
                    enforce_user_quota(owner, total_bytes)
                out_file.write(chunk)
    except Exception:
        if dest_path.exists():
            dest_path.unlink(missing_ok=True)
        raise

    try:
        metadata: MediaMetadata = probe_media_file(dest_path, is_image=(media_kind == "image"))
    except Exception as exc:
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
        owner_id=owner.id if owner else None,
        original_filename=clean_original,
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


@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media_batch(
    files: list[UploadFile] = File(...),
    analyze: bool = Query(default=True),
    current_user: Optional[UserPublic] = Depends(get_optional_current_user),
) -> MediaUploadResponse:
    """Upload one or more video, image, or audio files with probing, proxies, and CV intelligence."""
    settings = get_settings()
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")
    if len(files) > settings.MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Batch exceeds maximum limit of {settings.MAX_BATCH_FILES} files per request.",
        )

    uploaded: list[MediaAsset] = []
    errors: list[dict[str, str]] = []

    for f in files:
        try:
            asset = await _ingest_single_upload(f, run_analysis=analyze, owner=current_user)
            uploaded.append(asset)
        except MediaValidationError as exc:
            # For single-file uploads, surface exact HTTP error status directly
            if len(files) == 1:
                raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
            errors.append({"filename": f.filename or "unknown", "error": str(exc)})
        except Exception as exc:
            if len(files) == 1:
                raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc
            errors.append({"filename": f.filename or "unknown", "error": str(exc)})

    return MediaUploadResponse(uploaded=uploaded, errors=errors)


@router.get("/search", response_model=MediaSearchResponse)
def search_media(
    q: str = Query(default="", max_length=200),
    tag: Optional[str] = Query(default=None),
    min_quality: float = Query(default=0.0, ge=0.0, le=100.0),
    exclude_duplicates: bool = Query(default=False),
    sort_by: Literal["auto", "quality", "sharpness", "brightness"] = Query(default="auto"),
) -> MediaSearchResponse:
    """Search and rank media assets by natural keywords, semantic tags, and CV scores."""
    all_assets = get_database().list_media_assets()
    ranked = search_and_rank_media(
        all_assets,
        query=q,
        tag=tag,
        min_quality=min_quality,
        exclude_duplicates=exclude_duplicates,
        sort_by=sort_by,
    )
    return MediaSearchResponse(query=q, total_matches=len(ranked), results=ranked)


@router.post("/analyze-all", response_model=list[MediaAsset])
def analyze_all_media() -> list[MediaAsset]:
    """Run or refresh Phase 3 CV quality, scene detection, and deduplication on all media assets."""
    db = get_database()
    assets = db.list_media_assets()
    updated: list[MediaAsset] = []
    for asset in assets:
        if Path(asset.file_path).is_file():
            updated.append(analyze_media_asset(asset))
    return updated


@router.get("", response_model=list[MediaAsset])
def list_media(kind: Optional[str] = Query(default=None, pattern="^(video|image|audio)$")) -> list[MediaAsset]:
    """List ingested media assets ordered by upload time."""
    return get_database().list_media_assets(media_kind=kind)


@router.post("/{media_id}/analyze", response_model=MediaAsset)
def analyze_single_media(media_id: str) -> MediaAsset:
    """Run or refresh CV intelligence and PySceneDetect splitting for a single media asset."""
    asset = get_database().get_media_asset(media_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found.")
    return analyze_media_asset(asset)


@router.get("/{media_id}/scenes", response_model=list[DetectedScene])
def get_media_scenes(media_id: str) -> list[DetectedScene]:
    """Return PySceneDetect cut intervals and scores for a specific media asset."""
    db = get_database()
    asset = db.get_media_asset(media_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found.")
    return db.get_detected_scenes(media_id)


@router.get("/{media_id}", response_model=MediaAsset)
def get_media(media_id: str) -> MediaAsset:
    """Return metadata and URLs for a specific media asset."""
    asset = get_database().get_media_asset(media_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found.")
    return asset


@router.delete("/{media_id}")
def delete_media(
    media_id: str,
    current_user: Optional[UserPublic] = Depends(get_optional_current_user),
) -> dict[str, str]:
    """Delete an uploaded media asset along with its generated proxy, thumbnail, and scene crops."""
    db = get_database()
    existing = db.get_media_asset(media_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Media asset not found.")
    if (
        current_user is not None
        and existing.owner_id
        and existing.owner_id != current_user.id
        and current_user.role not in {"admin", "club_lead"}
    ):
        raise HTTPException(status_code=403, detail="Forbidden: cannot delete another student's media asset.")

    asset = db.delete_media_asset(media_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found.")

    settings = get_settings()
    for path_str in (asset.file_path, asset.proxy_path):
        if path_str:
            Path(path_str).unlink(missing_ok=True)
    thumb_path = settings.PROXY_DIR / f"{media_id}_thumb.jpg"
    thumb_path.unlink(missing_ok=True)
    for scene_thumb in settings.PROXY_DIR.glob(f"{media_id}_scene_*.jpg"):
        scene_thumb.unlink(missing_ok=True)
    return {"status": "deleted", "id": media_id}

