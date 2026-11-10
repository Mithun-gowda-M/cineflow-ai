"""Transparent multi-factor quality scoring and explanation builder."""

from __future__ import annotations

from backend.api.schemas import QualityBreakdown
from backend.media_analysis.cv_analyzer import FrameAnalysisMetrics


def compute_quality_breakdown(
    metrics: FrameAnalysisMetrics,
    *,
    is_image: bool = False,
) -> QualityBreakdown:
    """Compute a transparent 0-100 quality breakdown and plain-English explanation."""
    if is_image:
        overall = (
            0.40 * metrics.sharpness_score
            + 0.35 * metrics.exposure_score
            + 0.25 * metrics.composition_score
        )
    else:
        overall = (
            0.30 * metrics.sharpness_score
            + 0.25 * metrics.exposure_score
            + 0.25 * metrics.stability_score
            + 0.20 * metrics.composition_score
        )

    overall_rounded = round(max(0.0, min(100.0, overall)), 1)

    notes: list[str] = []
    if metrics.sharpness_score >= 75.0:
        notes.append(f"Crisp focus ({metrics.sharpness_score:.0f}/100)")
    elif metrics.sharpness_score < 45.0:
        notes.append(f"Blurry focus (laplacian={metrics.laplacian_variance:.1f})")
    else:
        notes.append(f"Moderate sharpness ({metrics.sharpness_score:.0f}/100)")

    if metrics.exposure_score >= 80.0:
        notes.append(f"balanced exposure ({metrics.exposure_score:.0f}/100)")
    elif metrics.mean_luminance < 55.0:
        notes.append(f"underexposed/low-light (lum={metrics.mean_luminance:.0f})")
    elif metrics.mean_luminance > 210.0:
        notes.append(f"overexposed highlights (lum={metrics.mean_luminance:.0f})")
    else:
        notes.append(f"fair lighting ({metrics.exposure_score:.0f}/100)")

    if not is_image:
        if metrics.motion_intensity == "shaky":
            notes.append(f"camera shake detected ({metrics.stability_score:.0f}/100)")
        elif metrics.motion_intensity == "action":
            notes.append("dynamic action motion")
        elif metrics.motion_intensity == "smooth":
            notes.append("smooth camera motion")
        else:
            notes.append("steady framing")

    if metrics.face_count == 1:
        notes.append(f"1 clear face ({metrics.subject_position})")
    elif metrics.face_count > 1:
        notes.append(f"{metrics.face_count} people visible")

    explanation = "; ".join(notes).capitalize() + "."

    return QualityBreakdown(
        sharpness_score=metrics.sharpness_score,
        exposure_score=metrics.exposure_score,
        stability_score=metrics.stability_score,
        composition_score=metrics.composition_score,
        laplacian_variance=metrics.laplacian_variance,
        mean_luminance=metrics.mean_luminance,
        motion_intensity=metrics.motion_intensity,
        lighting_mood=metrics.lighting_mood,
        face_count=metrics.face_count,
        subject_position=metrics.subject_position,
        dominant_colors=metrics.dominant_colors,
        overall_score=overall_rounded,
        explanation=explanation,
    )

