"""OpenCV frame quality, motion stability, face visibility, and color palette analyzer."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

import cv2
import numpy as np

MotionLevel = Literal["static", "smooth", "action", "shaky"]
LightingMood = Literal["bright", "warm_golden", "balanced", "low_light"]
SubjectPos = Literal["center", "rule_of_thirds", "wide", "none"]


@dataclass(frozen=True)
class FrameAnalysisMetrics:
    sharpness_score: float
    laplacian_variance: float
    exposure_score: float
    mean_luminance: float
    stability_score: float
    motion_intensity: MotionLevel
    composition_score: float
    face_count: int
    subject_position: SubjectPos
    lighting_mood: LightingMood
    dominant_colors: list[str]
    warm_pixel_ratio: float
    saturation_mean: float
    dark_with_bright_spikes: bool


@lru_cache(maxsize=1)
def _get_face_cascade() -> Optional[cv2.CascadeClassifier]:
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    if not cascade_path.is_file():
        return None
    clf = cv2.CascadeClassifier(str(cascade_path))
    return None if clf.empty() else clf


def _resize_max_width(bgr: np.ndarray, target_width: int = 480) -> np.ndarray:
    h, w = bgr.shape[:2]
    if w <= target_width or w == 0:
        return bgr
    scale = target_width / float(w)
    new_h = max(2, int(round(h * scale)))
    return cv2.resize(bgr, (target_width, new_h), interpolation=cv2.INTER_AREA)


def _score_laplacian(lap_var: float) -> float:
    if lap_var <= 15.0:
        return round((lap_var / 15.0) * 30.0, 1)
    if lap_var <= 120.0:
        return round(30.0 + ((lap_var - 15.0) / 105.0) * 45.0, 1)
    return round(min(100.0, 75.0 + ((lap_var - 120.0) / 380.0) * 25.0), 1)


def _score_exposure(gray: np.ndarray) -> tuple[float, float, float]:
    mean_lum = float(np.mean(gray))
    shadow_clip = float(np.mean(gray < 12))
    highlight_clip = float(np.mean(gray > 246))

    # Ideal average luminance band for natural & cinematic scenes is ~75..185
    if 75.0 <= mean_lum <= 185.0:
        lum_score = 94.0
    elif mean_lum < 75.0:
        lum_score = max(12.0, 94.0 - (75.0 - mean_lum) * 1.15)
    else:
        lum_score = max(20.0, 94.0 - (mean_lum - 185.0) * 1.10)

    clip_penalty = max(0.0, (shadow_clip + highlight_clip - 0.08) * 120.0)
    contrast_std = float(np.std(gray))
    contrast_bonus = 5.0 if 32.0 <= contrast_std <= 82.0 else (-8.0 if contrast_std < 14.0 else 0.0)
    score = round(max(5.0, min(100.0, lum_score - clip_penalty + contrast_bonus)), 1)
    return score, round(mean_lum, 1), round(highlight_clip, 4)


def _extract_dominant_hex_colors(bgr: np.ndarray, k: int = 3) -> list[str]:
    small = cv2.resize(bgr, (48, 48), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    pixels = rgb.reshape((-1, 3)).astype(np.float32)

    if len(pixels) < k:
        return ["#0B0D13"]

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _compactness, labels, centers = cv2.kmeans(
        pixels, k, None, criteria, 2, cv2.KMEANS_PP_CENTERS
    )
    counts = np.bincount(labels.flatten(), minlength=k)
    order = np.argsort(-counts)
    hex_colors: list[str] = []
    for idx in order:
        r, g, b = [int(np.clip(round(v), 0, 255)) for v in centers[idx]]
        hex_colors.append(f"#{r:02X}{g:02X}{b:02X}")
    return hex_colors


def _detect_faces_and_composition(gray: np.ndarray) -> tuple[int, SubjectPos, float]:
    h, w = gray.shape[:2]
    cascade = _get_face_cascade()
    faces = ()
    if cascade is not None:
        faces = cascade.detectMultiScale(
            gray,
            scaleFactor=1.15,
            minNeighbors=5,
            minSize=(24, 24),
        )

    face_count = len(faces)
    if face_count > 0:
        # Analyze primary (largest) face placement
        areas = [(fw * fh, fx + fw / 2.0, fy + fh / 2.0) for (fx, fy, fw, fh) in faces]
        areas.sort(reverse=True)
        _, cx, cy = areas[0]
        nx, ny = cx / float(w), cy / float(h)

        if 0.35 <= nx <= 0.65 and 0.28 <= ny <= 0.68:
            pos: SubjectPos = "center"
            comp = 92.0
        elif (0.25 <= nx <= 0.42 or 0.58 <= nx <= 0.75) and (0.25 <= ny <= 0.72):
            pos = "rule_of_thirds"
            comp = 90.0
        else:
            pos = "wide" if face_count > 1 else "center"
            comp = 78.0
        return face_count, pos, comp

    # Without faces, evaluate structural edge balance across rule-of-thirds regions
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.mean(edges > 0))
    if edge_density < 0.005:
        return 0, "none", 45.0
    comp_score = round(min(88.0, 62.0 + edge_density * 220.0), 1)
    return 0, "wide" if edge_density > 0.03 else "none", comp_score


def _analyze_hsv_mood(bgr: np.ndarray, mean_lum: float, highlight_clip: float) -> tuple[LightingMood, float, float, bool]:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]

    sat_mean = float(np.mean(sat))
    # OpenCV Hue range [0, 179]: warm gold/orange/red sits in [0..26] or [165..179] with saturation >= 55
    warm_mask = (((hue <= 26) | (hue >= 165)) & (sat >= 55) & (val >= 50))
    warm_ratio = float(np.mean(warm_mask))

    bright_spikes = float(np.mean((val > 225) & (sat > 40)))
    dark_with_bright_spikes = bool(mean_lum < 90.0 and (bright_spikes > 0.01 or highlight_clip > 0.008))

    if mean_lum < 65.0:
        mood: LightingMood = "low_light"
    elif warm_ratio >= 0.22:
        mood = "warm_golden"
    elif mean_lum >= 165.0:
        mood = "bright"
    else:
        mood = "balanced"

    return mood, round(warm_ratio, 3), round(sat_mean, 1), dark_with_bright_spikes


def _analyze_motion_sequence(small_grays: list[np.ndarray]) -> tuple[MotionLevel, float]:
    if len(small_grays) < 2:
        return "static", 95.0

    mags: list[float] = []
    coherences: list[float] = []
    for i in range(len(small_grays) - 1):
        flow = cv2.calcOpticalFlowFarneback(
            small_grays[i],
            small_grays[i + 1],
            None,
            0.5,
            2,
            11,
            2,
            5,
            1.1,
            0,
        )
        fx, fy = flow[..., 0], flow[..., 1]
        mag = np.sqrt(fx * fx + fy * fy)
        mean_mag = float(np.mean(mag))
        mags.append(mean_mag)

        # Coherence = magnitude of vector mean / mean of vector magnitudes
        vec_mean_mag = float(np.hypot(np.mean(fx), np.mean(fy)))
        coherence = vec_mean_mag / (mean_mag + 1e-5)
        coherences.append(coherence)

    avg_mag = float(np.mean(mags))
    mag_std = float(np.std(mags))
    avg_coh = float(np.mean(coherences))

    if avg_mag < 0.35:
        return "static", 95.0
    if avg_mag >= 1.8 and (avg_coh < 0.35 or mag_std > avg_mag * 0.85):
        stability = round(max(25.0, 62.0 - avg_mag * 5.0), 1)
        return "shaky", stability
    if avg_mag >= 3.0:
        return "action", round(min(90.0, 74.0 + avg_coh * 15.0), 1)
    return "smooth", round(min(96.0, 82.0 + avg_coh * 12.0), 1)


def analyze_image_file(file_path: Path) -> FrameAnalysisMetrics:
    """Analyze a still image for sharpness, exposure, faces, composition, and colors."""
    bgr = cv2.imread(str(file_path))
    if bgr is None or bgr.size == 0:
        raise ValueError(f"OpenCV could not decode image: {file_path}")

    resized = _resize_max_width(bgr, 480)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    sharpness = _score_laplacian(lap_var)
    exposure, mean_lum, highlight_clip = _score_exposure(gray)
    face_count, subject_pos, comp_score = _detect_faces_and_composition(gray)
    mood, warm_ratio, sat_mean, bright_spikes = _analyze_hsv_mood(resized, mean_lum, highlight_clip)
    palette = _extract_dominant_hex_colors(resized)

    return FrameAnalysisMetrics(
        sharpness_score=sharpness,
        laplacian_variance=round(lap_var, 2),
        exposure_score=exposure,
        mean_luminance=mean_lum,
        stability_score=100.0,
        motion_intensity="static",
        composition_score=comp_score,
        face_count=face_count,
        subject_position=subject_pos,
        lighting_mood=mood,
        dominant_colors=palette,
        warm_pixel_ratio=warm_ratio,
        saturation_mean=sat_mean,
        dark_with_bright_spikes=bright_spikes,
    )


def analyze_video_segment(
    video_path: Path,
    start_seconds: float = 0.0,
    end_seconds: Optional[float] = None,
    max_samples: int = 10,
) -> FrameAnalysisMetrics:
    """Sample frames evenly across a video or scene window and compute aggregated CV metrics."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"OpenCV could not open video: {video_path}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        total_dur = total_frames / fps if total_frames > 0 else 0.0

        start_f = max(0, int(round(start_seconds * fps)))
        end_sec = end_seconds if (end_seconds is not None and end_seconds > start_seconds) else total_dur
        end_f = min(max(start_f + 1, int(round(end_sec * fps))), max(1, total_frames - 1))

        count = min(max_samples, max(1, end_f - start_f + 1))
        indices = np.linspace(start_f, end_f, num=count, dtype=int)

        lap_vars: list[float] = []
        sharp_scores: list[float] = []
        exp_scores: list[float] = []
        lums: list[float] = []
        comp_scores: list[float] = []
        face_counts: list[int] = []
        positions: list[SubjectPos] = []
        small_grays: list[np.ndarray] = []
        mid_frame: Optional[np.ndarray] = None
        mid_idx = len(indices) // 2

        for i, frame_idx in enumerate(indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            resized = _resize_max_width(frame, 480)
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

            lv = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            lap_vars.append(lv)
            sharp_scores.append(_score_laplacian(lv))

            exp, lum, _hl = _score_exposure(gray)
            exp_scores.append(exp)
            lums.append(lum)

            fc, pos, cs = _detect_faces_and_composition(gray)
            face_counts.append(fc)
            positions.append(pos)
            comp_scores.append(cs)

            small_grays.append(cv2.resize(gray, (160, 90), interpolation=cv2.INTER_AREA))
            if i == mid_idx or mid_frame is None:
                mid_frame = resized

        if mid_frame is None:
            raise ValueError(f"No readable frames found in video segment: {video_path}")

        mid_gray = cv2.cvtColor(mid_frame, cv2.COLOR_BGR2GRAY)
        _exp, mid_lum, mid_hl = _score_exposure(mid_gray)
        mood, warm_ratio, sat_mean, bright_spikes = _analyze_hsv_mood(mid_frame, mid_lum, mid_hl)
        palette = _extract_dominant_hex_colors(mid_frame)
        motion_level, stability = _analyze_motion_sequence(small_grays)

        best_pos: SubjectPos = next((p for p in positions if p in {"center", "rule_of_thirds"}), positions[0])

        return FrameAnalysisMetrics(
            sharpness_score=round(float(np.mean(sharp_scores)), 1),
            laplacian_variance=round(float(np.mean(lap_vars)), 2),
            exposure_score=round(float(np.mean(exp_scores)), 1),
            mean_luminance=round(float(np.mean(lums)), 1),
            stability_score=stability,
            motion_intensity=motion_level,
            composition_score=round(float(np.mean(comp_scores)), 1),
            face_count=int(max(face_counts)) if face_counts else 0,
            subject_position=best_pos,
            lighting_mood=mood,
            dominant_colors=palette,
            warm_pixel_ratio=warm_ratio,
            saturation_mean=sat_mean,
            dark_with_bright_spikes=bright_spikes,
        )
    finally:
        cap.release()

