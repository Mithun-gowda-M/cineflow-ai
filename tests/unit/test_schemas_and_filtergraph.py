"""Unit tests for Pydantic timeline validation, aspect dimensions, and filtergraph assembly."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.api.schemas import (
    AudioTrackCue,
    MediaAsset,
    MediaClip,
    MediaMetadata,
    TimelinePlan,
    TransitionSpec,
)
from backend.audio_engine.mixer import ResolvedAudioSource, build_atempo_chain
from backend.video_engine.filtergraph import (
    ResolvedVideoSource,
    build_render_command,
    resolve_canvas_dimensions,
)


def _dummy_asset(asset_id: str, kind: str = "video", has_audio: bool = True) -> MediaAsset:
    return MediaAsset(
        id=asset_id,
        original_filename=f"{asset_id}.mp4",
        stored_filename=f"{asset_id}.mp4",
        media_kind=kind,  # type: ignore[arg-type]
        mime_type="video/mp4" if kind == "video" else "image/png",
        file_size_bytes=1024,
        file_path=f"/tmp/{asset_id}.mp4",
        source_url=f"/static/uploads/{asset_id}.mp4",
        metadata=MediaMetadata(width=1920, height=1080, fps=30.0, duration_seconds=5.0, has_audio=has_audio),
        tags=[kind],
        created_at="2026-11-10T00:00:00Z",
    )


def test_clip_rejects_invalid_trim_bounds() -> None:
    with pytest.raises(ValidationError):
        MediaClip(
            clip_id="c1",
            source_id="media_1",
            start_time_seconds=3.0,
            end_time_seconds=2.5,
            timeline_start_seconds=0.0,
            duration_seconds=2.0,
        )


def test_clip_rejects_extreme_playback_speed() -> None:
    with pytest.raises(ValidationError):
        MediaClip(
            clip_id="c1",
            source_id="media_1",
            start_time_seconds=0.0,
            end_time_seconds=2.0,
            timeline_start_seconds=0.0,
            duration_seconds=2.0,
            playback_speed=8.0,
        )


@pytest.mark.parametrize(
    ("aspect", "res", "expected"),
    [
        ("16:9", "1080p", (1920, 1080)),
        ("9:16", "1080p", (1080, 1920)),
        ("1:1", "720p", (720, 720)),
        ("4:5", "1080p", (1080, 1350)),
        ("21:9", "720p", (1680, 720)),
    ],
)
def test_canvas_dimensions_even_and_accurate(aspect, res, expected) -> None:
    w, h = resolve_canvas_dimensions(aspect, res)
    assert (w, h) == expected
    assert w % 2 == 0 and h % 2 == 0


def test_atempo_chain_stays_within_ffmpeg_bounds() -> None:
    assert build_atempo_chain(1.0) == ""
    assert build_atempo_chain(0.25) == "atempo=0.5,atempo=0.5"
    assert build_atempo_chain(3.0) == "atempo=2.0,atempo=1.5"


def test_filtergraph_builds_xfade_offset_and_anullsrc_for_silent_clip() -> None:
    clip1 = MediaClip(
        clip_id="c1",
        source_id="m1",
        start_time_seconds=0.0,
        end_time_seconds=4.0,
        timeline_start_seconds=0.0,
        duration_seconds=4.0,
        playback_speed=1.0,
        transition_in=TransitionSpec(type="fade_from_black", duration_seconds=0.5),
    )
    clip2 = MediaClip(
        clip_id="c2",
        source_id="m2",
        start_time_seconds=0.0,
        end_time_seconds=4.0,
        timeline_start_seconds=3.5,
        duration_seconds=4.0,
        playback_speed=1.0,
        transition_in=TransitionSpec(type="crossfade", duration_seconds=0.5),
        transition_out=TransitionSpec(type="fade_to_black", duration_seconds=0.5),
    )
    timeline = TimelinePlan(
        project_id="proj_1",
        title="Unit Test Cut",
        aspect_ratio="16:9",
        target_duration_seconds=7.5,
        fps=30,
        color_grade="golden_hour",
        video_clips=[clip1, clip2],
        audio_tracks=[],
        subtitles=[],
    )
    music = ResolvedAudioSource(
        cue=AudioTrackCue(
            id="a1",
            source_id="m_aud",
            duration_seconds=10.0,
            volume=0.8,
            ducking_enabled=True,
            duck_volume=0.3,
        ),
        file_path="/tmp/music.wav",
    )

    cmd, total_dur = build_render_command(
        timeline=timeline,
        resolved_clips=[
            ResolvedVideoSource(clip=clip1, asset=_dummy_asset("m1", "video", has_audio=True)),
            ResolvedVideoSource(clip=clip2, asset=_dummy_asset("m2", "image", has_audio=False)),
        ],
        resolved_audio=[music],
        output_path="/tmp/out.mp4",
        resolution="720p",
    )

    assert total_dur == pytest.approx(7.5, abs=0.01)
    fg = cmd[cmd.index("-filter_complex") + 1]
    assert "anullsrc=channel_layout=stereo:sample_rate=48000" in fg
    assert "xfade=transition=fade:duration=0.500:offset=3.500" in fg
    assert "colorbalance=" in fg
    assert "amix=inputs=2" in fg
    assert cmd[-1].endswith("out.mp4")
