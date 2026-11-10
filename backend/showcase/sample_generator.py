"""Procedural Full-HD royalty-free sample media generator for the CINEFLOW AI showcase."""

from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import soundfile as sf

from backend.api.config import get_settings
from backend.video_engine.ffmpeg_runner import resolve_binary


@dataclass(frozen=True)
class SampleClipSpec:
    filename: str
    media_kind: str
    width: int
    height: int
    duration_seconds: float
    fps: int
    role: str
    theme: str


SAMPLE_PACK_SPECS: tuple[SampleClipSpec, ...] = (
    SampleClipSpec(
        filename="01_diya_golden_intro_1080p.mp4",
        media_kind="video",
        width=1920,
        height=1080,
        duration_seconds=4.0,
        fps=24,
        role="Opening Hook — Warm Golden Diya Macro Glow",
        theme="diya_warm",
    ),
    SampleClipSpec(
        filename="02_auditorium_stage_pulse_1080p.mp4",
        media_kind="video",
        width=1920,
        height=1080,
        duration_seconds=4.5,
        fps=24,
        role="Rising Action — BMSIT Cultural Stage & Neon Cut",
        theme="stage_pulse",
    ),
    SampleClipSpec(
        filename="03_fireworks_climax_burst_1080p.mp4",
        media_kind="video",
        width=1920,
        height=1080,
        duration_seconds=4.5,
        fps=24,
        role="Climax Drop — High-Energy Festival Fireworks Burst",
        theme="fireworks",
    ),
    SampleClipSpec(
        filename="04_campus_aerial_portrait_1080p.mp4",
        media_kind="video",
        width=1080,
        height=1920,
        duration_seconds=4.0,
        fps=24,
        role="Vertical B-Roll — Golden Sunset Aerial Sweep (9:16)",
        theme="sunset_portrait",
    ),
    SampleClipSpec(
        filename="05_festival_beat_120bpm.wav",
        media_kind="audio",
        width=0,
        height=0,
        duration_seconds=16.0,
        fps=22050,
        role="Soundtrack Bed — 120 BPM Electronic Festival Pulse",
        theme="audio_120bpm",
    ),
)


def sample_media_dir() -> Path:
    return get_settings().BASE_DIR / "assets" / "sample_media"


