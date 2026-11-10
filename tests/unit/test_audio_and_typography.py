"""Unit tests for Librosa beat analysis, beat-sync alignment, ASS subtitles, and Phase 5 filtergraphs."""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from backend.api.schemas import (
    AudioTrackCue,
    CinematicEffects,
    MediaAsset,
    MediaClip,
    MediaMetadata,
    SubtitleCue,
    TimelinePlan,
)
from backend.audio_engine.analyzer import analyze_audio_file
from backend.audio_engine.beat_sync import align_timeline_to_beats
from backend.audio_engine.mixer import ResolvedAudioSource
from backend.video_engine.filtergraph import ResolvedVideoSource, build_render_command
from backend.video_engine.typography import format_ass_filter_arg, generate_ass_file


def _write_rhythmic_wav(out_path: Path, *, bpm: float = 120.0, duration: float = 6.0, sr: int = 22050) -> Path:
    """Create a real mono PCM16 WAV with crisp percussive transients spaced at the target BPM."""
    total_samples = int(duration * sr)
    samples = np.zeros(total_samples, dtype=np.float64)
    interval = 60.0 / bpm
    click_len = int(0.05 * sr)
    t_click = np.arange(click_len) / sr
    envelope = np.exp(-t_click * 55.0)
    click_wave = 0.85 * np.sin(2.0 * np.pi * 660.0 * t_click) * envelope

    beat_t = 0.5
    while beat_t + 0.06 < duration:
        start_idx = int(beat_t * sr)
        end_idx = min(total_samples, start_idx + click_len)
        samples[start_idx:end_idx] += click_wave[: end_idx - start_idx]
        beat_t += interval

    pcm = np.clip(samples * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return out_path


def _write_silent_wav(out_path: Path, *, duration: float = 2.0, sr: int = 22050) -> Path:
    pcm = np.zeros(int(duration * sr), dtype=np.int16)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return out_path


def _make_dummy_asset(asset_id: str, kind: str, duration: float, file_path: str) -> MediaAsset:
    return MediaAsset(
        id=asset_id,
        original_filename=f"{asset_id}.mp4",
        stored_filename=f"{asset_id}.mp4",
        media_kind=kind,  # type: ignore[arg-type]
        mime_type="video/mp4" if kind == "video" else "image/png",
        file_size_bytes=1024,
        file_path=file_path,
        source_url=f"/static/uploads/{asset_id}.mp4",
        metadata=MediaMetadata(
            width=1920,
            height=1080,
            fps=30.0,
            duration_seconds=duration,
            has_audio=(kind == "video"),
        ),
        created_at="2026-11-10T00:00:00Z",
    )


def test_analyze_rhythmic_and_silent_wav(tmp_path: Path) -> None:
    rhythm_wav = _write_rhythmic_wav(tmp_path / "beats.wav", bpm=120.0, duration=6.0)
    analysis = analyze_audio_file(rhythm_wav)

    assert analysis.duration_seconds > 5.5
    assert len(analysis.waveform_peaks) == 64
    assert all(0.08 <= bar <= 1.0 for bar in analysis.waveform_peaks)
    assert len(analysis.beat_timestamps) >= 4
    assert 55.0 <= analysis.tempo_bpm <= 185.0
    assert 0.0 <= analysis.silence_ratio < 1.0

    silent_wav = _write_silent_wav(tmp_path / "silent.wav", duration=2.0)
    silent_res = analyze_audio_file(silent_wav)
    assert silent_res.tempo_bpm == 0.0
    assert silent_res.beat_timestamps == []
    assert silent_res.silence_ratio == 1.0
    assert len(silent_res.waveform_peaks) == 64


def test_align_timeline_to_beats_snaps_within_source_bounds() -> None:
    asset1 = _make_dummy_asset("a1", "video", duration=5.0, file_path="/tmp/a1.mp4")
    asset2 = _make_dummy_asset("a2", "video", duration=2.05, file_path="/tmp/a2.mp4")
    assets = {"a1": asset1, "a2": asset2}

    clip1 = MediaClip(
        clip_id="c1",
        source_id="a1",
        source_filename="a1.mp4",
        source_url="/static/uploads/a1.mp4",
        start_time_seconds=0.0,
        end_time_seconds=1.86,
        timeline_start_seconds=0.0,
        duration_seconds=1.86,
        playback_speed=1.0,
        transition_in=None,
    )
    # Clip 2 ends at 3.86s, near beat 4.1s, but source asset duration is only 2.05s
    clip2 = MediaClip(
        clip_id="c2",
        source_id="a2",
        source_filename="a2.mp4",
        source_url="/static/uploads/a2.mp4",
        start_time_seconds=0.0,
        end_time_seconds=2.0,
        timeline_start_seconds=1.86,
        duration_seconds=2.0,
        playback_speed=1.0,
        transition_in=None,
    )
    timeline = TimelinePlan(
        project_id="proj_beat",
        title="Beat Test",
        video_clips=[clip1, clip2],
    )

    aligned, snapped_count, beats_used = align_timeline_to_beats(
        timeline=timeline,
        beat_timestamps=[0.5, 1.0, 1.5, 2.0, 2.5, 4.1],
        downbeat_timestamps=[0.5, 2.0],
        assets_by_id=assets,
        tolerance_seconds=0.35,
    )

    assert snapped_count >= 1
    assert 2.0 in beats_used
    assert aligned.video_clips[0].duration_seconds == 2.0
    assert aligned.video_clips[0].end_time_seconds == 2.0
    # Anti-overtrim protection guarantees Clip 2 never exceeds its 2.05s source asset
    assert aligned.video_clips[1].end_time_seconds <= 2.05


def test_generate_ass_subtitles_and_windows_filter_escaping(tmp_path: Path) -> None:
    subtitles = [
        SubtitleCue(
            id="s1",
            start_seconds=0.5,
            end_seconds=2.5,
            text="Festival {Glow} Line 1\nLine 2",
            style="cinematic_gold_bottom",
        ),
        SubtitleCue(
            id="s2",
            start_seconds=2.6,
            end_seconds=4.2,
            text="CLIMAX DROP!",
            style="bold_center_reel",
        ),
        SubtitleCue(
            id="s3",
            start_seconds=4.3,
            end_seconds=5.5,
            text="Closing note",
            style="subtle_white",
        ),
    ]
    ass_path = generate_ass_file(subtitles, 1280, 720, tmp_path / "subs.ass")
    assert ass_path.is_file()
    content = ass_path.read_text(encoding="utf-8")
    assert "[V4+ Styles]" in content
    assert "Style: cinematic_gold_bottom" in content
    assert "Style: bold_center_reel" in content
    assert "Style: subtle_white" in content
    assert "Festival (Glow) Line 1\\NLine 2" in content
    assert "\\fad(" in content

    filter_arg = format_ass_filter_arg(ass_path)
    assert filter_arg.startswith("ass=filename='")
    assert "\\" not in filter_arg.replace("\\:", "")  # forward slashes everywhere except drive colon escape


def test_filtergraph_phase5_speed_ramp_effects_ducking_and_ass(tmp_path: Path) -> None:
    vid_asset = _make_dummy_asset("v1", "video", duration=5.0, file_path="/tmp/v1.mp4")
    img_asset = _make_dummy_asset("i1", "image", duration=0.0, file_path="/tmp/i1.png")

    clip1 = MediaClip(
        clip_id="c1",
        source_id="v1",
        source_filename="v1.mp4",
        source_url="/static/uploads/v1.mp4",
        start_time_seconds=0.0,
        end_time_seconds=3.0,
        timeline_start_seconds=0.0,
        duration_seconds=3.0,
        speed_ramp="fast_to_slow",
    )
    clip2 = MediaClip(
        clip_id="c2",
        source_id="i1",
        source_filename="i1.png",
        source_url="/static/uploads/i1.png",
        start_time_seconds=0.0,
        end_time_seconds=2.5,
        timeline_start_seconds=2.5,
        duration_seconds=2.5,
    )
    music = AudioTrackCue(
        id="m1",
        name="music.wav",
        source_id="aud1",
        source_url="/static/uploads/music.wav",
        start_time_seconds=0.0,
        timeline_start_seconds=0.0,
        duration_seconds=5.5,
        ducking_enabled=True,
    )
    ass_path = tmp_path / "captions.ass"
    ass_path.write_text("[Script Info]\n", encoding="utf-8")

    timeline = TimelinePlan(
        project_id="p5",
        title="Cinematic Engine",
        color_grade="bleach_bypass",
        cinematic_effects=CinematicEffects(
            vignette=True,
            film_grain=True,
            ken_burns_on_images=True,
            audio_ducking=True,
            loudness_normalize=True,
        ),
        video_clips=[clip1, clip2],
        audio_tracks=[music],
    )

    cmd, expected_dur = build_render_command(
        timeline=timeline,
        resolved_clips=[ResolvedVideoSource(clip1, vid_asset), ResolvedVideoSource(clip2, img_asset)],
        resolved_audio=[ResolvedAudioSource(music, "/tmp/music.wav")],
        output_path=str(tmp_path / "out.mp4"),
        resolution="720p",
        subtitle_ass_path=ass_path,
    )

    assert expected_dur > 3.0
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "split=2" in fc
    assert "asplit=2" in fc
    assert "zoompan=" in fc
    assert "eq=contrast=1.32:saturation=0.45:brightness=-0.03" in fc
    assert "vignette=angle=PI/5" in fc
    assert "noise=alls=8:allf=t+u" in fc
    assert "ass=filename=" in fc
    assert "sidechaincompress=" in fc
    assert "loudnorm=I=-16:TP=-1.5:LRA=11" in fc

    # Verify disabling audio_ducking & loudness_normalize cleanly omits those stages
    disabled_tl = timeline.model_copy(
        update={
            "cinematic_effects": CinematicEffects(
                vignette=False,
                film_grain=False,
                ken_burns_on_images=False,
                audio_ducking=False,
                loudness_normalize=False,
            )
        }
    )
    cmd_off, _ = build_render_command(
        timeline=disabled_tl,
        resolved_clips=[ResolvedVideoSource(clip1, vid_asset), ResolvedVideoSource(clip2, img_asset)],
        resolved_audio=[ResolvedAudioSource(music, "/tmp/music.wav")],
        output_path=str(tmp_path / "out_off.mp4"),
        resolution="720p",
    )
    fc_off = cmd_off[cmd_off.index("-filter_complex") + 1]
    assert "sidechaincompress=" not in fc_off
    assert "loudnorm=" not in fc_off
    assert "vignette=" not in fc_off
    assert "noise=" not in fc_off
    assert "zoompan=" not in fc_off
