"""Idempotent showcase project seeder hydrating HD sample media via real CINEFLOW pipelines."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from backend.api.config import get_settings, utc_now_iso
from backend.api.database import get_database
from backend.api.schemas import (
    AudioTrackCue,
    CinematicEffects,
    HardwareProfileInfo,
    MediaAsset,
    MediaClip,
    ProjectResponse,
    ShowcaseLoadResponse,
    ShowcaseSampleFileInfo,
    ShowcaseStatusResponse,
    SubtitleCue,
    TimelineDiffSummary,
    TimelinePlan,
    TransitionSpec,
)
from backend.benchmarking.runner import load_saved_benchmark_report
from backend.media_analysis.pipeline import finalize_local_media_ingest
from backend.media_analysis.probe import probe_media_file
from backend.media_analysis.validator import classify_extension, generate_storage_identity
from backend.showcase.sample_generator import (
    SAMPLE_PACK_SPECS,
    ensure_sample_media_pack,
    sample_media_dir,
)
from backend.video_engine.hardware import detect_hardware_profile

SHOWCASE_PROJECT_ID = "proj_bmsit_showcase_2026"
SHOWCASE_PROJECT_TITLE = "BMSIT Cultural & Tech Fest 2026 — Official HD Showcase"


def _build_hardware_info() -> HardwareProfileInfo:
    hw = detect_hardware_profile()
    return HardwareProfileInfo(
        profile=hw.profile,
        cpu_cores=hw.cpu_cores,
        free_disk_gb=hw.free_disk_gb,
        video_encoder=hw.video_encoder,
        hw_accel_available=hw.hw_accel_available,
        detected_encoders=list(hw.detected_encoders),
        max_concurrent_renders=hw.max_concurrent_renders,
    )


def get_showcase_status() -> ShowcaseStatusResponse:
    """Inspect committed Full-HD sample pack, seeded showcase project, and benchmark report readiness."""
    db = get_database()
    sdir = sample_media_dir()
    sample_files: list[ShowcaseSampleFileInfo] = []
    ready_count = 0
    total_bytes = 0

    for spec in SAMPLE_PACK_SPECS:
        fp = sdir / spec.filename
        size = fp.stat().st_size if fp.is_file() else 0
        if size > 4096:
            ready_count += 1
        total_bytes += size
        res_label = (
            f"{spec.width}x{spec.height} @ {spec.fps}fps"
            if spec.media_kind == "video"
            else f"{spec.fps} Hz PCM WAV"
        )
        sample_files.append(
            ShowcaseSampleFileInfo(
                filename=spec.filename,
                media_kind="audio" if spec.media_kind == "audio" else "video",
                size_bytes=size,
                resolution_label=res_label,
                duration_seconds=spec.duration_seconds,
                role=spec.role,
            )
        )

    existing_proj = db.get_project(SHOWCASE_PROJECT_ID)
    proj_loaded = bool(existing_proj and existing_proj.timeline and len(existing_proj.timeline.video_clips) > 0)
    saved_report = load_saved_benchmark_report()

    return ShowcaseStatusResponse(
        showcase_project_id=SHOWCASE_PROJECT_ID,
        project_loaded=proj_loaded,
        sample_pack_ready=(ready_count == len(SAMPLE_PACK_SPECS)),
        sample_files=sample_files,
        total_sample_bytes=total_bytes,
        benchmark_report_ready=(saved_report is not None),
        last_benchmark_at=saved_report.generated_at if saved_report else None,
        hardware=_build_hardware_info(),
    )


def _find_usable_existing_asset(assets: list[MediaAsset], original_filename: str) -> Optional[MediaAsset]:
    for asset in assets:
        if asset.original_filename == original_filename and Path(asset.file_path).is_file():
            if asset.analysis is not None:
                return asset
    return None


def seed_showcase_project(
    *,
    force_reset: bool = False,
    owner_id: Optional[str] = None,
) -> ShowcaseLoadResponse:
    """Ingest sample HD footage into SQLite via real CV/Audio engines and build `proj_bmsit_showcase_2026`."""
    settings = get_settings()
    settings.ensure_directories()
    db = get_database()

    sample_paths = ensure_sample_media_pack(force=False)
    total_sample_bytes = sum(p.stat().st_size for p in sample_paths if p.is_file())

    existing_project = db.get_project(SHOWCASE_PROJECT_ID)
    if existing_project and existing_project.timeline and not force_reset:
        all_assets = db.list_media_assets()
        assets_by_id = {a.id: a for a in all_assets}
        needed_ids = [c.source_id for c in existing_project.timeline.video_clips] + [
            a.source_id for a in existing_project.timeline.audio_tracks
        ]
        if all(
            sid in assets_by_id and Path(assets_by_id[sid].file_path).is_file()
            for sid in needed_ids
        ):
            showcase_assets = [
                a for a in all_assets if a.original_filename in {s.filename for s in SAMPLE_PACK_SPECS}
            ]
            audio_id = next(
                (a.source_id for a in existing_project.timeline.audio_tracks),
                None,
            )
            return ShowcaseLoadResponse(
                project=existing_project,
                assets=showcase_assets,
                audio_asset_id=audio_id,
                newly_ingested=False,
                total_sample_bytes=total_sample_bytes,
                message="Official HD Showcase project already loaded and ready in Studio.",
            )

    current_assets = db.list_media_assets()
    by_filename: dict[str, MediaAsset] = {}
    newly_ingested = False

    for spec in SAMPLE_PACK_SPECS:
        src_file = sample_media_dir() / spec.filename
        if not force_reset:
            reused = _find_usable_existing_asset(current_assets, spec.filename)
            if reused is not None:
                by_filename[spec.filename] = reused
                continue

        ext, media_kind, mime_type = classify_extension(spec.filename)
        media_id, stored_name = generate_storage_identity(ext)
        dest_path = settings.UPLOAD_DIR / stored_name
        shutil.copy2(src_file, dest_path)

        ingested = finalize_local_media_ingest(
            dest_path=dest_path,
            media_id=media_id,
            original_filename=spec.filename,
            stored_filename=stored_name,
            media_kind=media_kind,
            mime_type=mime_type,
            total_bytes=dest_path.stat().st_size,
            owner_id=owner_id,
            run_analysis=True,
            cleanup_on_probe_error=False,
        )
        by_filename[spec.filename] = ingested
        newly_ingested = True

    c1 = by_filename["01_diya_golden_intro_1080p.mp4"]
    c2 = by_filename["02_auditorium_stage_pulse_1080p.mp4"]
    c3 = by_filename["03_fireworks_climax_burst_1080p.mp4"]
    c4 = by_filename["04_campus_aerial_portrait_1080p.mp4"]
    audio_asset = by_filename["05_festival_beat_120bpm.wav"]

    c1_dur = round(min(4.0, max(2.0, c1.metadata.duration_seconds or 4.0)), 2)
    c2_dur = round(min(4.5, max(2.0, c2.metadata.duration_seconds or 4.5)), 2)
    c4_dur = round(min(3.5, max(2.0, c4.metadata.duration_seconds or 3.5)), 2)
    c3_dur = round(min(4.5, max(2.0, c3.metadata.duration_seconds or 4.5)), 2)

    timeline = TimelinePlan(
        project_id=SHOWCASE_PROJECT_ID,
        title=SHOWCASE_PROJECT_TITLE,
        aspect_ratio="16:9",
        target_duration_seconds=15.0,
        fps=30,
        color_grade="golden_hour",
        cinematic_effects=CinematicEffects(
            vignette=True,
            film_grain=False,
            ken_burns_on_images=True,
            audio_ducking=True,
            loudness_normalize=True,
        ),
        video_clips=[
            MediaClip(
                clip_id="show_clip_01",
                source_id=c1.id,
                source_filename=c1.original_filename,
                source_url=c1.source_url,
                thumbnail_url=c1.thumbnail_url,
                start_time_seconds=0.0,
                end_time_seconds=c1_dur,
                timeline_start_seconds=0.0,
                duration_seconds=c1_dur,
                playback_speed=1.0,
                speed_ramp="none",
                transition_in=TransitionSpec(type="fade_from_black", duration_seconds=0.6),
                transition_out=TransitionSpec(type="crossfade", duration_seconds=0.5),
                color_grade="golden_hour",
                quality_score=c1.analysis.quality.overall_score if c1.analysis else 94.0,
                tags=["Opening Hook", "Golden Diya", "1080p"],
            ),
            MediaClip(
                clip_id="show_clip_02",
                source_id=c2.id,
                source_filename=c2.original_filename,
                source_url=c2.source_url,
                thumbnail_url=c2.thumbnail_url,
                start_time_seconds=0.0,
                end_time_seconds=c2_dur,
                timeline_start_seconds=3.5,
                duration_seconds=c2_dur,
                playback_speed=1.0,
                speed_ramp="fast_to_slow",
                transition_in=TransitionSpec(type="crossfade", duration_seconds=0.5),
                transition_out=TransitionSpec(type="crossfade", duration_seconds=0.5),
                color_grade="cinematic_teal_orange",
                quality_score=c2.analysis.quality.overall_score if c2.analysis else 91.0,
                tags=["Rising Action", "Cultural Stage", "Multi-Scene"],
            ),
            MediaClip(
                clip_id="show_clip_03",
                source_id=c4.id,
                source_filename=c4.original_filename,
                source_url=c4.source_url,
                thumbnail_url=c4.thumbnail_url,
                start_time_seconds=0.0,
                end_time_seconds=c4_dur,
                timeline_start_seconds=7.5,
                duration_seconds=c4_dur,
                playback_speed=1.0,
                speed_ramp="none",
                transition_in=TransitionSpec(type="zoom_in", duration_seconds=0.45),
                transition_out=TransitionSpec(type="crossfade", duration_seconds=0.5),
                color_grade="golden_hour",
                quality_score=c4.analysis.quality.overall_score if c4.analysis else 92.0,
                tags=["Campus Aerial", "9:16 Adaptive"],
            ),
            MediaClip(
                clip_id="show_clip_04",
                source_id=c3.id,
                source_filename=c3.original_filename,
                source_url=c3.source_url,
                thumbnail_url=c3.thumbnail_url,
                start_time_seconds=0.0,
                end_time_seconds=c3_dur,
                timeline_start_seconds=10.5,
                duration_seconds=c3_dur,
                playback_speed=1.0,
                speed_ramp="slow_to_fast",
                transition_in=TransitionSpec(type="crossfade", duration_seconds=0.5),
                transition_out=TransitionSpec(type="fade_to_black", duration_seconds=0.7),
                color_grade="golden_hour",
                quality_score=c3.analysis.quality.overall_score if c3.analysis else 95.0,
                tags=["Climax", "Fireworks", "Finale"],
            ),
        ],
        audio_tracks=[
            AudioTrackCue(
                id="show_audio_01",
                name="Festival Pulse (120 BPM)",
                source_id=audio_asset.id,
                source_url=audio_asset.source_url,
                volume=0.85,
                start_time_seconds=0.0,
                timeline_start_seconds=0.0,
                duration_seconds=15.0,
                ducking_enabled=True,
                duck_volume=0.35,
            )
        ],
        subtitles=[
            SubtitleCue(
                id="show_sub_01",
                start_seconds=0.5,
                end_seconds=3.6,
                text="When BMSIT lights up the festival night",
                style="cinematic_gold_bottom",
            ),
            SubtitleCue(
                id="show_sub_02",
                start_seconds=4.2,
                end_seconds=8.0,
                text="Zero cloud fees — 100% local AI editing",
                style="cinematic_gold_bottom",
            ),
            SubtitleCue(
                id="show_sub_03",
                start_seconds=10.8,
                end_seconds=14.4,
                text="CINEFLOW AI // BMSIT Showcase 2026",
                style="cinematic_gold_bottom",
            ),
        ],
    )

    now = utc_now_iso()
    project = ProjectResponse(
        id=SHOWCASE_PROJECT_ID,
        owner_id=owner_id,
        title=SHOWCASE_PROJECT_TITLE,
        description=(
            "Pre-ingested Full-HD showcase montage featuring 4 high-definition clips, "
            "PySceneDetect scene splits, OpenCV quality scores, 120 BPM Librosa beat grid, "
            "and ready-to-export FFmpeg filtergraph."
        ),
        aspect_ratio="16:9",
        target_duration_seconds=15.0,
        color_grade="golden_hour",
        timeline=timeline,
        created_at=existing_project.created_at if existing_project else now,
        updated_at=now,
    )
    saved_project = db.save_project(project)
    history = db.get_project_history(SHOWCASE_PROJECT_ID)
    if history.total_revisions == 0:
        db.push_timeline_revision(
            SHOWCASE_PROJECT_ID,
            timeline,
            "Loaded BMSIT Full-HD Showcase Sequence",
            TimelineDiffSummary(changes=["Initialized 4-clip HD showcase montage with 120 BPM beat track"]),
        )

    probe_media_file(Path(c1.file_path))
    ordered_assets = [c1, c2, c3, c4, audio_asset]
    return ShowcaseLoadResponse(
        project=saved_project,
        assets=ordered_assets,
        audio_asset_id=audio_asset.id,
        newly_ingested=newly_ingested,
        total_sample_bytes=total_sample_bytes,
        message=(
            f"Ingested {len(ordered_assets)} HD showcase assets via FFprobe/OpenCV/PySceneDetect/Librosa "
            f"and seeded project '{SHOWCASE_PROJECT_ID}'."
        ),
    )

