"""FastAPI routes for Copyright-Safe Trend Intelligence and Original Style Recipes."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.api.config import get_settings
from backend.api.database import get_database
from backend.api.schemas import (
    StyleAnalyzeUrlRequest,
    StyleApplyRequest,
    StyleApplyResponse,
    StyleRecipe,
)
from backend.media_analysis.validator import (
    MediaValidationError,
    classify_extension,
    sanitize_filename,
    verify_magic_bytes,
)
from backend.trend_intelligence.recipe_generator import (
    apply_style_recipe_to_timeline,
    create_recipe_from_url_pattern,
    create_recipe_from_video,
    ensure_builtin_recipes_seeded,
)
from backend.trend_intelligence.safety import TrendSafetyError

router = APIRouter(prefix="/trends", tags=["Trend Intelligence & Style Recipes"])


@router.get("/recipes", response_model=list[StyleRecipe])
def list_recipes() -> list[StyleRecipe]:
    """List curated studio recipes and user-analyzed style blueprints."""
    return ensure_builtin_recipes_seeded()


@router.get("/recipes/{recipe_id}", response_model=StyleRecipe)
def get_recipe(recipe_id: str) -> StyleRecipe:
    ensure_builtin_recipes_seeded()
    recipe = get_database().get_style_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Style recipe not found.")
    return recipe


@router.post("/analyze-media/{media_id}", response_model=StyleRecipe)
def analyze_ingested_reference_media(
    media_id: str,
    recipe_name: Optional[str] = Form(default=None),
) -> StyleRecipe:
    """Extract abstract editing telemetry from an already-uploaded local video asset."""
    asset = get_database().get_media_asset(media_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found.")
    if asset.media_kind != "video":
        raise HTTPException(status_code=422, detail="Reference style analysis requires a video asset.")

    file_path = Path(asset.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Reference video missing on disk.")

    return create_recipe_from_video(
        file_path,
        recipe_name=recipe_name,
        reference_label=asset.original_filename,
        metadata=asset.metadata,
    )


@router.post("/analyze-upload", response_model=StyleRecipe)
async def analyze_ephemeral_reference_upload(
    file: UploadFile = File(...),
    recipe_name: Optional[str] = Form(default=None),
) -> StyleRecipe:
    """Analyze a temporary reference clip and delete raw video bytes immediately after extraction."""
    settings = get_settings()
    try:
        clean_name = sanitize_filename(file.filename or "reference.mp4")
        ext, kind, _mime = classify_extension(clean_name)
    except MediaValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    if kind != "video":
        raise HTTPException(status_code=422, detail="Reference style analyzer accepts video files only.")

    payload = await file.read()
    max_bytes = settings.MAX_UPLOAD_FILE_MB * 1024 * 1024
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded reference clip is empty.")
    if len(payload) > max_bytes:
        raise HTTPException(status_code=413, detail="Reference upload exceeds configured size limit.")

    try:
        verify_magic_bytes(payload[:32], ext)
    except MediaValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    tmp_ref = settings.CACHE_DIR / f"trend_ref_{uuid.uuid4().hex[:10]}{ext}"
    try:
        tmp_ref.write_bytes(payload)
        return create_recipe_from_video(
            tmp_ref,
            recipe_name=recipe_name,
            reference_label=clean_name,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to analyze reference video: {exc}") from exc
    finally:
        # Strict copyright & privacy policy: never retain raw uploaded reference frames
        tmp_ref.unlink(missing_ok=True)


@router.post("/analyze-url", response_model=StyleRecipe)
def analyze_safe_reference_url(request: StyleAnalyzeUrlRequest) -> StyleRecipe:
    """Derive a style recipe from a public URL pattern & descriptors without downloading media."""
    try:
        return create_recipe_from_url_pattern(request)
    except TrendSafetyError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/recipes/{recipe_id}/apply", response_model=StyleApplyResponse)
def apply_recipe_to_timeline(recipe_id: str, request: StyleApplyRequest) -> StyleApplyResponse:
    """Apply an abstract StyleRecipe onto the active timeline and record revision history."""
    ensure_builtin_recipes_seeded()
    db = get_database()
    recipe = db.get_style_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Style recipe not found.")

    assets_by_id = {a.id: a for a in db.list_media_assets()}
    return apply_style_recipe_to_timeline(recipe, request, assets_by_id)


@router.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: str) -> dict[str, str]:
    ensure_builtin_recipes_seeded()
    deleted, was_builtin = get_database().delete_style_recipe(recipe_id)
    if was_builtin:
        raise HTTPException(status_code=403, detail="Curated built-in style recipes cannot be deleted.")
    if not deleted:
        raise HTTPException(status_code=404, detail="Style recipe not found.")
    return {"status": "deleted", "id": recipe_id}

