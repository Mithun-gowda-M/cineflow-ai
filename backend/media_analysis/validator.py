"""Upload validation, magic-byte inspection, and path-traversal defense."""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Literal

from backend.api.config import get_settings

MediaKind = Literal["video", "image", "audio"]

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg"}

ALLOWED_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS | AUDIO_EXTENSIONS

MIME_BY_EXTENSION = {
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".aac": "audio/aac",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
}


class MediaValidationError(ValueError):
    """Raised when an uploaded file fails security, extension, or magic-byte checks."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def sanitize_filename(raw_name: str) -> str:
    """Strip any directory traversal components and unsafe characters from a user filename."""
    if not raw_name or "\x00" in raw_name:
        raise MediaValidationError("Invalid filename.", status_code=400)

    # Reject explicit path traversal attempts before stripping
    normalized = raw_name.replace("\\", "/")
    if ".." in normalized.split("/"):
        raise MediaValidationError("Path traversal sequences are forbidden.", status_code=400)

    base = Path(normalized).name.strip()
    if not base:
        raise MediaValidationError("Filename cannot be empty.", status_code=400)

    clean = re.sub(r"[^A-Za-z0-9._\- ]+", "_", base)
    return clean[:180]


def classify_extension(filename: str) -> tuple[str, MediaKind, str]:
    """Validate file extension and return `(ext, media_kind, mime_type)`."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise MediaValidationError(
            f"Unsupported file extension '{ext or '(none)'}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            status_code=415,
        )

    if ext in VIDEO_EXTENSIONS:
        kind: MediaKind = "video"
    elif ext in IMAGE_EXTENSIONS:
        kind = "image"
    else:
        kind = "audio"

    return ext, kind, MIME_BY_EXTENSION[ext]


def verify_magic_bytes(header: bytes, ext: str) -> None:
    """Verify file header bytes match the declared extension family."""
    if len(header) < 4:
        raise MediaValidationError("File is empty or truncated.", status_code=400)

    if ext in {".jpg", ".jpeg"}:
        if not header.startswith(b"\xff\xd8\xff"):
            raise MediaValidationError("File signature does not match JPEG format.", status_code=415)
        return

    if ext == ".png":
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise MediaValidationError("File signature does not match PNG format.", status_code=415)
        return

    if ext == ".webp":
        if not (header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP"):
            raise MediaValidationError("File signature does not match WebP format.", status_code=415)
        return

    if ext in {".mp4", ".mov", ".m4v", ".m4a"}:
        if len(header) < 8 or header[4:8] not in {b"ftyp", b"moov", b"mdat", b"wide", b"free"}:
            raise MediaValidationError("File signature does not match ISO BMFF (MP4/MOV) format.", status_code=415)
        return

    if ext in {".mkv", ".webm"}:
        if not header.startswith(b"\x1a\x45\xdf\xa3"):
            raise MediaValidationError("File signature does not match EBML (MKV/WebM) format.", status_code=415)
        return

    if ext in {".avi", ".wav"}:
        if not header.startswith(b"RIFF"):
            raise MediaValidationError("File signature does not match RIFF (AVI/WAV) format.", status_code=415)
        return

    if ext == ".flac":
        if not header.startswith(b"fLaC"):
            raise MediaValidationError("File signature does not match FLAC format.", status_code=415)
        return

    if ext == ".ogg":
        if not header.startswith(b"OggS"):
            raise MediaValidationError("File signature does not match Ogg format.", status_code=415)
        return

    if ext == ".mp3":
        is_id3 = header.startswith(b"ID3")
        is_sync = header[0] == 0xFF and (header[1] & 0xE0) == 0xE0
        if not (is_id3 or is_sync):
            raise MediaValidationError("File signature does not match MP3 format.", status_code=415)
        return

    if ext == ".aac":
        is_adts = header[0] == 0xFF and (header[1] & 0xF0) == 0xF0
        is_adif = header.startswith(b"ADIF")
        if not (is_adts or is_adif):
            raise MediaValidationError("File signature does not match AAC format.", status_code=415)


def generate_storage_identity(ext: str) -> tuple[str, str]:
    """Generate a collision-free UUID media ID and safe internal filename."""
    media_id = f"media_{uuid.uuid4().hex[:12]}"
    stored_filename = f"{media_id}{ext}"
    return media_id, stored_filename


def validate_file_size(byte_count: int) -> None:
    """Enforce maximum single-file upload size limit."""
    settings = get_settings()
    if byte_count <= 0:
        raise MediaValidationError("Uploaded file is empty.", status_code=400)
    max_bytes = settings.MAX_UPLOAD_FILE_MB * 1024 * 1024
    if byte_count > max_bytes:
        raise MediaValidationError(
            f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_FILE_MB} MB.",
            status_code=413,
        )

