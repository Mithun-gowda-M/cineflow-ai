"""Local faster-whisper speech-to-text transcription and timestamped subtitle cue generator."""

from __future__ import annotations

import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any, Optional

from backend.api.config import get_settings
from backend.api.schemas import (
    SubtitleCue,
    SubtitleStyle,
    TranscriptSegment,
    TranscriptWord,
    TranscriptionResponse,
    WhisperStatusResponse,
)
from backend.video_engine.ffmpeg_runner import (
    FFmpegExecutionError,
    get_binary_info,
    run_ffmpeg_sync,
)

_MODEL_LOCK = threading.Lock()
_LOADED_MODELS: dict[tuple[str, str, str], Any] = {}


class WhisperUnavailableError(RuntimeError):
    """Raised when local Whisper weights or runtime cannot be loaded."""


def _is_model_cached(model_name: str) -> bool:
    if Path(model_name).is_dir():
        return True
    hub_dir = Path.home() / ".cache" / "huggingface" / "hub"
    if not hub_dir.is_dir():
        return False
    repo_folder = hub_dir / f"models--Systran--faster-whisper-{model_name}"
    if not repo_folder.is_dir():
        return False
    return any(repo_folder.rglob("model.bin"))


def get_whisper_status() -> WhisperStatusResponse:
    """Inspect local faster-whisper package, FFmpeg readiness, and cached model availability."""
    settings = get_settings()
    try:
        import faster_whisper  # noqa: F401

        pkg_ok = True
    except ImportError:
        pkg_ok = False

    bin_info = get_binary_info()
    ffmpeg_ready = bool(bin_info.get("ffmpeg_path"))
    cached = _is_model_cached(settings.WHISPER_MODEL)
    ready = pkg_ok and ffmpeg_ready and (cached or not settings.WHISPER_LOCAL_FILES_ONLY)

    if not pkg_ok:
        detail = "faster-whisper is not installed in the backend Python environment."
    elif not cached and settings.WHISPER_LOCAL_FILES_ONLY:
        detail = f"Whisper model '{settings.WHISPER_MODEL}' is not cached locally for strict offline mode."
    elif cached:
        detail = f"Local Whisper '{settings.WHISPER_MODEL}' ({settings.WHISPER_COMPUTE_TYPE}) cached and ready."
    else:
        detail = f"faster-whisper installed; '{settings.WHISPER_MODEL}' will cache locally on first use."

    return WhisperStatusResponse(
        package_installed=pkg_ok,
        model_name=settings.WHISPER_MODEL,
        device=settings.WHISPER_DEVICE,
        compute_type=settings.WHISPER_COMPUTE_TYPE,
        model_cached=cached,
        ready=ready,
        ffmpeg_ready=ffmpeg_ready,
        detail=detail,
    )


