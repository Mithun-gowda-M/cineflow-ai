"""Integration tests for AI Director API, Ollama mocking/fallback, and Director-to-FFmpeg render."""

from __future__ import annotations

import json
import time

from backend.ai_director import director as director_mod
from backend.media_analysis.probe import probe_media_file
from backend.video_engine.ffmpeg_runner import run_ffmpeg_sync
from tests.conftest import (
    create_synthetic_audio,
    create_synthetic_video,
)


def _poll_render(client, job_id: str, timeout_sec: float = 60.0) -> dict:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        res = client.get(f"/api/v1/render/{job_id}")
        assert res.status_code == 200
        body = res.json()
        if body["status"] in {"completed", "failed", "cancelled"}:
            return body
        time.sleep(0.25)
    raise AssertionError("Timed out polling render job.")


def test_director_status_and_empty_library_guard(isolated_env) -> None:
    client, _settings, _tmp = isolated_env

    status_res = client.get("/api/v1/director/status")
    assert status_res.status_code == 200
    assert status_res.json()["fallback_ready"] is True

    plan_res = client.post(
        "/api/v1/director/plan",
        json={"project_id": "proj_empty", "instruction": "Create a 30s travel film"},
    )
    assert plan_res.status_code == 422


def test_director_plan_executes_and_renders_real_mp4(isolated_env, monkeypatch) -> None:
    client, _settings, tmp_path = isolated_env

    # Ensure deterministic fallback regardless of host Ollama status
    async def _offline_ollama():
        return False, []

    monkeypatch.setattr(director_mod, "check_ollama_status", _offline_ollama)

    src = tmp_path / "src"
    src.mkdir()
    clip1 = create_synthetic_video(src / "diya_opening.mp4", width=640, height=360, duration=2.0, with_audio=True)
    # Create a visually distinct second video using testsrc2 so perceptual dHash treats it as unique footage
    clip2 = src / "fireworks_finale.mp4"
    run_ffmpeg_sync(
        [
            "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=2.0",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(clip2),
        ],
        timeout=30,
    )
    # Crisp sunset skyline PNG with real edge detail
    import cv2
    import numpy as np

    sunset_img = np.zeros((360, 640, 3), dtype=np.uint8)
    for y in range(360):
        sunset_img[y, :] = (int(50 - y * 0.1), int(150 - y * 0.25), int(235 - y * 0.2))
    for i, x in enumerate(range(30, 590, 65)):
        cv2.rectangle(sunset_img, (x, 220 - (i % 3) * 30), (x + 42, 360), (20, 20, 25), -1)
    img3 = src / "sunset_card.png"
    cv2.imwrite(str(img3), sunset_img)

    wav4 = create_synthetic_audio(src / "festive_bg.wav", duration=6.0)

    up_res = client.post(
        "/api/v1/media/upload",
        files=[
            ("files", ("diya_opening.mp4", clip1.read_bytes(), "video/mp4")),
            ("files", ("fireworks_finale.mp4", clip2.read_bytes(), "video/mp4")),
            ("files", ("sunset_card.png", img3.read_bytes(), "image/png")),
            ("files", ("festive_bg.wav", wav4.read_bytes(), "audio/wav")),
        ],
    )
    assert up_res.status_code == 200
    assert len(up_res.json()["uploaded"]) == 4

    # Ask AI Director for a 2-minute Deepavali film -> should produce unique footage + warning + valid TimelinePlan
    plan_res = client.post(
        "/api/v1/director/plan",
        json={
            "project_id": "proj_deepavali",
            "instruction": (
                "Create a two-minute cinematic Deepavali video. "
                "Start with a slow dramatic introduction, fast cuts during fireworks, and emotional ending."
            ),
            "use_llm": True,
        },
    )
    assert plan_res.status_code == 200
    plan_body = plan_res.json()
    assert plan_body["engine_used"] == "rule_fallback"
    assert plan_body["intent"]["color_grade"] == "golden_hour"
    assert len(plan_body["storyboard"]) >= 2
    assert len(plan_body["timeline"]["audio_tracks"]) == 1
    assert any("without artificial duplication" in w for w in plan_body["warnings"])

    # Hand the AI-generated TimelinePlan straight to Phase 2 FFmpeg render endpoint!
    render_res = client.post(
        "/api/v1/render",
        json={
            "timeline": plan_body["timeline"],
            "resolution": "720p",
            "encoder_preference": "cpu",
        },
    )
    assert render_res.status_code == 202
    job = _poll_render(client, render_res.json()["job_id"])
    assert job["status"] == "completed", job.get("error_message")

    dl = client.get(job["output_video_url"])
    assert dl.status_code == 200
    out_mp4 = tmp_path / "ai_directed.mp4"
    out_mp4.write_bytes(dl.content)

    meta = probe_media_file(out_mp4)
    assert meta.width == 1280 and meta.height == 720
    assert meta.codec == "h264"
    assert meta.has_audio is True
    assert meta.duration_seconds > 2.5


def test_director_uses_ollama_when_available_and_falls_back_on_bad_json(isolated_env, monkeypatch) -> None:
    client, _settings, tmp_path = isolated_env

    src = tmp_path / "src_llm"
    src.mkdir()
    clip1 = create_synthetic_video(src / "travel_drone.mp4", width=640, height=360, duration=2.0)
    up_res = client.post(
        "/api/v1/media/upload",
        files=[("files", ("travel_drone.mp4", clip1.read_bytes(), "video/mp4"))],
    )
    assert up_res.status_code == 200
    asset = up_res.json()["uploaded"][0]
    first_cid = asset["scenes"][0]["scene_id"] if asset["scenes"] else asset["id"]

    async def _online_ollama():
        return True, ["llama3.2:latest"]

    async def _mock_valid_plan(project_id, instruction, intent, candidates, audio_assets):
        from backend.ai_director.sequencer import build_rule_based_storyboard

        return build_rule_based_storyboard(project_id, intent, candidates[:1], audio_assets)

    monkeypatch.setattr(director_mod, "check_ollama_status", _online_ollama)
    monkeypatch.setattr(director_mod, "plan_with_ollama", _mock_valid_plan)

    res_ok = client.post(
        "/api/v1/director/plan",
        json={"project_id": "proj_llm", "instruction": "Make a travel film"},
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["engine_used"] == "ollama"
    assert len(res_ok.json()["timeline"]["video_clips"]) == 1
    assert first_cid is not None

    # Simulate malformed/empty Ollama output -> must gracefully recover via rule_fallback
    async def _mock_failed_ollama(*_args, **_kwargs):
        return None

    monkeypatch.setattr(director_mod, "plan_with_ollama", _mock_failed_ollama)
    res_fb = client.post(
        "/api/v1/director/plan",
        json={"project_id": "proj_llm", "instruction": "Make a travel film"},
    )
    assert res_fb.status_code == 200
    assert res_fb.json()["engine_used"] == "rule_fallback"
