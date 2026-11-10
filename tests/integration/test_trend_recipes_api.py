"""Integration tests for Trend Intelligence endpoints, ephemeral uploads, SSRF guards, and Director style transfer."""

from __future__ import annotations

from pathlib import Path

from backend.video_engine.ffmpeg_runner import run_ffmpeg_sync
from tests.conftest import create_synthetic_image, create_synthetic_video


def test_trend_recipes_upload_ssrf_director_and_apply_history(isolated_env) -> None:
    client, settings, tmp_path = isolated_env

    # 1. Seeded curated recipes exist & builtins cannot be deleted
    list_res = client.get("/api/v1/trends/recipes")
    assert list_res.status_code == 200
    recipes = list_res.json()
    assert len(recipes) >= 5
    builtin_ids = {r["id"] for r in recipes}
    assert "recipe_viral_reel_9x16" in builtin_ids
    assert "recipe_bleach_docu" in builtin_ids

    del_builtin = client.delete("/api/v1/trends/recipes/recipe_viral_reel_9x16")
    assert del_builtin.status_code == 403

    # 2. Ephemeral reference video upload analysis (must extract telemetry & delete temp video file!)
    src_dir = tmp_path / "trend_inputs"
    src_dir.mkdir()
    ref_mp4 = src_dir / "ref_style.mp4"
    run_ffmpeg_sync(
        [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=s=640x360:r=30:d=1.5",
            "-f",
            "lavfi",
            "-i",
            "smptebars=s=640x360:r=30:d=1.5",
            "-filter_complex",
            "[0:v][1:v]concat=n=2:v=1:a=0[vout]",
            "-map",
            "[vout]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(ref_mp4),
        ],
        timeout=30,
    )
    up_style_res = client.post(
        "/api/v1/trends/analyze-upload",
        files={"file": ("ref_style.mp4", ref_mp4.read_bytes(), "video/mp4")},
        data={"recipe_name": "Extracted Hackathon Cut"},
    )
    assert up_style_res.status_code == 200
    extracted = up_style_res.json()
    assert extracted["name"] == "Extracted Hackathon Cut"
    assert extracted["source_type"] == "uploaded_reference"
    assert extracted["cuts_per_minute"] > 0
    assert extracted["motion_velocity_score"] > 0
    assert extracted["safety_audit"]["copyright_safe"] is True
    assert extracted["safety_audit"]["media_downloaded"] is False
    assert extracted["safety_audit"]["raw_frames_retained"] is False
    assert list(settings.CACHE_DIR.glob("trend_ref_*")) == []

    # Reject image uploads cleanly on reference video endpoint
    img_png = create_synthetic_image(src_dir / "not_video.png")
    bad_ref = client.post(
        "/api/v1/trends/analyze-upload",
        files={"file": ("not_video.png", img_png.read_bytes(), "image/png")},
    )
    assert bad_ref.status_code == 422

    # 3. Safe URL pattern analysis & strict SSRF / scheme enforcement
    assert (
        client.post(
            "/api/v1/trends/analyze-url",
            json={"reference_url": "http://127.0.0.1:8000/secret"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/trends/analyze-url",
            json={"reference_url": "http://169.254.169.254/latest/meta-data"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/trends/analyze-url",
            json={"reference_url": "file:///C:/Windows/win.ini"},
        ).status_code
        == 400
    )

    url_res = client.post(
        "/api/v1/trends/analyze-url",
        json={
            "reference_url": "https://example.com/reels/bmsit-utsav-aftermovie",
            "recipe_name": "Campus Reel Blueprint",
            "style_notes": "Fast vertical cuts with bleach bypass look and vignette",
        },
    )
    assert url_res.status_code == 200
    url_recipe = url_res.json()
    assert url_recipe["recommended_aspect_ratio"] == "9:16"
    assert url_recipe["recommended_color_grade"] == "bleach_bypass"
    assert url_recipe["cinematic_effects"]["vignette"] is True
    assert url_recipe["safety_audit"]["media_downloaded"] is False

    # Custom user recipes can be deleted cleanly
    assert client.delete(f"/api/v1/trends/recipes/{url_recipe['id']}").status_code == 200

    # 4. Ingest two distinct user clips & test Director plan + 1-click recipe apply + Undo/Redo
    vid1 = create_synthetic_video(src_dir / "clip1.mp4", duration=3.0, with_audio=True)
    vid2 = src_dir / "clip2.mp4"
    run_ffmpeg_sync(
        [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "rgbtestsrc=s=640x360:r=30:d=3.0",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(vid2),
        ],
        timeout=20,
    )
    ing_res = client.post(
        "/api/v1/media/upload",
        files=[
            ("files", ("clip1.mp4", vid1.read_bytes(), "video/mp4")),
            ("files", ("clip2.mp4", vid2.read_bytes(), "video/mp4")),
        ],
    )
    assert ing_res.status_code == 200
    v1_asset = ing_res.json()["uploaded"][0]

    # Test analyze-media on ingested video
    am_res = client.post(f"/api/v1/trends/analyze-media/{v1_asset['id']}")
    assert am_res.status_code == 200

    # Test Director plan driven by style_recipe_id
    dir_res = client.post(
        "/api/v1/director/plan",
        json={
            "project_id": "proj_trend_01",
            "instruction": "Create a campus montage",
            "use_llm": False,
            "style_recipe_id": "recipe_viral_reel_9x16",
        },
    )
    assert dir_res.status_code == 200
    tl = dir_res.json()["timeline"]
    assert tl["aspect_ratio"] == "9:16"
    assert tl["color_grade"] == "cinematic_teal_orange"
    assert any(c["speed_ramp"] == "slow_to_fast" for c in tl["video_clips"])

    # Apply Bleach Docu recipe onto timeline & verify Undo restores 9:16 Viral Reel state
    apply_res = client.post(
        "/api/v1/trends/recipes/recipe_bleach_docu/apply",
        json={"project_id": "proj_trend_01", "timeline": tl, "record_history": True},
    )
    assert apply_res.status_code == 200
    applied = apply_res.json()
    assert applied["timeline"]["color_grade"] == "bleach_bypass"
    assert applied["timeline"]["aspect_ratio"] == "21:9"
    assert applied["timeline"]["cinematic_effects"]["film_grain"] is True
    assert applied["can_undo"] is True

    undo_res = client.post("/api/v1/projects/proj_trend_01/undo")
    assert undo_res.status_code == 200
    assert undo_res.json()["timeline"]["aspect_ratio"] == "9:16"
    assert undo_res.json()["timeline"]["color_grade"] == "cinematic_teal_orange"

