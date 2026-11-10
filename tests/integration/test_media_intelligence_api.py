"""Integration tests for Phase 3 PySceneDetect splitting, CV scoring, deduplication, and search."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from backend.video_engine.ffmpeg_runner import run_ffmpeg_sync


def _make_multiscene_mp4(out_path: Path, tmp_dir: Path) -> Path:
    """Create a 3.6s MP4 with 3 sharp visual cuts: testsrc -> blue -> bright gold."""
    seg1 = tmp_dir / "seg1.mp4"
    seg2 = tmp_dir / "seg2.mp4"
    seg3 = tmp_dir / "seg3.mp4"
    for seg, src in (
        (seg1, "testsrc=size=480x270:rate=30:duration=1.2"),
        (seg2, "color=c=#1E3A8A:size=480x270:rate=30:duration=1.2"),
        (seg3, "testsrc2=size=480x270:rate=30:duration=1.2"),
    ):
        run_ffmpeg_sync(
            [
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                src,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(seg),
            ],
            timeout=20,
        )

    run_ffmpeg_sync(
        [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(seg1),
            "-i",
            str(seg2),
            "-i",
            str(seg3),
            "-filter_complex",
            "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]",
            "-map",
            "[v]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(out_path),
        ],
        timeout=30,
    )
    return out_path


def _write_crisp_sunset_png(path: Path) -> Path:
    img = np.zeros((320, 480, 3), dtype=np.uint8)
    for y in range(320):
        # Warm golden sky gradient + crisp dark silhouettes
        r = int(240 - (y / 320.0) * 100)
        g = int(170 - (y / 320.0) * 110)
        b = int(60 - (y / 320.0) * 40)
        img[y, :] = (b, g, r)
    # Sharp geometric skyline silhouette for real edge sharpness
    for idx, x in enumerate(range(20, 440, 55)):
        h = 90 + (idx % 3) * 35
        cv2.rectangle(img, (x, 320 - h), (x + 38, 320), (20, 20, 28), -1)
    cv2.imwrite(str(path), img)
    return path


def test_multiscene_splitting_deduplication_and_search_api(isolated_env) -> None:
    client, settings, tmp_path = isolated_env

    work = tmp_path / "inputs"
    work.mkdir()
    multi_mp4 = _make_multiscene_mp4(work / "fest_cuts.mp4", work)
    sharp_png = _write_crisp_sunset_png(work / "sunset_skyline_sharp.png")
    dup_png = _write_crisp_sunset_png(work / "sunset_skyline_copy.png")

    # Dark heavily blurred image for negative quality comparison
    dark_blur = cv2.GaussianBlur(
        (cv2.imread(str(sharp_png)) * 0.25).astype(np.uint8),
        (31, 31),
        sigmaX=11.0,
    )
    dark_path = work / "dark_blurred_shot.png"
    cv2.imwrite(str(dark_path), dark_blur)

    res = client.post(
        "/api/v1/media/upload",
        files=[
            ("files", ("fest_cuts.mp4", multi_mp4.read_bytes(), "video/mp4")),
            ("files", ("sunset_skyline_sharp.png", sharp_png.read_bytes(), "image/png")),
            ("files", ("sunset_skyline_copy.png", dup_png.read_bytes(), "image/png")),
            ("files", ("dark_blurred_shot.png", dark_path.read_bytes(), "image/png")),
        ],
    )
    assert res.status_code == 200
    uploaded = res.json()["uploaded"]
    assert len(uploaded) == 4
    by_name = {a["original_filename"]: a for a in uploaded}

    # 1. Verify PySceneDetect detected multiple scenes in fest_cuts.mp4
    fest = by_name["fest_cuts.mp4"]
    assert len(fest["scenes"]) >= 2
    assert fest["scenes"][0]["start_seconds"] < fest["scenes"][0]["end_seconds"]
    scenes_res = client.get(f"/api/v1/media/{fest['id']}/scenes")
    assert scenes_res.status_code == 200
    assert len(scenes_res.json()) == len(fest["scenes"])
    # Confirm scene thumbnail generated on disk
    first_thumb_name = Path(fest["scenes"][0]["thumbnail_url"]).name
    assert (settings.PROXY_DIR / first_thumb_name).is_file()

    # 2. Verify transparent quality scoring separates sharp vs dark blurred
    sharp_asset = by_name["sunset_skyline_sharp.png"]
    dark_asset = by_name["dark_blurred_shot.png"]
    assert sharp_asset["analysis"]["quality"]["overall_score"] > dark_asset["analysis"]["quality"]["overall_score"] + 15.0
    assert "Blurry focus" in dark_asset["analysis"]["quality"]["explanation"]
    assert len(sharp_asset["analysis"]["quality"]["dominant_colors"]) == 3

    # 3. Verify perceptual dHash flagged sunset_skyline_copy.png as duplicate of sunset_skyline_sharp.png
    dup_asset = by_name["sunset_skyline_copy.png"]
    assert dup_asset["analysis"]["duplicate_of_id"] == sharp_asset["id"]
    assert dup_asset["analysis"]["similarity_percent"] >= 95.0
    assert "Near-Duplicate" in dup_asset["tags"]

    # 4. Verify natural-language search & ranking API
    search_res = client.get("/api/v1/media/search", params={"q": "best sunset", "exclude_duplicates": "true"})
    assert search_res.status_code == 200
    search_body = search_res.json()
    found_ids = [item["id"] for item in search_body["results"]]
    assert sharp_asset["id"] in found_ids
    assert dup_asset["id"] not in found_ids
    # Sharp skyline ranks above dark blurred skyline
    if dark_asset["id"] in found_ids:
        assert found_ids.index(sharp_asset["id"]) < found_ids.index(dark_asset["id"])

    # 5. Verify re-analyze endpoint works idempotently
    re_res = client.post(f"/api/v1/media/{sharp_asset['id']}/analyze")
    assert re_res.status_code == 200
    assert re_res.json()["analysis"]["quality"]["overall_score"] == sharp_asset["analysis"]["quality"]["overall_score"]
