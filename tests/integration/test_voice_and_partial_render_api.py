"""Integration tests for Whisper voice endpoints, conversational editing, Undo/Redo history, and partial re-rendering."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from backend.audio_engine import transcriber as transcriber_mod
from backend.media_analysis.probe import probe_media_file
from backend.video_engine.ffmpeg_runner import run_ffmpeg_sync
from tests.conftest import create_synthetic_audio, create_synthetic_video


@dataclass
class _StubWord:
    word: str
    start: float
    end: float
    probability: float = 0.98


@dataclass
class _StubSeg:
    start: float
    end: float
    text: str
    words: list[_StubWord]


@dataclass
class _StubInfo:
    language: str = "en"
    duration: float = 2.0


class _StubWhisperModel:
    def transcribe(self, _wav_path: str, **_kwargs):
        return [
            _StubSeg(
                start=0.1,
                end=1.9,
                text="Replace clip 2 with fireworks",
                words=[
                    _StubWord("Replace", 0.1, 0.4),
                    _StubWord("clip", 0.4, 0.7),
                    _StubWord("2", 0.7, 0.9),
                    _StubWord("with", 0.9, 1.2),
                    _StubWord("fireworks", 1.2, 1.9),
                ],
            )
        ], _StubInfo()


def _create_patterned_video(out_path: Path, *, source_expr: str, with_audio: bool = False) -> Path:
    args = [
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        source_expr,
    ]
    if with_audio:
        args.extend(["-f", "lavfi", "-i", "sine=frequency=520:sample_rate=48000:duration=3.5"])
        args.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest"])
    else:
        args.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-an"])
    args.append(str(out_path))
    run_ffmpeg_sync(args, timeout=30)
    return out_path


def _poll_render(client, job_id: str, timeout_sec: float = 90.0) -> dict:
    deadline = time.time() + timeout_sec
    last_payload = {}
    while time.time() < deadline:
        res = client.get(f"/api/v1/render/{job_id}")
        assert res.status_code == 200
        last_payload = res.json()
        if last_payload["status"] in {"completed", "failed", "cancelled"}:
            return last_payload
        time.sleep(0.25)
    raise AssertionError(f"Render job {job_id} timed out; last status: {last_payload}")


def test_voice_conversational_undo_redo_and_partial_segment_render(isolated_env, monkeypatch) -> None:
    client, _settings, tmp_path = isolated_env

    # 1. Generate distinct synthetic media assets
    src_dir = tmp_path / "phase6_inputs"
    src_dir.mkdir()
    vid_intro = create_synthetic_video(
        src_dir / "diya_opening.mp4", width=640, height=360, duration=4.0, with_audio=True
    )
    vid_broll = _create_patterned_video(
        src_dir / "broll_campus.mp4",
        source_expr="smptebars=size=640x360:rate=30:duration=3.5",
        with_audio=False,
    )
    vid_fireworks = _create_patterned_video(
        src_dir / "fireworks_finale.mp4",
        source_expr="rgbtestsrc=size=640x360:rate=30:duration=3.5",
        with_audio=True,
    )
    voice_wav = create_synthetic_audio(src_dir / "mic_cmd.wav", duration=2.5)

    up_res = client.post(
        "/api/v1/media/upload",
        files=[
            ("files", ("diya_opening.mp4", vid_intro.read_bytes(), "video/mp4")),
            ("files", ("broll_campus.mp4", vid_broll.read_bytes(), "video/mp4")),
            ("files", ("fireworks_finale.mp4", vid_fireworks.read_bytes(), "video/mp4")),
        ],
    )
    assert up_res.status_code == 200
    by_name = {a["original_filename"]: a for a in up_res.json()["uploaded"]}
    diya_a = by_name["diya_opening.mp4"]
    broll_a = by_name["broll_campus.mp4"]
    fireworks_a = by_name["fireworks_finale.mp4"]

    # 2. Check voice status & Whisper transcription endpoint (with injected offline model stub)
    status_res = client.get("/api/v1/voice/status")
    assert status_res.status_code == 200
    assert status_res.json()["package_installed"] is True

    monkeypatch.setattr(transcriber_mod, "_get_whisper_model", lambda: _StubWhisperModel())
    tr_res = client.post(
        "/api/v1/voice/transcribe",
        files={"file": ("mic_cmd.wav", voice_wav.read_bytes(), "audio/wav")},
    )
    assert tr_res.status_code == 200
    spoken_cmd = tr_res.json()["text"]
    assert spoken_cmd == "Replace clip 2 with fireworks"

    sub_res = client.post(f"/api/v1/voice/subtitles/{diya_a['id']}")
    assert sub_res.status_code == 200
    assert len(sub_res.json()["suggested_subtitles"]) >= 1

    # 3. Create project & perform Initial Render #1 (populates segment cache)
    proj_res = client.post(
        "/api/v1/projects",
        json={"title": "Phase 6 Partial Cache Cut", "aspect_ratio": "16:9", "color_grade": "golden_hour"},
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    initial_timeline = {
        "project_id": proj_id,
        "title": "Phase 6 Partial Cache Cut",
        "aspect_ratio": "16:9",
        "fps": 30,
        "color_grade": "golden_hour",
        "video_clips": [
            {
                "clip_id": "c1",
                "source_id": diya_a["id"],
                "source_filename": "diya_opening.mp4",
                "source_url": diya_a["source_url"],
                "start_time_seconds": 0.0,
                "end_time_seconds": 4.0,
                "timeline_start_seconds": 0.0,
                "duration_seconds": 4.0,
                "playback_speed": 1.0,
                "transition_in": {"type": "fade_from_black", "duration_seconds": 0.4},
            },
            {
                "clip_id": "c2",
                "source_id": broll_a["id"],
                "source_filename": "broll_campus.mp4",
                "source_url": broll_a["source_url"],
                "start_time_seconds": 0.0,
                "end_time_seconds": 3.5,
                "timeline_start_seconds": 3.6,
                "duration_seconds": 3.5,
                "playback_speed": 1.0,
                "transition_in": {"type": "crossfade", "duration_seconds": 0.4},
            },
        ],
        "audio_tracks": [],
        "subtitles": [],
    }

    r1 = client.post(
        "/api/v1/render",
        json={"timeline": initial_timeline, "resolution": "720p", "encoder_preference": "cpu", "partial_cache": True},
    )
    assert r1.status_code == 202
    r1_status = _poll_render(client, r1.json()["job_id"])
    assert r1_status["status"] == "completed", r1_status
    assert r1_status["segment_cache_misses"] == 2
    assert r1_status["segment_cache_hits"] == 0
    assert r1_status["partial_rerender_used"] is False

    # 4. Conversational Edit #1 (voice command transcript) -> Replace clip 2 with fireworks
    e1 = client.post(
        "/api/v1/director/edit",
        json={
            "project_id": proj_id,
            "instruction": spoken_cmd,
            "timeline": initial_timeline,
            "use_llm": False,
        },
    )
    assert e1.status_code == 200
    e1_data = e1.json()
    assert e1_data["timeline"]["video_clips"][1]["source_id"] == fireworks_a["id"]
    assert e1_data["diff"]["modified_clip_ids"] == ["c2"]
    assert "c1" in e1_data["diff"]["unchanged_clip_ids"]
    assert e1_data["can_undo"] is True
    assert e1_data["history_count"] == 2

    # 5. Conversational Edit #2 -> Trim clip 1 by 1 second
    e2 = client.post(
        "/api/v1/director/edit",
        json={
            "project_id": proj_id,
            "instruction": "Trim clip 1 by 1 second",
            "timeline": e1_data["timeline"],
            "use_llm": False,
        },
    )
    assert e2.status_code == 200
    assert e2.json()["timeline"]["video_clips"][0]["duration_seconds"] == 3.0
    assert e2.json()["history_count"] == 3

    # 6. Undo / Redo SQLite Revision History verification
    hist_res = client.get(f"/api/v1/projects/{proj_id}/history")
    assert hist_res.status_code == 200
    assert hist_res.json()["active_revision_index"] == 2

    undo_res = client.post(f"/api/v1/projects/{proj_id}/undo")
    assert undo_res.status_code == 200
    assert undo_res.json()["active_revision_index"] == 1
    assert undo_res.json()["timeline"]["video_clips"][0]["duration_seconds"] == 4.0
    assert undo_res.json()["timeline"]["video_clips"][1]["source_id"] == fireworks_a["id"]
    assert undo_res.json()["can_redo"] is True

    undo2_res = client.post(f"/api/v1/projects/{proj_id}/undo")
    assert undo2_res.status_code == 200
    assert undo2_res.json()["timeline"]["video_clips"][1]["source_id"] == broll_a["id"]
    assert undo2_res.json()["can_undo"] is False

    redo_res = client.post(f"/api/v1/projects/{proj_id}/redo")
    assert redo_res.status_code == 200
    assert redo_res.json()["active_revision_index"] == 1
    edited_timeline = redo_res.json()["timeline"]
    assert edited_timeline["video_clips"][1]["source_id"] == fireworks_a["id"]

    # 7. Partial Re-Render #2: Clip 1 (diya_opening) MUST be cached hit, Clip 2 (fireworks) cache miss!
    r2 = client.post(
        "/api/v1/render",
        json={"timeline": edited_timeline, "resolution": "720p", "encoder_preference": "cpu", "partial_cache": True},
    )
    assert r2.status_code == 202
    r2_status = _poll_render(client, r2.json()["job_id"])
    assert r2_status["status"] == "completed", r2_status
    assert r2_status["segment_cache_hits"] == 1
    assert r2_status["segment_cache_misses"] == 1
    assert r2_status["partial_rerender_used"] is True

    dl_res = client.get(f"/api/v1/render/{r2.json()['job_id']}/download")
    assert dl_res.status_code == 200
    final_mp4 = tmp_path / "phase6_partial_rerender.mp4"
    final_mp4.write_bytes(dl_res.content)

    probed = probe_media_file(final_mp4, is_image=False)
    assert probed.width == 1280
    assert probed.height == 720
    assert probed.has_audio is True
    assert probed.duration_seconds > 5.0

