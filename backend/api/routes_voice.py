"""Voice transcription, microphone blob ingestion, and Whisper auto-captioning routes."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from backend.api.config import get_settings
from backend.api.database import get_database
from backend.api.schemas import (
    SubtitleStyle,
    TranscriptionResponse,
    WhisperStatusResponse,
)
from backend.audio_engine.transcriber import (
    WhisperUnavailableError,
    get_whisper_status,
    transcribe_audio_file,
)
from backend.video_engine.ffmpeg_runner import FFmpegExecutionError

router = APIRouter(prefix="/voice", tags=["Voice & Speech-to-Text"])

_ALLOWED_VOICE_EXTENSIONS = {
    ".wav",
    ".webm",
    ".ogg",
    ".mp3",
    ".m4a",
    ".aac",
    ".flac",
    ".mp4",
    ".mov",
}
_MAX_VOICE_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB voice recording guard


def _transcribe_asset_by_id(
    media_id: str,
    *,
    language: Optional[str] = None,
    style: SubtitleStyle = "cinematic_gold_bottom",
) -> TranscriptionResponse:
    asset = get_database().get_media_asset(media_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found.")
    if asset.media_kind == "image":
        raise HTTPException(status_code=422, detail="Cannot extract speech from a static image.")
    if asset.media_kind == "video" and not asset.metadata.has_audio:
        raise HTTPException(status_code=422, detail="Selected video contains no audio stream.")
    target_path = Path(asset.file_path)
    if not target_path.is_file():
        raise HTTPException(status_code=404, detail="Source media file missing on disk.")
    try:
        return transcribe_audio_file(target_path, language=language, style=style)
    except WhisperUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FFmpegExecutionError as exc:
        raise HTTPException(status_code=422, detail=f"Audio decoding failed: {exc}") from exc


@router.get("/status", response_model=WhisperStatusResponse)
def voice_engine_status() -> WhisperStatusResponse:
    """Report faster-whisper and FFmpeg availability for local voice commands & auto-subtitles."""
    return get_whisper_status()


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_voice_or_media(
    file: Optional[UploadFile] = File(default=None),
    media_id: Optional[str] = Form(default=None),
    language: Optional[str] = Form(default=None),
    style: SubtitleStyle = Form(default="cinematic_gold_bottom"),
) -> TranscriptionResponse:
    """Transcribe either a recorded microphone upload or an ingested asset via local Whisper."""
    if file is None and not media_id:
        raise HTTPException(status_code=400, detail="Provide either an audio file upload or a media_id.")

    if media_id:
        return _transcribe_asset_by_id(media_id, language=language, style=style)

    assert file is not None
    raw_name = Path(file.filename or "recording.webm").name
    ext = Path(raw_name).suffix.lower() or ".webm"
    if ext not in _ALLOWED_VOICE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported voice format '{ext}'.")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded voice recording is empty.")
    if len(payload) > _MAX_VOICE_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Voice recording exceeds 50 MB limit.")

    tmp_path = get_settings().CACHE_DIR / f"voice_{uuid.uuid4().hex[:10]}{ext}"
    try:
        tmp_path.write_bytes(payload)
        return transcribe_audio_file(tmp_path, language=language, style=style)
    except WhisperUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FFmpegExecutionError as exc:
        raise HTTPException(status_code=422, detail=f"Audio decoding failed: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/subtitles/{media_id}", response_model=TranscriptionResponse)
def transcribe_asset_to_subtitles(
    media_id: str,
    style: SubtitleStyle = Query(default="cinematic_gold_bottom"),
    language: Optional[str] = Query(default=None),
) -> TranscriptionResponse:
    """Transcribe dialogue from an ingested video/audio asset directly into SubtitleCue records."""
    return _transcribe_asset_by_id(media_id, language=language, style=style)