def extract_pcm_16k_wav(media_path: Path, out_wav: Path) -> Path:
    """Decode any audio/video stream into 16 kHz mono 16-bit PCM WAV via parameterized FFmpeg."""
    run_ffmpeg_sync(
        [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(media_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            "-f",
            "wav",
            str(out_wav),
        ],
        timeout=90,
    )
    if not out_wav.is_file() or out_wav.stat().st_size <= 44:
        raise FFmpegExecutionError("Decoded audio stream is empty or contains no usable samples.")
    return out_wav


def _get_whisper_model() -> Any:
    settings = get_settings()
    key = (settings.WHISPER_MODEL, settings.WHISPER_DEVICE, settings.WHISPER_COMPUTE_TYPE)
    with _MODEL_LOCK:
        if key in _LOADED_MODELS:
            return _LOADED_MODELS[key]
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise WhisperUnavailableError(
                "faster-whisper is not installed in backend/.venv."
            ) from exc

        try:
            model = WhisperModel(
                settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE,
                local_files_only=settings.WHISPER_LOCAL_FILES_ONLY,
            )
        except Exception as exc:
            raise WhisperUnavailableError(
                f"Could not initialize local Whisper '{settings.WHISPER_MODEL}' model: {exc}"
            ) from exc

        _LOADED_MODELS[key] = model
        return model


def segments_to_subtitle_cues(
    segments: list[TranscriptSegment],
    *,
    style: SubtitleStyle = "cinematic_gold_bottom",
    max_words_per_cue: int = 7,
) -> list[SubtitleCue]:
    """Group timestamped speech words into crisp screen-readable SubtitleCue entries."""
    cues: list[SubtitleCue] = []
    for seg in segments:
        if seg.words:
            for i in range(0, len(seg.words), max_words_per_cue):
                chunk = seg.words[i : i + max_words_per_cue]
                text = " ".join(w.word.strip() for w in chunk if w.word.strip()).strip()
                if not text:
                    continue
                start_s = round(max(0.0, chunk[0].start_seconds), 2)
                end_s = round(max(start_s + 0.4, chunk[-1].end_seconds), 2)
                cues.append(
                    SubtitleCue(
                        id=f"sub_{uuid.uuid4().hex[:8]}",
                        start_seconds=start_s,
                        end_seconds=end_s,
                        text=text,
                        style=style,
                    )
                )
        else:
            clean = seg.text.strip()
            if clean:
                cues.append(
                    SubtitleCue(
                        id=f"sub_{uuid.uuid4().hex[:8]}",
                        start_seconds=round(max(0.0, seg.start_seconds), 2),
                        end_seconds=round(max(seg.start_seconds + 0.5, seg.end_seconds), 2),
                        text=clean,
                        style=style,
                    )
                )
    return cues


def transcribe_audio_file(
    file_path: Path,
    *,
    language: Optional[str] = None,
    style: SubtitleStyle = "cinematic_gold_bottom",
    model_override: Any = None,
) -> TranscriptionResponse:
    """Run local faster-whisper speech-to-text over any audio or video asset."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Audio/video source missing: {file_path}")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_wav = Path(tmp.name)

    try:
        extract_pcm_16k_wav(file_path, tmp_wav)
        model = model_override if model_override is not None else _get_whisper_model()

        raw_segments, info = model.transcribe(
            str(tmp_wav),
            language=language or None,
            beam_size=1,
            word_timestamps=True,
            vad_filter=False,
        )

        segments: list[TranscriptSegment] = []
        full_parts: list[str] = []
        for idx, raw in enumerate(raw_segments):
            txt = str(getattr(raw, "text", "") or "").strip()
            if not txt:
                continue
            s_t = round(float(getattr(raw, "start", 0.0)), 3)
            e_t = round(max(s_t + 0.1, float(getattr(raw, "end", s_t + 0.5))), 3)

            words: list[TranscriptWord] = []
            for w in getattr(raw, "words", None) or []:
                w_txt = str(getattr(w, "word", "") or "").strip()
                if not w_txt:
                    continue
                ws = round(max(0.0, float(getattr(w, "start", s_t))), 3)
                we = round(max(ws, float(getattr(w, "end", e_t))), 3)
                prob = max(0.0, min(1.0, float(getattr(w, "probability", 1.0))))
                words.append(
                    TranscriptWord(
                        word=w_txt,
                        start_seconds=ws,
                        end_seconds=we,
                        probability=round(prob, 3),
                    )
                )

            segments.append(
                TranscriptSegment(
                    id=f"seg_{idx + 1}",
                    start_seconds=s_t,
                    end_seconds=e_t,
                    text=txt,
                    words=words,
                )
            )
            full_parts.append(txt)

        detected_lang = str(getattr(info, "language", None) or language or "en")
        dur_sec = round(float(getattr(info, "duration", 0.0) or 0.0), 3)
        subtitles = segments_to_subtitle_cues(segments, style=style)

        return TranscriptionResponse(
            text=" ".join(full_parts).strip(),
            language=detected_lang,
            duration_seconds=dur_sec,
            engine="custom" if model_override is not None else "faster_whisper",
            segments=segments,
            suggested_subtitles=subtitles,
        )
    finally:
        tmp_wav.unlink(missing_ok=True)
