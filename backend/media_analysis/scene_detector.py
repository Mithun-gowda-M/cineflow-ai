"""PySceneDetect scene segmentation and per-scene keyframe quality analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
from scenedetect import ContentDetector, SceneManager, open_video

from backend.api.config import get_settings
from backend.api.schemas import DetectedScene, MediaMetadata
from backend.media_analysis.cv_analyzer import analyze_video_segment
from backend.media_analysis.scoring import compute_quality_breakdown
from backend.media_analysis.tagger import generate_semantic_tags
from backend.video_engine.hardware import detect_hardware_profile


def _extract_scene_thumbnail(
    video_path: Path, media_id: str, scene_index: int, midpoint_seconds: float
) -> Optional[str]:
    settings = get_settings()
    thumb_path = settings.PROXY_DIR / f"{media_id}_scene_{scene_index:02d}.jpg"
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        target_frame = max(0, int(round(midpoint_seconds * fps)))
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ok, frame = cap.read()
        if not ok or frame is None:
            return None
        h, w = frame.shape[:2]
        if w > 360:
            scale = 360.0 / float(w)
            frame = cv2.resize(frame, (360, max(2, int(round(h * scale)))), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(thumb_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        return f"/static/proxies/{thumb_path.name}" if thumb_path.is_file() else None
    finally:
        cap.release()


def detect_video_scenes(
    video_path: Path,
    media_id: str,
    original_filename: str,
    metadata: MediaMetadata,
    *,
    threshold: float = 26.0,
    max_scenes: int = 30,
) -> list[DetectedScene]:
    """Segment a video file into scenes using PySceneDetect and score each scene."""
    profile = detect_hardware_profile().profile
    downscale_factor = 3 if profile == "low" else (2 if profile == "medium" else 1)
    frame_skip = 1 if profile == "low" else 0

    raw_intervals: list[tuple[float, float]] = []
    video = open_video(str(video_path))
    try:
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=10))
        scene_manager.auto_downscale = False
        scene_manager.downscale = downscale_factor
        scene_manager.detect_scenes(video=video, frame_skip=frame_skip, show_progress=False)
        scene_list = scene_manager.get_scene_list()
        for start_tc, end_tc in scene_list[:max_scenes]:
            s_sec = round(float(start_tc.seconds), 3)
            e_sec = round(float(end_tc.seconds), 3)
            if e_sec > s_sec + 0.05:
                raw_intervals.append((s_sec, e_sec))
    finally:
        del video

    if not raw_intervals:
        dur = max(0.5, round(float(metadata.duration_seconds or 1.0), 3))
        raw_intervals = [(0.0, dur)]

    detected: list[DetectedScene] = []
    for idx, (start_sec, end_sec) in enumerate(raw_intervals):
        dur_sec = round(max(0.1, end_sec - start_sec), 3)
        midpoint = start_sec + dur_sec / 2.0
        thumb_url = _extract_scene_thumbnail(video_path, media_id, idx + 1, midpoint)

        try:
            metrics = analyze_video_segment(
                video_path,
                start_seconds=start_sec,
                end_seconds=end_sec,
                max_samples=6,
            )
            breakdown = compute_quality_breakdown(metrics, is_image=False)
            tags = generate_semantic_tags(original_filename, metadata, metrics, is_image=False)
            q_score = breakdown.overall_score
            s_score = breakdown.sharpness_score
            motion = breakdown.motion_intensity
        except Exception:
            q_score, s_score, motion, tags = 70.0, 70.0, "static", []

        detected.append(
            DetectedScene(
                scene_id=f"{media_id}_sc_{idx + 1:02d}",
                media_id=media_id,
                scene_index=idx + 1,
                start_seconds=start_sec,
                end_seconds=end_sec,
                duration_seconds=dur_sec,
                thumbnail_url=thumb_url,
                quality_score=q_score,
                sharpness_score=s_score,
                motion_level=motion,
                tags=tags,
            )
        )

    return detected
