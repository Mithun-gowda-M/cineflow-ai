"""Integration test verifying live HD showcase loading, project hydration, benchmarks, and MP4 export."""

from __future__ import annotations

import time


def test_showcase_status_load_idempotency_and_benchmark_api(isolated_env) -> None:
    client, _settings, _tmp = isolated_env

    # 1. Inspect showcase readiness cleanly inside isolated workspace
    status_res = client.get("/api/v1/showcase/status")
    assert status_res.status_code == 200
    status_body = status_res.json()
    assert status_body["showcase_project_id"] == "proj_bmsit_showcase_2026"
    assert status_body["sample_pack_ready"] is True
    assert status_body["project_loaded"] is False
    assert len(status_body["sample_files"]) == 5

    # 2. Load showcase project via real FFprobe + OpenCV + PySceneDetect + Librosa ingestion
    load_res = client.post("/api/v1/showcase/load", json={"force_reset": False})
    assert load_res.status_code == 200, load_res.text
    loaded = load_res.json()
    assert loaded["newly_ingested"] is True
    proj = loaded["project"]
    assert proj["id"] == "proj_bmsit_showcase_2026"
    assert len(loaded["assets"]) == 5
    assert proj["timeline"] is not None
    assert len(proj["timeline"]["video_clips"]) == 4
    assert len(proj["timeline"]["audio_tracks"]) == 1
    assert len(proj["timeline"]["subtitles"]) >= 2

    # Confirm real scene detection ran on ingested HD clips
    video_assets = [a for a in loaded["assets"] if a["media_kind"] == "video"]
    assert sum(len(a["scenes"]) for a in video_assets) >= 4

    # 3. Verify idempotency when calling /showcase/load again
    second_res = client.post("/api/v1/showcase/load", json={"force_reset": False})
    assert second_res.status_code == 200
    assert second_res.json()["newly_ingested"] is False

    # 4. Verify project deep-link hydration endpoint used by /editor?projectId=...
    proj_get = client.get("/api/v1/projects/proj_bmsit_showcase_2026")
    assert proj_get.status_code == 200
    assert proj_get.json()["title"] == proj["title"]

    # 5. Verify saved benchmark metrics API
    bench_res = client.get("/api/v1/showcase/benchmarks")
    assert bench_res.status_code == 200
    bench = bench_res.json()
    assert bench["cold_render_seconds"] > 0
    assert bench["warm_cached_render_seconds"] > 0
    assert bench["cache_speedup_percent"] > 0

    # 6. Verify hydrated showcase timeline renders cleanly to a real H.264/AAC MP4
    submit_res = client.post(
        "/api/v1/render",
        json={
            "timeline": proj["timeline"],
            "resolution": "720p",
            "encoder_preference": "auto",
            "partial_cache": True,
        },
    )
    assert submit_res.status_code == 202, submit_res.text
    job_id = submit_res.json()["job_id"]

    deadline = time.time() + 120
    final_status = None
    while time.time() < deadline:
        poll = client.get(f"/api/v1/render/{job_id}")
        assert poll.status_code == 200
        body = poll.json()
        if body["status"] in {"completed", "failed", "cancelled"}:
            final_status = body
            break
        time.sleep(0.5)

    assert final_status is not None and final_status["status"] == "completed", final_status
    dl = client.get(f"/api/v1/render/{job_id}/download")
    assert dl.status_code == 200
    assert b"ftyp" in dl.content[:64]

