"""Unit tests for AI Director instruction parsing, 4-act sequencing, anti-duplication, and safety."""

from __future__ import annotations

from backend.ai_director.intent_parser import parse_director_instruction
from backend.ai_director.sequencer import (
    CandidateSegment,
    build_rule_based_storyboard,
    extract_candidates,
)
from backend.ai_director.validator import validate_and_sanitize_timeline
from backend.api.schemas import MediaAsset, MediaClip, MediaMetadata


def _make_cand(
    cid: str,
    tags: list[str],
    *,
    duration: float = 4.0,
    quality: float = 90.0,
    motion: str = "smooth",
    is_dup: bool = False,
) -> CandidateSegment:
    return CandidateSegment(
        candidate_id=cid,
        source_id=cid,
        filename=f"{cid}.mp4",
        source_url=f"/static/uploads/{cid}.mp4",
        thumbnail_url=None,
        media_kind="video",
        start_seconds=0.0,
        end_seconds=duration,
        quality_score=quality,
        sharpness_score=quality,
        motion_level=motion,
        tags=tags,
        is_duplicate=is_dup,
    )


def test_parse_deepavali_master_prompt() -> None:
    intent = parse_director_instruction(
        "Create a two-minute cinematic Deepavali video. Start with a slow dramatic introduction. "
        "Use fast transitions during the fireworks. Make the ending emotional."
    )
    assert intent.target_duration_seconds == 120.0
    assert intent.aspect_ratio == "16:9"
    assert intent.color_grade == "golden_hour"
    assert intent.intro_style == "slow_dramatic"
    assert "fireworks" in intent.climax_keywords
    assert intent.outro_style == "emotional"
    assert intent.pacing == "dynamic_arc"


def test_parse_vertical_reel_prompt() -> None:
    intent = parse_director_instruction("Produce a fast 9:16 Instagram Reel from my travel clips")
    assert intent.aspect_ratio == "9:16"
    assert intent.color_grade == "cinematic_teal_orange"
    assert intent.pacing == "fast"
    assert intent.target_duration_seconds == 30.0


def test_rule_based_sequencer_orders_acts_and_never_duplicates_footage() -> None:
    intent = parse_director_instruction(
        "Create a two-minute Deepavali film with slow dramatic intro, fast fireworks, and emotional ending."
    )
    candidates = [
        _make_cand("sunset_outro", ["Sunset", "Golden-Warm", "Emotional"], duration=5.0, quality=95.0, motion="static"),
        _make_cand("fireworks_burst", ["Fireworks", "Action", "Celebration"], duration=4.0, quality=92.0, motion="action"),
        _make_cand("crowd_dance", ["People", "Group", "Celebration"], duration=5.0, quality=88.0, motion="smooth"),
        _make_cand("diya_intro", ["Diya", "Establishing", "Golden-Warm"], duration=4.0, quality=93.0, motion="static"),
    ]

    timeline, storyboard, warnings = build_rule_based_storyboard(
        project_id="proj_test",
        intent=intent,
        candidates=candidates,
        audio_assets=[],
    )

    assert len(timeline.video_clips) == 4
    assert storyboard[0].act == "Opening Hook"
    assert storyboard[0].source_id == "diya_intro"
    assert storyboard[0].playback_speed == 0.8
    assert timeline.video_clips[0].transition_in and timeline.video_clips[0].transition_in.type == "fade_from_black"

    acts_by_src = {b.source_id: b.act for b in storyboard}
    assert acts_by_src["fireworks_burst"] == "Climax"
    assert acts_by_src["sunset_outro"] == "Emotional Resolution"

    # Anti-duplication enforcement: requested 120s with ~18s source -> must NOT loop clips
    used_sources = [c.source_id for c in timeline.video_clips]
    assert len(used_sources) == len(set(used_sources))
    assert timeline.target_duration_seconds < 30.0
    assert any("without artificial duplication" in w for w in warnings)


def test_validator_drops_hallucinated_and_duplicate_segments_and_clamps_bounds() -> None:
    asset = MediaAsset(
        id="m_real",
        original_filename="real.mp4",
        stored_filename="m_real.mp4",
        media_kind="video",
        mime_type="video/mp4",
        file_size_bytes=1024,
        file_path="/tmp/m_real.mp4",
        source_url="/static/uploads/m_real.mp4",
        metadata=MediaMetadata(width=1280, height=720, fps=30.0, duration_seconds=5.0, has_audio=False),
        tags=["video"],
        created_at="2026-11-10T00:00:00Z",
    )

    intent = parse_director_instruction("10 second cinematic cut")
    timeline, beats, _ = build_rule_based_storyboard(
        "proj_v",
        intent,
        [_make_cand("m_real", ["Landscape"], duration=5.0)],
        [],
    )

    # Inject bad LLM clip: hallucinated ID, out-of-bounds trim, and duplicate of m_real
    bad_clip = MediaClip(
        clip_id="bad_1",
        source_id="hallucinated_999",
        start_time_seconds=0.0,
        end_time_seconds=3.0,
        timeline_start_seconds=0.0,
        duration_seconds=3.0,
    )
    overtrim_clip = timeline.video_clips[0].model_copy(
        update={"clip_id": "over_1", "end_time_seconds": 999.0}
    )
    dup_clip = timeline.video_clips[0].model_copy(
        update={"clip_id": "dup_1", "end_time_seconds": 999.0}
    )
    tampered = timeline.model_copy(update={"video_clips": [bad_clip, overtrim_clip, dup_clip]})

    clean_tl, _clean_beats, val_warnings = validate_and_sanitize_timeline(
        tampered, beats, {"m_real": asset}
    )

    assert len(clean_tl.video_clips) == 1
    assert clean_tl.video_clips[0].end_time_seconds == 5.0
    assert any("unknown" in w.lower() for w in val_warnings)
    assert any("duplicate" in w.lower() for w in val_warnings)

