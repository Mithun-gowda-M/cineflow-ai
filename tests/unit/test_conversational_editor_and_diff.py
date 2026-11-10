"""Unit tests for conversational editing, timeline diff calculation, and segment cache fingerprinting."""

from __future__ import annotations

from pathlib import Path

from backend.ai_director.conversational_editor import _apply_deterministic_edit
from backend.ai_director.diff_engine import compute_timeline_diff
from backend.api.schemas import (
    CinematicEffects,
    MediaAnalysisResult,
    MediaAsset,
    MediaClip,
    MediaMetadata,
    QualityBreakdown,
    TimelinePlan,
    TransitionSpec,
)
from backend.rendering.segment_cache import compute_segment_cache_key
from backend.video_engine.filtergraph import ResolvedVideoSource


def _make_asset(asset_id: str, filename: str, tags: list[str], tmp_file: Path) -> MediaAsset:
    tmp_file.write_bytes(b"mock-media-payload-" + asset_id.encode("utf-8"))
    return MediaAsset(
        id=asset_id,
        original_filename=filename,
        stored_filename=filename,
        media_kind="video",
        mime_type="video/mp4",
        file_size_bytes=tmp_file.stat().st_size,
        file_path=str(tmp_file),
        source_url=f"/static/uploads/{filename}",
        tags=tags,
        metadata=MediaMetadata(
            width=1920,
            height=1080,
            fps=30.0,
            duration_seconds=8.0,
            has_audio=True,
        ),
        analysis=MediaAnalysisResult(
            quality=QualityBreakdown(
                sharpness_score=90.0,
                exposure_score=85.0,
                stability_score=85.0,
                composition_score=85.0,
                overall_score=88.0,
                explanation="Sharp clip",
            ),
            semantic_tags=tags,
            analyzed_at="2026-11-10T00:00:00Z",
        ),
        created_at="2026-11-10T00:00:00Z",
    )


def _sample_timeline(assets: dict[str, MediaAsset]) -> TimelinePlan:
    c1 = MediaClip(
        clip_id="c1",
        source_id="m1",
        source_filename=assets["m1"].original_filename,
        source_url=assets["m1"].source_url,
        start_time_seconds=0.0,
        end_time_seconds=4.0,
        timeline_start_seconds=0.0,
        duration_seconds=4.0,
        playback_speed=1.0,
        transition_in=TransitionSpec(type="fade_from_black", duration_seconds=0.5),
    )
    c2 = MediaClip(
        clip_id="c2",
        source_id="m2",
        source_filename=assets["m2"].original_filename,
        source_url=assets["m2"].source_url,
        start_time_seconds=0.0,
        end_time_seconds=4.0,
        timeline_start_seconds=3.5,
        duration_seconds=4.0,
        playback_speed=1.0,
        transition_in=TransitionSpec(type="crossfade", duration_seconds=0.5),
    )
    c3 = MediaClip(
        clip_id="c3",
        source_id="m3",
        source_filename=assets["m3"].original_filename,
        source_url=assets["m3"].source_url,
        start_time_seconds=0.0,
        end_time_seconds=4.0,
        timeline_start_seconds=7.0,
        duration_seconds=4.0,
        playback_speed=1.0,
        transition_in=TransitionSpec(type="crossfade", duration_seconds=0.5),
    )
    return TimelinePlan(
        project_id="proj_chat",
        title="Campus Cut",
        aspect_ratio="16:9",
        color_grade="natural",
        video_clips=[c1, c2, c3],
    )


def test_conversational_clip_replacement_and_diff_preservation(tmp_path: Path) -> None:
    assets = {
        "m1": _make_asset("m1", "diya_intro.mp4", ["Diya", "Warm"], tmp_path / "m1.mp4"),
        "m2": _make_asset("m2", "stage_dance.mp4", ["Dance", "Action"], tmp_path / "m2.mp4"),
        "m3": _make_asset("m3", "crowd_cheer.mp4", ["Crowd", "Celebration"], tmp_path / "m3.mp4"),
        "m4": _make_asset("m4", "golden_sunset.mp4", ["Sunset", "Golden", "Warm"], tmp_path / "m4.mp4"),
    }
    before = _sample_timeline(assets)

    after, ops, warnings = _apply_deterministic_edit("Replace clip 2 with the sunset", before, assets)
    assert warnings == []
    assert any("golden_sunset.mp4" in op for op in ops)
    assert after.video_clips[1].source_id == "m4"
    assert after.video_clips[0].source_id == "m1"
    assert after.video_clips[2].source_id == "m3"

    diff = compute_timeline_diff(before, after)
    assert diff.modified_clip_ids == ["c2"]
    assert "c1" in diff.unchanged_clip_ids
    assert "c3" in diff.unchanged_clip_ids
    assert diff.affected_segment_indices == [1]


def test_conversational_trim_speed_lut_effects_and_aspect(tmp_path: Path) -> None:
    assets = {
        "m1": _make_asset("m1", "diya.mp4", ["Diya"], tmp_path / "m1.mp4"),
        "m2": _make_asset("m2", "fireworks.mp4", ["Fireworks"], tmp_path / "m2.mp4"),
        "m3": _make_asset("m3", "campus.mp4", ["Campus"], tmp_path / "m3.mp4"),
    }
    before = _sample_timeline(assets)

    after, ops, _ = _apply_deterministic_edit(
        "Trim clip 1 by 1.5 seconds, change to golden hour, add vignette and film grain, switch to 9:16",
        before,
        assets,
    )
    assert after.video_clips[0].duration_seconds == 2.5
    assert after.video_clips[0].end_time_seconds == 2.5
    assert after.color_grade == "golden_hour"
    assert after.cinematic_effects.vignette is True
    assert after.cinematic_effects.film_grain is True
    assert after.aspect_ratio == "9:16"
    # Clip 2 timeline_start shifted forward after Clip 1 became shorter
    assert after.video_clips[1].timeline_start_seconds < before.video_clips[1].timeline_start_seconds
    assert len(ops) >= 4

    diff = compute_timeline_diff(before, after)
    assert diff.global_visual_changed is True
    assert any("golden_hour" in c for c in diff.changes)
    assert any("9:16" in c for c in diff.changes)


def test_segment_cache_key_stability_and_invalidation(tmp_path: Path) -> None:
    asset1 = _make_asset("m1", "a.mp4", ["Campus"], tmp_path / "a.mp4")
    clip1 = MediaClip(
        clip_id="c1",
        source_id="m1",
        source_filename="a.mp4",
        start_time_seconds=0.0,
        end_time_seconds=3.0,
        duration_seconds=3.0,
        playback_speed=1.0,
    )
    item = ResolvedVideoSource(clip=clip1, asset=asset1)

    key_a = compute_segment_cache_key(
        item,
        width=1280,
        height=720,
        fps=30,
        effective_grade="golden_hour",
        ken_burns_on_images=True,
        apply_fade_in=True,
        apply_fade_out=False,
    )
    key_same = compute_segment_cache_key(
        item,
        width=1280,
        height=720,
        fps=30,
        effective_grade="golden_hour",
        ken_burns_on_images=True,
        apply_fade_in=True,
        apply_fade_out=False,
    )
    key_diff_grade = compute_segment_cache_key(
        item,
        width=1280,
        height=720,
        fps=30,
        effective_grade="bleach_bypass",
        ken_burns_on_images=True,
        apply_fade_in=True,
        apply_fade_out=False,
    )
    assert key_a == key_same
    assert key_a != key_diff_grade

