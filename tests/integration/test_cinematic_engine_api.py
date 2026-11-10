"""Integration tests for Phase 5 Librosa audio endpoints, beat-sync alignment, and full cinematic MP4 renders."""

from __future__ import annotations

import time
import wave
from pathlib import Path

import numpy as np

from backend.media_analysis.probe import probe_media_file
from backend.video_engine.ffmpeg_runner import run_ffmpeg_sync
from tests.conftest import create_synthetic_image, create_synthetic_video


def _create_rhythmic_click_wav(out_path: Path, *, bpm: float = 120.0, duration: float = 6.0) -> Path:
    sr = 22050
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


def test_audio_endpoints_beat_sync_and_cinematic_mp4_render(isolated_env) -> None:
    client, _settings, tmp_path = isolated_env

    src_dir = tmp_path / "cinematic_inputs"
    src_dir.mkdir()
    vid_audio = create_synthetic_video(
        src_dir / "hero_speech.mp4", width=640, height=360, duration=4.0, with_audio=True
    )
    # Distinct visual pattern (smptebars) so perceptual dHash does not mark it as duplicate of testsrc
    vid_silent = src_dir / "broll_silent.mp4"
    run_ffmpeg_sync(
        [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "smptebars=size=640x360:rate=30:duration=3.0",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(vid_silent),
        ],
        timeout=30,
    )
    img_card = create_synthetic_image(src_dir / "poster.png", width=800, height=600)
    music_wav = _create_rhythmic_click_wav(src_dir / "rhythm_120bpm.wav", bpm=120.0, duration=6.0)

    up_res = client.post(
        "/api/v1/media/upload",
        files=[
            ("files", ("hero_speech.mp4", vid_audio.read_bytes(), "video/mp4")),
            ("files", ("broll_silent.mp4", vid_silent.read_bytes(), "video/mp4")),
            ("files", ("poster.png", img_card.read_bytes(), "image/png")),
            ("files", ("rhythm_120bpm.wav", music_wav.read_bytes(), "audio/wav")),
        ],
    )
    assert up_res.status_code == 200
    uploaded = {a["original_filename"]: a for a in up_res.json()["uploaded"]}

    wav_asset = uploaded["rhythm_120bpm.wav"]
    vid_asset = uploaded["hero_speech.mp4"]
    silent_asset = uploaded["broll_silent.mp4"]
    img_asset = uploaded["poster.png"]

    # Auto-analyzed upon upload via media pipeline
    assert wav_asset["audio_analysis"] is not None
    assert len(wav_asset["audio_analysis"]["waveform_peaks"]) == 64
    assert wav_asset["audio_analysis"]["tempo_bpm"] > 0

    # Dedicated GET/POST audio analysis endpoints & validation guards
    get_aud = client.get(f"/api/v1/audio/{wav_asset['id']}/analysis")
    assert get_aud.status_code == 200
    assert len(get_aud.json()["waveform_peaks"]) == 64

    post_aud = client.post(f"/api/v1/audio/{wav_asset['id']}/analyze")
    assert post_aud.status_code == 200
    assert any("BPM" in tag for tag in post_aud.json()["tags"])

    assert client.post(f"/api/v1/audio/{img_asset['id']}/analyze").status_code == 422
    assert client.post(f"/api/v1/audio/{silent_asset['id']}/analyze").status_code == 422
    assert client.get("/api/v1/audio/nonexistent_id/analysis").status_code == 404

    # AI Director automatic beat sync
    dir_res = client.post(
        "/api/v1/director/plan",
        json={
            "project_id": "proj_phase5",
            "instruction": "Create an energetic teaser synced to the music beats",
            "target_duration_seconds": 6.0,
            "use_llm": False,
            "beat_sync": True,
        },
    )
    assert dir_res.status_code == 200
    plan_data = dir_res.json()
    assert len(plan_data["timeline"]["video_clips"]) >= 2
    assert len(plan_data["timeline"]["audio_tracks"]) == 1

    # Explicit beat-sync API call on an off-beat timeline
    sync_timeline = {
        "project_id": "proj_phase5",
        "title": "Beat Sync Test",
        "aspect_ratio": "16:9",
        "fps": 30,
        "color_grade": "bleach_bypass",
        "cinematic_effects": {
            "vignette": True,
            "film_grain": True,
            "ken_burns_on_images": True,
            "audio_ducking": True,
            "loudness_normalize": True,
        },
        "video_clips": [
            {
                "clip_id": "clip_1",
                "source_id": vid_asset["id"],
                "source_filename": "hero_speech.mp4",
                "source_url": vid_asset["source_url"],
                "start_time_seconds": 0.0,
                "end_time_seconds": 3.0,
                "timeline_start_seconds": 0.0,
                "duration_seconds": 2.95,
                "playback_speed": 1.0,
                "speed_ramp": "fast_to_slow",
                "transition_in": {"type": "fade_from_black", "duration_seconds": 0.4},
            },
            {
                "clip_id": "clip_2",
                "source_id": img_asset["id"],
                "source_filename": "poster.png",
                "source_url": img_asset["source_url"],
                "start_time_seconds": 0.0,
                "end_time_seconds": 2.5,
                "timeline_start_seconds": 2.6,
                "duration_seconds": 2.5,
                "playback_speed": 1.0,
                "speed_ramp": "none",
                "transition_in": {"type": "crossfade", "duration_seconds": 0.4},
            },
        ],
        "audio_tracks": [
            {
                "id": "aud_1",
                "name": "rhythm_120bpm.wav",
                "source_id": wav_asset["id"],
                "source_url": wav_asset["source_url"],
                "volume": 0.85,
                "start_time_seconds": 0.0,
                "timeline_start_seconds": 0.0,
                "duration_seconds": 5.5,
                "ducking_enabled": True,
                "duck_volume": 0.35,
            }
        ],
        "subtitles": [
            {
                "id": "sub_1",
                "start_seconds": 0.4,
                "end_seconds": 2.0,
                "text": "Phase 5 Cinematic Render",
                "style": "cinematic_gold_bottom",
            },
            {
                "id": "sub_2",
                "start_seconds": 2.2,
                "end_seconds": 4.0,
                "text": "BEAT SYNCED",
                "style": "bold_center_reel",
            },
        ],
    }

    sync_res = client.post(
        "/api/v1/audio/beat-sync",
        json={
            "timeline": sync_timeline,
            "audio_source_id": wav_asset["id"],
            "tolerance_seconds": 0.4,
        },
    )
    assert sync_res.status_code == 200
    assert sync_res.json()["tempo_bpm"] > 0

    # Real FFmpeg render with speed ramp + bleach_bypass + vignette + film_grain + Ken Burns + ASS + ducking
    render_res = client.post(
        "/api/v1/render",
        json={
            "timeline": sync_timeline,
            "resolution": "720p",
            "encoder_preference": "cpu",
        },
    )
    assert render_res.status_code == 202
    job_id = render_res.json()["job_id"]

    final_status = _poll_render(client, job_id)
    assert final_status["status"] == "completed", final_status
    assert final_status["output_file_size_bytes"] > 10_000

    dl_res = client.get(f"/api/v1/render/{job_id}/download")
    assert dl_res.status_code == 200
    rendered_mp4 = tmp_path / "cinematic_final.mp4"
    rendered_mp4.write_bytes(dl_res.content)

    probed = probe_media_file(rendered_mp4, is_image=False)
    assert probed.width == 1280
    assert probed.height == 720
    assert probed.has_audio is True
    assert probed.duration_seconds > 3.0