def _make_base_grid(width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
    xs = np.linspace(-1.0, 1.0, width, dtype=np.float32)[None, :]
    ys = np.linspace(-1.0, 1.0, height, dtype=np.float32)[:, None]
    return xs, ys


def _render_theme_frame(
    theme: str,
    frame_idx: int,
    total_frames: int,
    width: int,
    height: int,
    xs: np.ndarray,
    ys: np.ndarray,
) -> np.ndarray:
    t = frame_idx / max(total_frames - 1, 1)
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    if theme == "diya_warm":
        # Dark obsidian background with crisp concentric golden lantern glow & sharp geometric frame marks
        cx = 0.08 * math.sin(t * math.pi * 2)
        cy = 0.05 * math.cos(t * math.pi * 2)
        dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        glow = np.exp(-3.2 * dist)
        frame[:, :, 0] = np.clip(18 + 25 * glow, 0, 255).astype(np.uint8)  # B
        frame[:, :, 1] = np.clip(28 + 145 * glow, 0, 255).astype(np.uint8)  # G
        frame[:, :, 2] = np.clip(45 + 210 * glow, 0, 255).astype(np.uint8)  # R
        # Sharp lantern bokeh discs for high Laplacian clarity
        for k in range(7):
            ox = int(width * (0.18 + 0.11 * k + 0.03 * math.sin(t * 4 + k)))
            oy = int(height * (0.28 + 0.42 * ((k * 0.37) % 1.0) - 0.05 * math.cos(t * 3 + k)))
            cv2.circle(frame, (ox, oy), 26 + (k % 3) * 14, (70, 185, 248), -1, lineType=cv2.LINE_AA)
            cv2.circle(frame, (ox, oy), 12 + (k % 2) * 8, (150, 230, 255), -1, lineType=cv2.LINE_AA)
        cv2.putText(
            frame,
            "BMSIT CINEFLOW // OPENING HOOK",
            (96, height - 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.4,
            (180, 225, 255),
            3,
            cv2.LINE_AA,
        )

    elif theme == "stage_pulse":
        # Intentional visual scene cut at midpoint (t >= 0.5) so PySceneDetect splits 2 real scenes!
        if t < 0.5:
            # Scene A: Deep Cyan-Blue auditorium laser sweep
            wave = 0.5 + 0.5 * np.sin(8.0 * xs + t * 14.0)
            frame[:, :, 0] = np.clip(95 + 140 * wave, 0, 255).astype(np.uint8)
            frame[:, :, 1] = np.clip(55 + 115 * wave, 0, 255).astype(np.uint8)
            frame[:, :, 2] = np.clip(18 + 30 * (1.0 - wave), 0, 255).astype(np.uint8)
            for b in range(18):
                bar_h = int(height * (0.18 + 0.52 * abs(math.sin(t * 10 + b * 0.45))))
                x0 = int(width * (0.08 + b * 0.048))
                cv2.rectangle(frame, (x0, height - 140 - bar_h), (x0 + 48, height - 140), (248, 196, 56), -1)
        else:
            # Scene B: Crisp Amber-Crimson cultural stage strobe (dramatic histogram jump)
            rad = np.sqrt(xs**2 + ys**2)
            ring = 0.5 + 0.5 * np.cos(14.0 * rad - t * 22.0)
            frame[:, :, 0] = np.clip(20 + 35 * ring, 0, 255).astype(np.uint8)
            frame[:, :, 1] = np.clip(65 + 120 * ring, 0, 255).astype(np.uint8)
            frame[:, :, 2] = np.clip(150 + 100 * ring, 0, 255).astype(np.uint8)
            for beam in range(5):
                x_top = int(width * (0.15 + beam * 0.175))
                x_bot = int(width * (0.5 + 0.35 * math.sin(t * 9 + beam)))
                cv2.line(frame, (x_top, 40), (x_bot, height - 60), (210, 245, 255), 8, lineType=cv2.LINE_AA)
        cv2.putText(
            frame,
            "LIVE CULTURAL STAGE PULSE // 120 BPM",
            (96, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.35,
            (255, 255, 255),
            3,
            cv2.LINE_AA,
        )

    elif theme == "fireworks":
        # High-contrast night sky with crisp firework radial sparks
        sky_grad = np.clip(15 + 32 * (1.0 - ys), 0, 255).astype(np.uint8)
        frame[:, :, 0] = sky_grad
        frame[:, :, 1] = np.clip(10 + 18 * (1.0 - ys), 0, 255).astype(np.uint8)
        frame[:, :, 2] = np.clip(18 + 20 * (1.0 - ys), 0, 255).astype(np.uint8)
        bursts = [(0.3, 0.36, 0.0, (90, 200, 255)), (0.7, 0.32, 0.35, (255, 190, 75)), (0.5, 0.48, 0.65, (140, 140, 255))]
        for bx, by, phase, col in bursts:
            local_t = (t + phase) % 1.0
            radius = 35 + local_t * 360
            cx_px, cy_px = int(width * bx), int(height * by)
            for ray in range(28):
                ang = (2.0 * math.pi * ray) / 28.0
                px = int(cx_px + radius * math.cos(ang))
                py = int(cy_px + radius * math.sin(ang) + 45 * local_t * local_t)
                cv2.line(frame, (cx_px, cy_px), (px, py), col, 3, lineType=cv2.LINE_AA)
                cv2.circle(frame, (px, py), 8, (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.putText(
            frame,
            "FESTIVAL CLIMAX // FIREWORKS FINALE",
            (96, height - 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.35,
            (130, 215, 255),
            3,
            cv2.LINE_AA,
        )

    else:
        # 1080x1920 Portrait Golden Campus Horizon Panorama
        horizon = 0.5 + 0.5 * np.tanh(-2.8 * (ys - 0.1 + 0.08 * math.sin(t * math.pi * 2)))
        frame[:, :, 0] = np.clip(28 + 90 * (1.0 - horizon), 0, 255).astype(np.uint8)
        frame[:, :, 1] = np.clip(75 + 115 * horizon, 0, 255).astype(np.uint8)
        frame[:, :, 2] = np.clip(145 + 105 * horizon, 0, 255).astype(np.uint8)
        # Campus silhouette roofline & moving sweep reticle
        roof_y = int(height * 0.64)
        cv2.rectangle(frame, (0, roof_y), (width, height), (22, 18, 28), -1)
        for col_idx in range(7):
            bx = int(width * (0.08 + col_idx * 0.135))
            bh = int(120 + 180 * ((col_idx * 0.61) % 1.0))
            cv2.rectangle(frame, (bx, roof_y - bh), (bx + 92, roof_y), (32, 26, 42), -1)
            for row_idx in range(4):
                wy = roof_y - bh + 25 + row_idx * 28
                if wy < roof_y - 14:
                    cv2.rectangle(frame, (bx + 18, wy), (bx + 72, wy + 12), (95, 200, 255), -1)
        cv2.putText(
            frame,
            "BMSIT 9:16 REEL",
            (95, 190),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.6,
            (235, 245, 255),
            3,
            cv2.LINE_AA,
        )

    return frame


def _write_sample_video(spec: SampleClipSpec, out_path: Path, ffmpeg_bin: str) -> None:
    total_frames = max(int(round(spec.duration_seconds * spec.fps)), 24)
    xs, ys = _make_base_grid(spec.width, spec.height)
    freq = 220 if spec.theme == "diya_warm" else 330 if spec.theme == "stage_pulse" else 440

    cmd = [
        ffmpeg_bin,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s",
        f"{spec.width}x{spec.height}",
        "-r",
        str(spec.fps),
        "-i",
        "pipe:0",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={freq}:sample_rate=44100",
        "-t",
        f"{spec.duration_seconds:.2f}",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "24",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-af",
        "volume=0.18",
        "-movflags",
        "+faststart",
        str(out_path),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for idx in range(total_frames):
            frame = _render_theme_frame(
                spec.theme,
                idx,
                total_frames,
                spec.width,
                spec.height,
                xs,
                ys,
            )
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
    except Exception:
        proc.kill()
        raise

    stderr_bytes = proc.stderr.read() if proc.stderr else b""
    ret = proc.wait(timeout=120)
    if ret != 0:
        raise RuntimeError(
            f"Sample video encoding failed for {spec.filename}: {stderr_bytes.decode('utf-8', errors='ignore')}"
        )


def _write_festival_120bpm_wav(out_path: Path, duration_seconds: float = 16.0, sr: int = 22050) -> None:
    """Synthesize a crisp 120 BPM drum + bass + warm harmonic track for Librosa beat verification."""
    n_samples = int(sr * duration_seconds)
    t = np.linspace(0.0, duration_seconds, n_samples, endpoint=False, dtype=np.float32)

    # 120 BPM => 2.0 beats per second => 0.500s beat period
    beat_interval = 0.5
    signal = np.zeros(n_samples, dtype=np.float32)

    # Warm lush festival synth pad chord progression (A minor -> F -> C -> G)
    chords = [
        (220.0, 261.63, 329.63),
        (174.61, 220.0, 261.63),
        (261.63, 329.63, 392.00),
        (196.00, 246.94, 392.00),
    ]
    samples_per_bar = sr * 4
    for bar_idx in range(4):
        start_s = bar_idx * samples_per_bar
        end_s = min(n_samples, (bar_idx + 1) * samples_per_bar)
        t_bar = t[start_s:end_s]
        for freq in chords[bar_idx % len(chords)]:
            signal[start_s:end_s] += 0.085 * np.sin(2.0 * math.pi * freq * t_bar)

    # Sharp punchy 120 BPM kick + crisp hi-hat offbeats for unmistakable beat grid detection
    beat_idx = 0
    while beat_idx * beat_interval < duration_seconds:
        bt = beat_idx * beat_interval
        pos = int(bt * sr)
        kick_len = min(int(0.18 * sr), n_samples - pos)
        if kick_len > 0:
            tk = np.arange(kick_len, dtype=np.float32) / float(sr)
            freq_env = 52.0 + 98.0 * np.exp(-26.0 * tk)
            amp_env = np.exp(-15.0 * tk)
            kick = 0.55 * amp_env * np.sin(2.0 * math.pi * freq_env * tk)
            signal[pos : pos + kick_len] += kick

        # Snare/clap accent on downbeats 2 & 4
        if beat_idx % 2 == 1:
            clap_len = min(int(0.11 * sr), n_samples - pos)
            if clap_len > 0:
                rng = np.random.default_rng(42 + beat_idx)
                tc = np.arange(clap_len, dtype=np.float32) / float(sr)
                noise = rng.normal(0.0, 1.0, clap_len).astype(np.float32)
                signal[pos : pos + clap_len] += 0.24 * np.exp(-28.0 * tc) * noise
        beat_idx += 1

    peak = float(np.max(np.abs(signal))) or 1.0
    normalized = np.clip((signal / peak) * 0.85, -1.0, 1.0).astype(np.float32)
    sf.write(str(out_path), normalized, sr, subtype="PCM_16")


def ensure_sample_media_pack(*, force: bool = False) -> list[Path]:
    """Generate any missing Full-HD showcase clips and beat track into `assets/sample_media/`."""
    out_dir = sample_media_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_bin = resolve_binary("ffmpeg")

    generated_paths: list[Path] = []
    for spec in SAMPLE_PACK_SPECS:
        target = out_dir / spec.filename
        generated_paths.append(target)
        if target.is_file() and target.stat().st_size > 4096 and not force:
            continue
        if spec.media_kind == "audio":
            _write_festival_120bpm_wav(target, duration_seconds=spec.duration_seconds, sr=spec.fps)
        else:
            _write_sample_video(spec, target, ffmpeg_bin)
    return generated_paths


if __name__ == "__main__":
    paths = ensure_sample_media_pack(force=True)
    total_mb = sum(p.stat().st_size for p in paths) / (1024 * 1024)
    print(f"Generated {len(paths)} showcase media files in {sample_media_dir()} ({total_mb:.2f} MB total).")

