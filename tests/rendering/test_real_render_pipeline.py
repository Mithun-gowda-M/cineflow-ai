"""End-to-end integration tests executing real FastAPI uploads, FFprobe inspection, and FFmpeg MP4 renders."""

from __future__ import annotations

import time
from pathlib import Path

from backend.media_analysis.probe import probe_media_file
from tests.conftest import (
    create_synthetic_audio,
    create_synthetic_image,
    create_synthetic_video,
)


def _poll_until_done(client, job_id: str, timeout_sec: float = 60.0) -> dict:
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


def test_health_endpoint_reports_ffmpeg_ready(isolated_env) -> None:
    client, _settings, _tmp = isolated_env
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["ffmpeg_available"] is True
    assert body["ffprobe_available"] is True
    assert body["hardware"]["cpu_cores"] >= 1


def test_full_batch_upload_and_real_mp4_renders_landscape_and_portrait(isolated_env) -> None:
    client, settings, tmp_path = isolated_env

    # 1. Generate real heterogeneous media assets via FFmpeg lavfi
    src_dir = tmp_path / "synthetic_inputs"
    src_dir.mkdir()
    vid_landscape = create_synthetic_video(src_dir / "clip_land.mp4", width=640, height=360, duration=2.0, with_audio=True)
    vid_portrait_silent = create_synthetic_video(src_dir / "clip_port.mp4", width=360, height=640, duration=2.0, with_audio=False)
    img_card = create_synthetic_image(src_dir / "card.png", width=800, height=600)
    music_wav = create_synthetic_audio(src_dir / "music.wav", duration=5.0)

    # 2. Batch upload all 4 files via POST /api/v1/media/upload
    files_payload = [
        ("files", ("clip_land.mp4", vid_landscape.read_bytes(), "video/mp4")),
        ("files", ("clip_port.mp4", vid_portrait_silent.read_bytes(), "video/mp4")),
        ("files", ("card.png", img_card.read_bytes(), "image/png")),
        ("files", ("music.wav", music_wav.read_bytes(), "audio/wav")),
    ]
    upload_res = client.post("/api/v1/media/upload", files=files_payload)
    assert upload_res.status_code == 200
    up_data = upload_res.json()
    assert up_data["errors"] == []
    assert len(up_data["uploaded"]) == 4

    by_name = {a["original_filename"]: a for a in up_data["uploaded"]}
    assert by_name["clip_land.mp4"]["metadata"]["width"] == 640
    assert by_name["clip_land.mp4"]["metadata"]["has_audio"] is True
    assert by_name["clip_port.mp4"]["metadata"]["height"] == 640
    assert by_name["clip_port.mp4"]["metadata"]["has_audio"] is False
    assert by_name["card.png"]["media_kind"] == "image"
    assert by_name["music.wav"]["media_kind"] == "audio"

    # Verify thumbnails and 720p/540p proxies were actually written on disk
    assert Path(by_name["clip_land.mp4"]["proxy_path"]).is_file()
    assert (settings.PROXY_DIR / f"{by_name['clip_land.mp4']['id']}_thumb.jpg").is_file()
    assert (settings.PROXY_DIR / f"{by_name['card.png']['id']}_thumb.jpg").is_file()

    # 3. Create & persist project
    proj_res = client.post(
        "/api/v1/projects",
        json={
            "title": "Integration Test Film",
            "aspect_ratio": "16:9",
            "target_duration_seconds": 6.0,
            "color_grade": "golden_hour",
        },
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # 4. Build mixed-media timeline (video w/ audio + silent portrait video + still image + music track)
    timeline_payload = {
        "version": "1.0",
        "project_id": proj_id,
        "title": "Mixed Media Render",
        "aspect_ratio": "16:9",
        "target_duration_seconds": 5.0,
        "fps": 30,
        "color_grade": "golden_hour",
        "video_clips": [
            {
                "clip_id": "c1",
                "source_id": by_name["clip_land.mp4"]["id"],
                "start_time_seconds": 0.0,
                "end_time_seconds": 2.0,
                "timeline_start_seconds": 0.0,
                "duration_seconds": 2.0,
                "playback_speed": 1.0,
                "transition_in": {"type": "fade_from_black", "duration_seconds": 0.3},
                "tags": ["landscape"],
            },
            {
                "clip_id": "c2",
                "source_id": by_name["clip_port.mp4"]["id"],
                "start_time_seconds": 0.0,
                "end_time_seconds": 2.0,
                "timeline_start_seconds": 1.6,
                "duration_seconds": 2.0,
                "playback_speed": 1.0,
                "transition_in": {"type": "crossfade", "duration_seconds": 0.4},
                "tags": ["portrait"],
            },
            {
                "clip_id": "c3",
                "source_id": by_name["card.png"]["id"],
                "start_time_seconds": 0.0,
                "end_time_seconds": 1.8,
                "timeline_start_seconds": 3.2,
                "duration_seconds": 1.8,
                "playback_speed": 1.0,
                "transition_in": {"type": "wipe_left", "duration_seconds": 0.4},
                "transition_out": {"type": "fade_to_black", "duration_seconds": 0.3},
                "tags": ["image"],
            },
        ],
        "audio_tracks": [
            {
                "id": "a_bg",
                "name": "Test Soundtrack",
                "source_id": by_name["music.wav"]["id"],
                "volume": 0.6,
                "start_time_seconds": 0.0,
                "timeline_start_seconds": 0.0,
                "duration_seconds": 5.0,
                "ducking_enabled": True,
                "duck_volume": 0.3,
            }
        ],
        "subtitles": [],
    }

    # 5A. Render 16:9 720p Landscape MP4
    render_16_9 = client.post(
        "/api/v1/render",
        json={"timeline": timeline_payload, "resolution": "720p", "encoder_preference": "cpu"},
    )
    assert render_16_9.status_code == 202
    job_16_9 = _poll_until_done(client, render_16_9.json()["job_id"])
    assert job_16_9["status"] == "completed", job_16_9.get("error_message")
    assert job_16_9["progress_percent"] == 100.0
    assert job_16_9["output_file_size_bytes"] > 1024

    dl_16_9 = client.get(job_16_9["output_video_url"])
    assert dl_16_9.status_code == 200
    assert dl_16_9.headers["content-type"] == "video/mp4"
    out_16_9_path = tmp_path / "downloaded_16_9.mp4"
    out_16_9_path.write_bytes(dl_16_9.content)

    meta_16_9 = probe_media_file(out_16_9_path)
    assert meta_16_9.width == 1280
    assert meta_16_9.height == 720
    assert meta_16_9.codec == "h264"
    assert meta_16_9.has_audio is True
    assert meta_16_9.audio_codec == "aac"
    # Expected duration: 2.0 + 2.0 - 0.4 + 1.8 - 0.4 = 5.0s
    assert 4.6 <= meta_16_9.duration_seconds <= 5.4

    # 5B. Render 9:16 720p Portrait MP4 (Shorts/Reels conforming)
    timeline_9_16 = dict(timeline_payload, aspect_ratio="9:16", color_grade="cinematic_teal_orange")
    render_9_16 = client.post(
        "/api/v1/render",
        json={"timeline": timeline_9_16, "resolution": "720p", "encoder_preference": "cpu"},
    )
    assert render_9_16.status_code == 202
    job_9_16 = _poll_until_done(client, render_9_16.json()["job_id"])
    assert job_9_16["status"] == "completed", job_9_16.get("error_message")

    dl_9_16 = client.get(job_9_16["output_video_url"])
    assert dl_9_16.status_code == 200
    out_9_16_path = tmp_path / "downloaded_9_16.mp4"
    out_9_16_path.write_bytes(dl_9_16.content)

    meta_9_16 = probe_media_file(out_9_16_path)
    assert meta_9_16.width == 720
    assert meta_9_16.height == 1280
    assert meta_9_16.codec == "h264"
    assert meta_9_16.has_audio is True

    # 6. Verify clean asset deletion removes files & proxies
    del_id = by_name["clip_land.mp4"]["id"]
    del_path = Path(by_name["clip_land.mp4"]["file_path"])
    del_proxy = Path(by_name["clip_land.mp4"]["proxy_path"])
    assert del_path.is_file() and del_proxy.is_file()

    del_res = client.delete(f"/api/v1/media/{del_id}")
    assert del_res.status_code == 200
    assert not del_path.exists()
    assert not del_proxy.exists()

