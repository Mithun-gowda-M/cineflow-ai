"""Librosa-powered beat tracking, tempo estimation, waveform peaks, and silence analysis."""

from __future__ import annotations

import tempfile
from pathlib import Path

import librosa
import numpy as np

from backend.api.config import utc_now_iso
from backend.api.schemas import AudioAnalysisResult
from backend.video_engine.ffmpeg_runner import FFmpegExecutionError, run_ffmpeg_sync


def _extract_waveform_bars(y: np.ndarray, num_bars: int = 64) -> list[float]:
    if y.size == 0:
        return [0.1] * num_bars
    chunks = np.array_split(np.abs(y), num_bars)
    raw = np.array([float(np.sqrt(np.mean(c * c))) if c.size else 0.0 for c in chunks], dtype=np.float64)
    peak = float(np.max(raw))
    if peak <= 1e-6:
        return [0.1] * num_bars
    norm = raw / peak
    return [round(float(max(0.08, min(1.0, v))), 3) for v in norm]


def _load_audio_mono(file_path: Path, sr: int = 22050) -> tuple[np.ndarray, int]:
    """Decode WAV/FLAC/OGG directly, or decode MP4/MP3/AAC via FFmpeg to temp mono WAV."""
    ext = file_path.suffix.lower()
    if ext in {".wav", ".flac", ".ogg"}:
        y, actual_sr = librosa.load(str(file_path), sr=sr, mono=True)
        return y, int(actual_sr)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_wav = Path(tmp.name)

    try:
        run_ffmpeg_sync(
            [
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(file_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                str(sr),
                "-f",
                "wav",
                str(tmp_wav),
            ],
            timeout=60,
        )
        y, actual_sr = librosa.load(str(tmp_wav), sr=sr, mono=True)
        return y, int(actual_sr)
    except FFmpegExecutionError:
        y, actual_sr = librosa.load(str(file_path), sr=sr, mono=True)
        return y, int(actual_sr)
    finally:
        tmp_wav.unlink(missing_ok=True)


def analyze_audio_file(file_path: Path) -> AudioAnalysisResult:
    """Analyze audio tempo (BPM), beats, downbeats, waveform bars, and silence ratio."""
    y, sr = _load_audio_mono(file_path, sr=22050)
    duration_sec = round(float(len(y) / float(sr)) if sr > 0 else 0.0, 3)

    if y.size < sr // 4 or float(np.max(np.abs(y))) < 1e-5:
        return AudioAnalysisResult(
            tempo_bpm=0.0,
            duration_seconds=duration_sec,
            beat_timestamps=[],
            downbeat_timestamps=[],
            energy_peaks=[],
            waveform_peaks=[0.08] * 64,
            silence_ratio=1.0,
            analyzed_at=utc_now_iso(),
        )

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo_raw, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    tempo_val = float(np.atleast_1d(tempo_raw)[0]) if tempo_raw is not None else 0.0
    beat_times = [round(float(t), 3) for t in librosa.frames_to_time(beat_frames, sr=sr)]
    downbeats = [beat_times[i] for i in range(0, len(beat_times), 4)]

    # Top RMS energy peaks spaced >= 1.5s apart
    rms = librosa.feature.rms(y=y)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
    ranked_indices = np.argsort(-rms)
    energy_peaks: list[float] = []
    for idx in ranked_indices:
        t = round(float(rms_times[idx]), 3)
        if all(abs(t - existing) >= 1.5 for existing in energy_peaks):
            energy_peaks.append(t)
        if len(energy_peaks) >= 8:
            break
    energy_peaks.sort()

    # Silence ratio using 40dB below peak threshold
    non_silent = librosa.effects.split(y, top_db=40)
    active_samples = sum(int(end - start) for start, end in non_silent)
    silence_ratio = round(max(0.0, min(1.0, 1.0 - (active_samples / float(len(y))))), 3)

    return AudioAnalysisResult(
        tempo_bpm=round(tempo_val, 1),
        duration_seconds=duration_sec,
        beat_timestamps=beat_times,
        downbeat_timestamps=downbeats,
        energy_peaks=energy_peaks,
        waveform_peaks=_extract_waveform_bars(y, num_bars=64),
        silence_ratio=silence_ratio,
        analyzed_at=utc_now_iso(),
    )

