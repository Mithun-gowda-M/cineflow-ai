"""Unit tests for OpenCV quality metrics, transparent scoring, semantic tagging, and dHash."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from backend.api.schemas import MediaMetadata
from backend.media_analysis.cv_analyzer import analyze_image_file
from backend.media_analysis.deduplicator import compute_dhash_from_bgr, hamming_distance
from backend.media_analysis.scoring import compute_quality_breakdown
from backend.media_analysis.tagger import generate_semantic_tags


def _make_checkerboard_bgr(width: int = 480, height: int = 320, cell: int = 24) -> np.ndarray:
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if ((x // cell) + (y // cell)) % 2 == 0:
                img[y : y + cell, x : x + cell] = (210, 185, 130)  # warm champagne-gold BGR
            else:
                img[y : y + cell, x : x + cell] = (45, 55, 75)
    return img


def test_blurry_image_scores_much_lower_than_sharp_image(tmp_path: Path) -> None:
    sharp_bgr = _make_checkerboard_bgr()
    blur_bgr = cv2.GaussianBlur(sharp_bgr, (35, 35), sigmaX=12.0)

    sharp_path = tmp_path / "sharp.png"
    blur_path = tmp_path / "blur.png"
    cv2.imwrite(str(sharp_path), sharp_bgr)
    cv2.imwrite(str(blur_path), blur_bgr)

    sharp_metrics = analyze_image_file(sharp_path)
    blur_metrics = analyze_image_file(blur_path)

    sharp_q = compute_quality_breakdown(sharp_metrics, is_image=True)
    blur_q = compute_quality_breakdown(blur_metrics, is_image=True)

    assert sharp_q.sharpness_score >= 75.0
    assert blur_q.sharpness_score <= 35.0
    assert sharp_q.overall_score - blur_q.overall_score >= 20.0
    assert "Blurry focus" in blur_q.explanation


def test_dark_underexposed_image_tagged_low_light(tmp_path: Path) -> None:
    dark_bgr = np.full((320, 480, 3), 18, dtype=np.uint8)
    # Add small texture so it's not zero-variance
    cv2.rectangle(dark_bgr, (80, 80), (140, 140), (35, 35, 35), 2)
    dark_path = tmp_path / "night_hall.png"
    cv2.imwrite(str(dark_path), dark_bgr)

    metrics = analyze_image_file(dark_path)
    breakdown = compute_quality_breakdown(metrics, is_image=True)
    tags = generate_semantic_tags(
        "night_hall.png",
        MediaMetadata(width=480, height=320),
        metrics,
        is_image=True,
    )

    assert metrics.lighting_mood == "low_light"
    assert breakdown.mean_luminance < 55.0
    assert "Low-Light" in tags
    assert "Landscape" in tags


def test_warm_spikes_on_dark_sky_tag_diya_or_fireworks(tmp_path: Path) -> None:
    night_fire = np.full((360, 640, 3), 10, dtype=np.uint8)
    # Paint bright warm orange/gold sparks covering ~10% of frame
    for cx, cy in [(200, 120), (320, 150), (440, 110), (280, 210)]:
        cv2.circle(night_fire, (cx, cy), 42, (20, 180, 255), -1)  # vivid orange-gold in BGR
    img_path = tmp_path / "festival_diya.png"
    cv2.imwrite(str(img_path), night_fire)

    metrics = analyze_image_file(img_path)
    tags = generate_semantic_tags(
        "festival_diya.png",
        MediaMetadata(width=640, height=360),
        metrics,
        is_image=True,
    )
    assert metrics.dark_with_bright_spikes is True
    assert "Diya" in tags
    assert "Celebration" in tags


def test_dhash_identifies_identical_vs_distinct_images() -> None:
    img_a = _make_checkerboard_bgr()
    # Slight brightness tweak simulating re-encoded copy
    img_a_copy = np.clip(img_a.astype(np.int16) + 5, 0, 255).astype(np.uint8)
    # Inverted gradient image
    img_b = np.zeros((320, 480, 3), dtype=np.uint8)
    for x in range(480):
        img_b[:, x] = int((x / 480.0) * 255)

    h_a = compute_dhash_from_bgr(img_a)
    h_copy = compute_dhash_from_bgr(img_a_copy)
    h_b = compute_dhash_from_bgr(img_b)

    assert hamming_distance(h_a, h_copy) <= 4
    assert hamming_distance(h_a, h_b) >= 16
