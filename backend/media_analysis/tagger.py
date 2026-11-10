"""Rule-based semantic auto-tagger combining OpenCV visual signals and media metadata."""

from __future__ import annotations

import re

from backend.api.schemas import MediaMetadata
from backend.media_analysis.cv_analyzer import FrameAnalysisMetrics

_KEYWORD_TAGS = {
    "firework": "Fireworks",
    "cracker": "Fireworks",
    "diya": "Diya",
    "lamp": "Diya",
    "deepavali": "Celebration",
    "diwali": "Celebration",
    "rangoli": "Rangoli",
    "sunset": "Sunset",
    "sunrise": "Sunset",
    "drone": "Landscape",
    "aerial": "Landscape",
    "crowd": "Celebration",
    "fest": "Celebration",
    "stage": "Celebration",
    "wedding": "Emotional",
    "portrait": "Portrait",
    "selfie": "Portrait",
}


def generate_semantic_tags(
    original_filename: str,
    metadata: MediaMetadata,
    metrics: FrameAnalysisMetrics,
    *,
    is_image: bool = False,
) -> list[str]:
    """Derive human-meaningful semantic and technical tags from CV metrics and filename cues."""
    tags: list[str] = []

    def _add(tag: str) -> None:
        if tag not in tags:
            tags.append(tag)

    # 1. Aspect & orientation classification
    if metadata.width > 0 and metadata.height > 0:
        if metadata.height > metadata.width:
            _add("Portrait")
        elif metadata.width > metadata.height:
            _add("Landscape")

    # 2. Face & people semantics
    if metrics.face_count == 1:
        _add("People")
        _add("Portrait")
    elif metrics.face_count >= 2:
        _add("People")
        _add("Group")
        _add("Celebration")

    # 3. Motion & shot style
    if not is_image:
        if metrics.motion_intensity == "action":
            _add("Action")
        elif metrics.motion_intensity == "shaky":
            _add("Shaky")
        elif metrics.motion_intensity in {"static", "smooth"} and metrics.face_count == 0:
            _add("Establishing")

    # 4. Lighting & color mood
    if metrics.lighting_mood == "low_light":
        _add("Low-Light")
    elif metrics.lighting_mood == "warm_golden":
        _add("Golden-Warm")
    elif metrics.lighting_mood == "bright":
        _add("Bright")

    if metrics.saturation_mean >= 95.0:
        _add("Vibrant")

    # 5. Dark scenes with localized bright warm spikes (classic fireworks / diyas at night)
    if metrics.dark_with_bright_spikes and metrics.warm_pixel_ratio >= 0.08:
        _add("Fireworks" if metrics.motion_intensity == "action" else "Diya")
        _add("Celebration")
    elif metrics.warm_pixel_ratio >= 0.30 and metrics.face_count == 0 and metrics.mean_luminance >= 80.0:
        _add("Sunset")

    # 6. Blur flag if sharpness is degraded
    if metrics.sharpness_score < 42.0:
        _add("Blurry")

    # 7. Filename semantic cues (without inventing unsupported tags)
    tokens = re.split(r"[^a-z0-9]+", original_filename.lower())
    joined = " ".join(tokens)
    for kw, tag_name in _KEYWORD_TAGS.items():
        if kw in joined:
            _add(tag_name)

    if metadata.fps >= 50:
        _add("High-FPS")

    return tags
