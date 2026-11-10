"""Unit tests for local Whisper WAV preprocessing, word-level subtitle cue formatting, and offline guards."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.api.schemas import TranscriptSegment, TranscriptWord
from backend.audio_engine.transcriber import (
    WhisperUnavailableError,
    get_whisper_status,
    segments_to_subtitle_cues,
    transcribe_audio_file,
)
from backend.media_analysis.probe import probe_media_file
from tests.conftest import create_synthetic_audio


@dataclass
class _MockWord:
    word: str
    start: float
    end: float
    probability: float = 0.95


@dataclass
class _MockSegment:
    start: float
    end: float
    text: str
    words: list[_MockWord]


@dataclass
class _MockInfo:
    language: str = "en"
    duration: float = 4.2


class _MockWhisperModel:
    def transcribe(self, wav_path: str, **_kwargs):
        # Confirm FFmpeg decoded input to valid 16 kHz mono WAV before model inference
        meta = probe_media_file(Path(wav_path), is_image=False)
        assert meta.sample_rate == 16000
        assert meta.audio_channels == 1

        seg = _MockSegment(
            start=0.2,
            end=3.8,
            text="Welcome to BMSIT cultural fest cinema reel showcase today",
            words=[
                _MockWord("Welcome", 0.2, 0.5),
                _MockWord("to", 0.5, 0.7),
                _MockWord("BMSIT", 0.7, 1.1),
                _MockWord("cultural", 1.1, 1.5),
                _MockWord("fest", 1.5, 1.8),
                _MockWord("cinema", 1.8, 2.2),
                _MockWord("reel", 2.2, 2.6),
                _MockWord("showcase", 2.6, 3.1),
                _MockWord("today", 3.1, 3.8),
            ],
        )
        return [seg], _MockInfo()


def test_whisper_status_and_word_chunking() -> None:
    status = get_whisper_status()
    assert status.package_installed is True
    assert status.ffmpeg_ready is True

    seg = TranscriptSegment(
        id="s1",
        start_seconds=0.0,
        end_seconds=3.0,
        text="One two three four five six seven eight nine",
        words=[
            TranscriptWord(word=w, start_seconds=i * 0.3, end_seconds=(i + 1) * 0.3)
            for i, w in enumerate(["One", "two", "three", "four", "five", "six", "seven", "eight", "nine"])
        ],
    )
    cues = segments_to_subtitle_cues([seg], style="bold_center_reel", max_words_per_cue=5)
    assert len(cues) == 2
    assert cues[0].text == "One two three four five"
    assert cues[1].text == "six seven eight nine"
    assert cues[0].style == "bold_center_reel"


def test_transcribe_audio_file_extracts_16k_wav_and_generates_cues(tmp_path: Path) -> None:
    stereo_wav = create_synthetic_audio(tmp_path / "stereo_input.wav", duration=3.0)
    res = transcribe_audio_file(stereo_wav, style="cinematic_gold_bottom", model_override=_MockWhisperModel())

    assert res.engine == "custom"
    assert res.language == "en"
    assert "BMSIT cultural fest" in res.text
    assert len(res.segments) == 1
    assert len(res.suggested_subtitles) == 2
    assert res.suggested_subtitles[0].end_seconds > res.suggested_subtitles[0].start_seconds


def test_missing_local_whisper_model_raises_clear_unavailable_error(tmp_path: Path, monkeypatch) -> None:
    from backend.api import config as cfg_mod
    from backend.audio_engine import transcriber as tr_mod

    monkeypatch.setenv("WHISPER_MODEL", "nonexistent-local-model-xyz")
    monkeypatch.setenv("WHISPER_LOCAL_FILES_ONLY", "true")
    cfg_mod.get_settings.cache_clear()
    tr_mod._LOADED_MODELS.clear()

    stereo_wav = create_synthetic_audio(tmp_path / "voice.wav", duration=2.0)
    try:
        try:
            transcribe_audio_file(stereo_wav)
            raise AssertionError("Expected WhisperUnavailableError for missing local model")
        except WhisperUnavailableError as exc:
            assert "nonexistent-local-model-xyz" in str(exc)
    finally:
        cfg_mod.get_settings.cache_clear()
        tr_mod._LOADED_MODELS.clear()

