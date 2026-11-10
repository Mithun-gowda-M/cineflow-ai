"""Quantitative OpenCV & PySceneDetect style telemetry extractor for reference videos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from scenedetect import ContentDetector, SceneManager, open_video

from backend.api.schemas import (
    AspectRatio,
    CinematicEffects,
    ColorGradePreset,
    CutCadence,
    MediaMetadata,
    MotionProfile,
    PacingStyle,
    SpeedRampPreset,
    TransitionType,
)
from backend.media_analysis.cv_analyzer import analyze_video_segment
from backend.media_analysis.probe import probe_media_file
from backend.video_engine.hardware import detect_hardware_profile


@dataclass(frozen=True)
class ReferenceStyleMetrics:
    cuts_count: int
    duration_seconds: float
    cuts_per_minute: float
    avg_shot_duration_seconds: float
    cut_cadence: CutCadence
    motion_velocity_score: float
    motion_profile: MotionProfile
    color_mood: str
    recommended_color_grade: ColorGradePreset
    recommended_aspect_ratio: AspectRatio
    recommended_pacing: PacingStyle
    recommended_speed_ramp: SpeedRampPreset
    recommended_transition: TransitionType
    cinematic_effects: CinematicEffects
    dominant_palette: list[str]


def _count_cut_intervals(video_path: Path, duration: float) -> list[tuple[float, float]]:
    profile = detect_hardware_profile().profile
    downscale = 3 if profile == "low" else (2 if profile == "medium" else 1)
    frame_skip = 1 if profile == "low" else 0

    intervals: list[tuple[float, float]] = []
    video = open_video(str(video_path))
    try:
        sm = SceneManager()
        sm.add_detector(ContentDetector(threshold=25.0, min_scene_len=8))
        sm.auto_downscale = False
        sm.downscale = downscale
        sm.detect_scenes(video=video, frame_skip=frame_skip, show_progress=False)
        for s_tc, e_tc in sm.get_scene_list():
            s_s, e_s = float(s_tc.seconds), float(e_tc.seconds)
            if e_s > s_s + 0.05:
                intervals.append((s_s, e_s))
    finally:
        del video

    if not intervals:
        intervals = [(0.0, max(0.5, duration))]
    return intervals


def _compute_motion_velocity(video_path: Path, max_samples: int = 12) -> float:
    """Measure average inter-frame optical luminance energy (0–100) without retaining frames."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return 35.0
    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if total_frames < 2:
            return 25.0
        indices = np.linspace(0, max(1, total_frames - 1), num=min(max_samples, total_frames), dtype=int)
        prev_gray = None
        deltas: list[float] = []
        for f_idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(f_idx))
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            small = cv2.resize(frame, (160, 90), interpolation=cv2.INTER_AREA)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
            if prev_gray is not None:
                mad = float(np.mean(np.abs(gray - prev_gray)))
                deltas.append(mad)
            prev_gray = gray
        if not deltas:
            return 35.0
        # MAD of 28+ on uint8 scale represents rapid high-energy visual transitions/motion
        raw_score = (float(np.mean(deltas)) / 28.0) * 100.0
        return round(max(8.0, min(100.0, raw_score)), 1)
    finally:
        cap.release()


def _infer_aspect_ratio(meta: MediaMetadata) -> AspectRatio:
    if meta.height <= 0 or meta.width <= 0:
        return "16:9"
    ratio = meta.width / float(meta.height)
    if ratio < 0.7:
        return "9:16"
    if ratio < 0.9:
        return "4:5"
    if ratio <= 1.15:
        return "1:1"
    if ratio >= 2.0:
        return "21:9"
    return "16:9"


def analyze_reference_video(
    video_path: Path,
    *,
    metadata: Optional[MediaMetadata] = None,
) -> ReferenceStyleMetrics:
    """Analyze a local reference video for cut frequency, motion velocity, and color mood."""
    meta = metadata or probe_media_file(video_path, is_image=False)
    duration = max(0.5, float(meta.duration_seconds or 1.0))

    intervals = _count_cut_intervals(video_path, duration)
    shots = max(1, len(intervals))
    cuts_count = max(0, shots - 1)
    avg_shot = round(duration / float(shots), 2)
    cuts_per_min = round((max(1, shots) / duration) * 60.0, 1)

    if avg_shot <= 1.8 or cuts_per_min >= 28.0:
        cadence: CutCadence = "rapid"
        pacing: PacingStyle = "fast"
    elif avg_shot <= 3.8:
        cadence = "moderate"
        pacing = "dynamic_arc"
    else:
        cadence = "deliberate"
        pacing = "slow"

    cv_metrics = analyze_video_segment(video_path, max_samples=10)
    velocity = _compute_motion_velocity(video_path, max_samples=12)

    if velocity >= 72.0 or cv_metrics.motion_intensity == "action":
        motion_profile: MotionProfile = "high_velocity"
        ramp: SpeedRampPreset = "fast_to_slow"
    elif velocity >= 46.0:
        motion_profile = "dynamic_burst"
        ramp = "slow_to_fast"
    elif velocity >= 22.0 or cv_metrics.motion_intensity == "smooth":
        motion_profile = "smooth_glide"
        ramp = "ease_in_out"
    else:
        motion_profile = "static"
        ramp = "none"

    # Map lighting & saturation profile to curated LUT & finishing toggles
    if cv_metrics.saturation_mean < 28.0:
        color_grade: ColorGradePreset = "high_contrast_bw"
    elif cv_metrics.lighting_mood == "warm_golden":
        color_grade = "golden_hour"
    elif cv_metrics.dark_with_bright_spikes:
        color_grade = "cinematic_teal_orange"
    elif cv_metrics.lighting_mood == "low_light":
        color_grade = "moody_dark"
    elif cv_metrics.saturation_mean < 65.0 and cv_metrics.mean_luminance < 115.0:
        color_grade = "bleach_bypass"
    elif cv_metrics.warm_pixel_ratio >= 0.14 and cv_metrics.saturation_mean < 105.0:
        color_grade = "vintage_film"
    else:
        color_grade = "cinematic_teal_orange" if cadence == "rapid" else "natural"

    effects = CinematicEffects(
        vignette=(cv_metrics.mean_luminance < 115.0 or color_grade in {"moody_dark", "bleach_bypass"}),
        film_grain=(color_grade in {"vintage_film", "bleach_bypass"}),
        ken_burns_on_images=True,
        audio_ducking=True,
        loudness_normalize=True,
    )

    transition: TransitionType = (
        "zoom_in" if cadence == "rapid" else ("fade_from_black" if pacing == "slow" else "crossfade")
    )

    return ReferenceStyleMetrics(
        cuts_count=cuts_count,
        duration_seconds=round(duration, 2),
        cuts_per_minute=cuts_per_min,
        avg_shot_duration_seconds=avg_shot,
        cut_cadence=cadence,
        motion_velocity_score=velocity,
        motion_profile=motion_profile,
        color_mood=cv_metrics.lighting_mood,
        recommended_color_grade=color_grade,
        recommended_aspect_ratio=_infer_aspect_ratio(meta),
        recommended_pacing=pacing,
        recommended_speed_ramp=ramp,
        recommended_transition=transition,
        cinematic_effects=effects,
        dominant_palette=list(cv_metrics.dominant_colors),
    )

