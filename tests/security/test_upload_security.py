"""Security tests covering path traversal, file spoofing, invalid types, and subprocess safety."""

from __future__ import annotations

import inspect

import pytest

from backend.media_analysis.validator import MediaValidationError, sanitize_filename
from backend.video_engine import ffmpeg_runner


def test_sanitize_filename_blocks_path_traversal() -> None:
    with pytest.raises(MediaValidationError):
        sanitize_filename("../../etc/passwd.mp4")

    with pytest.raises(MediaValidationError):
        sanitize_filename("..\\..\\windows\\system32\\cmd.exe")

    with pytest.raises(MediaValidationError):
        sanitize_filename("evil\x00.mp4")


def test_upload_rejects_unsupported_extension(isolated_env) -> None:
    client, _settings, _tmp = isolated_env
    res = client.post(
        "/api/v1/media/upload",
        files=[("files", ("malware.exe", b"MZ\x90\x00not_a_video", "application/octet-stream"))],
    )
    assert res.status_code == 415


def test_upload_rejects_spoofed_mp4_magic_bytes(isolated_env) -> None:
    client, _settings, _tmp = isolated_env
    res = client.post(
        "/api/v1/media/upload",
        files=[("files", ("fake_clip.mp4", b"#!/bin/bash\nrm -rf /\n", "video/mp4"))],
    )
    assert res.status_code == 415


def test_upload_rejects_empty_file(isolated_env) -> None:
    client, _settings, _tmp = isolated_env
    res = client.post(
        "/api/v1/media/upload",
        files=[("files", ("empty.png", b"", "image/png"))],
    )
    assert res.status_code == 400


def test_render_rejects_unknown_media_source_id(isolated_env) -> None:
    client, _settings, _tmp = isolated_env
    res = client.post(
        "/api/v1/render",
        json={
            "resolution": "720p",
            "encoder_preference": "cpu",
            "timeline": {
                "version": "1.0",
                "project_id": "proj_sec_1",
                "title": "Bad Ref",
                "aspect_ratio": "16:9",
                "target_duration_seconds": 3.0,
                "fps": 30,
                "color_grade": "natural",
                "video_clips": [
                    {
                        "clip_id": "c1",
                        "source_id": "media_does_not_exist",
                        "start_time_seconds": 0.0,
                        "end_time_seconds": 2.0,
                        "timeline_start_seconds": 0.0,
                        "duration_seconds": 2.0,
                        "playback_speed": 1.0,
                        "tags": [],
                    }
                ],
                "audio_tracks": [],
                "subtitles": [],
            },
        },
    )
    assert res.status_code == 422


def test_ffmpeg_runner_never_uses_shell_true() -> None:
    source = inspect.getsource(ffmpeg_runner)
    assert "shell=True" not in source

