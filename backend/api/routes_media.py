"""Media upload, FFprobe inspection, proxy generation, and asset CRUD endpoints."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from backend.api.config import get_settings, utc_now_iso
from backend.api.database import get_database
from backend.api.schemas import MediaAsset, MediaMetadata, MediaUploadResponse
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


async def _ingest_single_upload(upload: UploadFile) -> MediaAsset:
    settings = get_settings()
    db = get_database()

    clean_original = sanitize_filename(upload.filename or "")
    ext, media_kind, mime_type = classify_extension(clean_original)
    media_id, stored_filename = generate_storage_identity(ext)
    dest_path = settings.UPLOAD_DIR / stored_filename

    # Stream file in chunks while checking header magic bytes and enforcing size limits
    first_chunk = await upload.read(64)
    verify_magic_bytes(first_chunk, ext)

    total_bytes = len(first_chunk)
    validate_file_size(total_bytes)

    try:
        with dest_path.open("wb") as out_file:
            out_file.write(first_chunk)
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                validate_file_size(total_bytes)
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
    return db.save_media_asset(asset)


@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media_batch(files: list[UploadFile] = File(...)) -> MediaUploadResponse:
    """Upload one or more video, image, or audio files with validation, probing, and proxies."""
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
            asset = await _ingest_single_upload(f)
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


@router.get("", response_model=list[MediaAsset])
def list_media(kind: Optional[str] = Query(default=None, pattern="^(video|image|audio)$")) -> list[MediaAsset]:
    """List ingested media assets ordered by upload time."""
    return get_database().list_media_assets(media_kind=kind)


@router.get("/{media_id}", response_model=MediaAsset)
def get_media(media_id: str) -> MediaAsset:
    """Return metadata and URLs for a specific media asset."""
    asset = get_database().get_media_asset(media_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found.")
    return asset


@router.delete("/{media_id}")
def delete_media(media_id: str) -> dict[str, str]:
    """Delete an uploaded media asset along with its generated proxy and thumbnail."""
    asset = get_database().delete_media_asset(media_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found.")

    settings = get_settings()
    for path_str in (asset.file_path, asset.proxy_path):
        if path_str:
            Path(path_str).unlink(missing_ok=True)
    thumb_path = settings.PROXY_DIR / f"{media_id}_thumb.jpg"
    thumb_path.unlink(missing_ok=True)
    return {"status": "deleted", "id": media_id}

