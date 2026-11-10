"""End-to-end CINEFLOW AI pipeline benchmark runner with real `psutil` and FFmpeg measurements."""

from __future__ import annotations

import asyncio
import json
import os
import platform
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

import psutil

from backend.api import config as config_mod
from backend.api import database as db_mod
from backend.api.schemas import (
    AudioTrackCue,
    BenchmarkStageResult,
    CinematicEffects,
    HardwareProfileInfo,
    MediaAsset,
    MediaClip,
    RenderRequest,
    ShowcaseBenchmarkReport,
    SubtitleCue,
    TimelinePlan,
    TransitionSpec,
)
from backend.audio_engine.analyzer import analyze_audio_file
from backend.media_analysis.pipeline import finalize_local_media_ingest
from backend.media_analysis.probe import probe_media_file
from backend.media_analysis.validator import classify_extension, generate_storage_identity
from backend.rendering.renderer import execute_render_job
from backend.showcase.sample_generator import ensure_sample_media_pack
from backend.video_engine.ffmpeg_runner import clear_binary_cache, get_binary_info
from backend.video_engine.hardware import detect_hardware_profile


def benchmark_report_paths() -> tuple[Path, Path]:
    root = config_mod._default_repo_root()
    bench_dir = root / "docs" / "benchmarks"
    return bench_dir / "BENCHMARK_REPORT.json", bench_dir / "BENCHMARK_REPORT.md"


def load_saved_benchmark_report() -> ShowcaseBenchmarkReport | None:
    json_path, _ = benchmark_report_paths()
    if not json_path.is_file():
        return None
    try:
        return ShowcaseBenchmarkReport.model_validate_json(json_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _measure_process_snapshot(proc: psutil.Process) -> tuple[float, float]:
    cpu = proc.cpu_percent(interval=None)
    rss_mb = round(proc.memory_info().rss / (1024 * 1024), 1)
    return round(float(cpu), 1), rss_mb


def _format_markdown_report(report: ShowcaseBenchmarkReport) -> str:
    hw = report.hardware_profile
    lines = [
        "# CINEFLOW AI — Verified Pipeline & Hardware Benchmark Report",
        "",
        f"> **Generated At:** `{report.generated_at}`  ",
        f"> **Host Environment:** `{report.host_os}` | Python `{report.python_version}` | {report.cpu_cores} Logical Cores | {report.ram_total_gb:.1f} GB RAM  ",
        f"> **FFmpeg Binary:** `{report.ffmpeg_version}`  ",
        f"> **Hardware Profile:** `{hw.profile}` (`{hw.video_encoder}`, working encoders: `{', '.join(hw.detected_encoders)}`)",
        "",
        "Every metric below was recorded directly on this machine using real 1920x1080 Full-HD showcase clips and 120 BPM audio — zero mocked timings.",
        "",
        "## 1. Stage-by-Stage Throughput Summary",
        "",
        "| Stage | Wall Time (s) | Throughput | Process CPU (%) | Process RSS (MB) | Notes |",
        "| :--- | ---: | :--- | ---: | ---: | :--- |",
    ]
    for st in report.stages:
        lines.append(
            f"| {st.stage_name} | {st.duration_seconds:.3f} | {st.throughput_label} | "
            f"{st.cpu_percent_avg:.1f}% | {st.memory_rss_mb:.1f} | {st.notes} |"
        )

    lines.extend(
        [
            "",
            "## 2. Cold 1080p Render vs. SHA-256 Partial Segment Cache",
            "",
            "| Metric | Measured Value |",
            "| :--- | :--- |",
            f"| **16:9 1080p Multi-Clip Cold Render** | **{report.cold_render_seconds:.3f} s** |",
            f"| **16:9 1080p Warm Partial Re-render** | **{report.warm_cached_render_seconds:.3f} s** ({report.segment_cache_hits} cache hits / {report.segment_cache_misses} rebuild) |",
            f"| **Partial Cache Speedup** | **{report.cache_speedup_percent:.1f}% faster** vs. cold build |",
            f"| **Output Duration & Speed Ratio** | {report.output_duration_seconds:.2f} s final MP4 (**{report.realtime_speedup_x:.2f}x realtime**) |",
            f"| **Portrait 9:16 (1080x1920) Render** | **{report.portrait_render_seconds:.3f} s** |",
            f"| **Final H.264/AAC MP4 Size** | {report.output_file_bytes / (1024 * 1024):.2f} MB |",
            "",
            "## 3. Reproducing These Benchmarks",
            "",
            "```powershell",
            "backend\\.venv\\Scripts\\python.exe -m backend.benchmarking.runner",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


async def _run_isolated_benchmarks_async() -> ShowcaseBenchmarkReport:
    sample_paths = ensure_sample_media_pack(force=False)
    proc = psutil.Process(os.getpid())
    proc.cpu_percent(interval=None)

    orig_env = {
        key: os.environ.get(key)
        for key in (
            "DATA_DIR",
            "UPLOAD_DIR",
            "PROXY_DIR",
            "RENDER_DIR",
            "CACHE_DIR",
            "PROJECTS_DIR",
            "DATABASE_PATH",
        )
    }

    with tempfile.TemporaryDirectory(prefix="cineflow_bench_") as tmp_root_str:
        tmp_data = Path(tmp_root_str) / "data"
        os.environ["DATA_DIR"] = str(tmp_data)
        os.environ["UPLOAD_DIR"] = str(tmp_data / "uploads")
        os.environ["PROXY_DIR"] = str(tmp_data / "proxies")
        os.environ["RENDER_DIR"] = str(tmp_data / "renders")
        os.environ["CACHE_DIR"] = str(tmp_data / "cache")
        os.environ["PROJECTS_DIR"] = str(tmp_data / "projects")
        os.environ["DATABASE_PATH"] = str(tmp_data / "bench.db")

        config_mod.get_settings.cache_clear()
        detect_hardware_profile.cache_clear()
        clear_binary_cache()
        db_mod._db_instance = None

        try:
            settings = config_mod.get_settings()
            settings.ensure_directories()
            db_mod.get_database()

            hw = detect_hardware_profile()
            bins = get_binary_info()
            hw_info = HardwareProfileInfo(
                profile=hw.profile,
                cpu_cores=hw.cpu_cores,
                free_disk_gb=hw.free_disk_gb,
                video_encoder=hw.video_encoder,
                hw_accel_available=hw.hw_accel_available,
                detected_encoders=list(hw.detected_encoders),
                max_concurrent_renders=hw.max_concurrent_renders,
            )

            stages: list[BenchmarkStageResult] = []
            ingested_videos: list[MediaAsset] = []
            audio_asset: MediaAsset | None = None
            video_paths = [p for p in sample_paths if p.suffix.lower() == ".mp4"]
            audio_paths = [p for p in sample_paths if p.suffix.lower() == ".wav"]

            # Stage 1: FFprobe inspection + 720p proxy & thumbnail transcode (analysis skipped here so Stage 2 measures CV cleanly)
            proc.cpu_percent(interval=None)
            t0 = time.perf_counter()
            for vp in video_paths:
                ext, kind, mime = classify_extension(vp.name)
                media_id, stored_name = generate_storage_identity(ext)
                dest = settings.UPLOAD_DIR / stored_name
                shutil.copy2(vp, dest)
                asset = finalize_local_media_ingest(
                    dest_path=dest,
                    media_id=media_id,
                    original_filename=vp.name,
                    stored_filename=stored_name,
                    media_kind=kind,
                    mime_type=mime,
                    total_bytes=dest.stat().st_size,
                    run_analysis=False,
                )
                ingested_videos.append(asset)
            dt_ingest = max(time.perf_counter() - t0, 0.001)
            cpu_ingest, rss_ingest = _measure_process_snapshot(proc)
            stages.append(
                BenchmarkStageResult(
                    stage_id="ingest_probe_proxy",
                    stage_name="FFprobe & 720p Proxy Generation",
                    duration_seconds=round(dt_ingest, 3),
                    throughput_label=f"{len(ingested_videos)} HD clips in {dt_ingest:.2f}s ({len(ingested_videos) / dt_ingest:.2f} clips/s)",
                    cpu_percent_avg=cpu_ingest,
                    memory_rss_mb=rss_ingest,
                    notes=f"3x 1920x1080 + 1x 1080x1920 -> 720p proxies ({hw.video_encoder})",
                )
            )

            # Stage 2: OpenCV Blur/Exposure + PySceneDetect Cut Analysis
            from backend.media_analysis.pipeline import analyze_media_asset

            proc.cpu_percent(interval=None)
            t0 = time.perf_counter()
            analyzed_videos: list[MediaAsset] = []
            for asset in ingested_videos:
                analyzed_videos.append(analyze_media_asset(asset, existing_assets=analyzed_videos))
            dt_cv = max(time.perf_counter() - t0, 0.001)
            cpu_cv, rss_cv = _measure_process_snapshot(proc)
            total_scenes = sum(len(a.scenes) for a in analyzed_videos)
            avg_quality = round(
                sum(a.analysis.quality.overall_score for a in analyzed_videos if a.analysis) / max(len(analyzed_videos), 1),
                1,
            )
            stages.append(
                BenchmarkStageResult(
                    stage_id="cv_scene_analysis",
                    stage_name="OpenCV CV Scoring & PySceneDetect",
                    duration_seconds=round(dt_cv, 3),
                    throughput_label=f"{len(analyzed_videos) / dt_cv:.2f} clips/s ({total_scenes} scenes)",
                    cpu_percent_avg=cpu_cv,
                    memory_rss_mb=rss_cv,
                    notes=f"Mean quality score {avg_quality}/100 across 1080p footage",
                )
            )

            # Stage 3: Librosa BPM & Beat Grid Intelligence
            proc.cpu_percent(interval=None)
            t0 = time.perf_counter()
            ap = audio_paths[0]
            ext_a, kind_a, mime_a = classify_extension(ap.name)
            a_id, a_stored = generate_storage_identity(ext_a)
            dest_a = settings.UPLOAD_DIR / a_stored
            shutil.copy2(ap, dest_a)
            audio_asset = finalize_local_media_ingest(
                dest_path=dest_a,
                media_id=a_id,
                original_filename=ap.name,
                stored_filename=a_stored,
                media_kind=kind_a,
                mime_type=mime_a,
                total_bytes=dest_a.stat().st_size,
                run_analysis=False,
            )
            audio_result = analyze_audio_file(dest_a)
            dt_audio = max(time.perf_counter() - t0, 0.001)
            cpu_audio, rss_audio = _measure_process_snapshot(proc)
            stages.append(
                BenchmarkStageResult(
                    stage_id="librosa_beat_sync",
                    stage_name="Librosa Tempo & Beat Tracking",
                    duration_seconds=round(dt_audio, 3),
                    throughput_label=f"{audio_result.duration_seconds / dt_audio:.2f}x realtime ({audio_result.tempo_bpm:.1f} BPM)",
                    cpu_percent_avg=cpu_audio,
                    memory_rss_mb=rss_audio,
                    notes=f"{len(audio_result.beat_timestamps)} beats detected on {audio_result.duration_seconds:.1f}s track",
                )
            )

            # Prepare 3 landscape clips for 16:9 1080p Cold vs Warm Partial Cache render
            landscape_clips = analyzed_videos[:3]
            clips_v1 = [
                MediaClip(
                    clip_id=f"bench_clip_{idx + 1}",
                    source_id=a.id,
                    source_filename=a.original_filename,
                    source_url=a.source_url,
                    thumbnail_url=a.thumbnail_url,
                    start_time_seconds=0.0,
                    end_time_seconds=3.5,
                    timeline_start_seconds=round(idx * 3.0, 2),
                    duration_seconds=3.5,
                    playback_speed=1.0,
                    transition_in=TransitionSpec(
                        type="fade_from_black" if idx == 0 else "crossfade",
                        duration_seconds=0.45,
                    ),
                    color_grade="golden_hour",
                    quality_score=a.analysis.quality.overall_score if a.analysis else 90.0,
                )
                for idx, a in enumerate(landscape_clips)
            ]
            cold_timeline = TimelinePlan(
                project_id="proj_bench_16_9",
                title="Benchmark 16:9 Showcase",
                aspect_ratio="16:9",
                target_duration_seconds=9.5,
                fps=30,
                color_grade="golden_hour",
                cinematic_effects=CinematicEffects(vignette=True, film_grain=False, audio_ducking=False, loudness_normalize=True),
                video_clips=clips_v1,
                audio_tracks=[
                    AudioTrackCue(
                        id="bench_audio_1",
                        name="Festival 120 BPM Bed",
                        source_id=audio_asset.id,
                        source_url=audio_asset.source_url,
                        volume=0.8,
                        start_time_seconds=0.0,
                        timeline_start_seconds=0.0,
                        duration_seconds=9.5,
                        ducking_enabled=False,
                    )
                ],
                subtitles=[
                    SubtitleCue(
                        id="bench_sub_1",
                        start_seconds=0.6,
                        end_seconds=3.8,
                        text="CINEFLOW AI // 1080P BENCHMARK",
                        style="cinematic_gold_bottom",
                    )
                ],
            )

            # Stage 4: Cold 16:9 1080p FFmpeg Render
            cold_stats: dict[str, Any] = {}
            proc.cpu_percent(interval=None)
            t0 = time.perf_counter()
            cold_out_path, cold_size = await execute_render_job(
                job_id="bench_cold_1080p",
                request=RenderRequest(timeline=cold_timeline, resolution="1080p", partial_cache=True),
                on_progress=lambda _pct, _msg: None,
                stats_holder=cold_stats,
            )
            dt_cold = max(time.perf_counter() - t0, 0.001)
            cpu_cold, rss_cold = _measure_process_snapshot(proc)
            cold_probe = probe_media_file(cold_out_path)
            out_duration = max(float(cold_probe.duration_seconds), 0.1)
            realtime_x = round(out_duration / dt_cold, 2)
            stages.append(
                BenchmarkStageResult(
                    stage_id="render_1080p_cold",
                    stage_name="Cold 1080p Multi-Clip MP4 Render",
                    duration_seconds=round(dt_cold, 3),
                    throughput_label=f"{realtime_x:.2f}x realtime ({out_duration:.1f}s @ 1920x1080)",
                    cpu_percent_avg=cpu_cold,
                    memory_rss_mb=rss_cold,
                    notes=f"Encoder: {hw.video_encoder}; LUT + ASS captions + xfade + loudnorm",
                )
            )

            # Stage 5: Warm Partial-Segment Re-Render (modify only clip 2 trim by 0.4s)
            warm_clips = [c.model_copy(deep=True) for c in clips_v1]
            warm_clips[1] = warm_clips[1].model_copy(update={"end_time_seconds": 3.1, "duration_seconds": 3.1})
            warm_timeline = cold_timeline.model_copy(update={"video_clips": warm_clips})
            warm_stats: dict[str, Any] = {}
            proc.cpu_percent(interval=None)
            t0 = time.perf_counter()
            await execute_render_job(
                job_id="bench_warm_1080p",
                request=RenderRequest(timeline=warm_timeline, resolution="1080p", partial_cache=True),
                on_progress=lambda _pct, _msg: None,
                stats_holder=warm_stats,
            )
            dt_warm = max(time.perf_counter() - t0, 0.001)
            cpu_warm, rss_warm = _measure_process_snapshot(proc)
            cache_hits = int(warm_stats.get("segment_cache_hits", 0))
            cache_misses = int(warm_stats.get("segment_cache_misses", 0))
            speedup_pct = round(max(0.0, ((dt_cold - dt_warm) / dt_cold) * 100.0), 1)
            stages.append(
                BenchmarkStageResult(
                    stage_id="render_1080p_warm_partial",
                    stage_name="Warm Partial-Cache Re-Render",
                    duration_seconds=round(dt_warm, 3),
                    throughput_label=f"{speedup_pct:.1f}% faster ({cache_hits}/{cache_hits + cache_misses} cached)",
                    cpu_percent_avg=cpu_warm,
                    memory_rss_mb=rss_warm,
                    notes="SHA-256 segment cache reuses untouched 1080p clips",
                )
            )

            # Stage 6: 9:16 Vertical Portrait Reel (1080x1920) Render
            portrait_asset = analyzed_videos[3]
            portrait_timeline = TimelinePlan(
                project_id="proj_bench_9_16",
                title="Benchmark 9:16 Vertical Reel",
                aspect_ratio="9:16",
                target_duration_seconds=3.5,
                fps=30,
                color_grade="cinematic_teal_orange",
                cinematic_effects=CinematicEffects(audio_ducking=False, loudness_normalize=True),
                video_clips=[
                    MediaClip(
                        clip_id="bench_portrait_1",
                        source_id=portrait_asset.id,
                        source_filename=portrait_asset.original_filename,
                        source_url=portrait_asset.source_url,
                        start_time_seconds=0.0,
                        end_time_seconds=3.5,
                        timeline_start_seconds=0.0,
                        duration_seconds=3.5,
                        color_grade="cinematic_teal_orange",
                    )
                ],
                audio_tracks=[
                    AudioTrackCue(
                        id="bench_portrait_audio",
                        name="Festival 120 BPM Bed",
                        source_id=audio_asset.id,
                        source_url=audio_asset.source_url,
                        volume=0.8,
                        start_time_seconds=0.0,
                        timeline_start_seconds=0.0,
                        duration_seconds=3.5,
                        ducking_enabled=False,
                    )
                ],
                subtitles=[],
            )
            proc.cpu_percent(interval=None)
            t0 = time.perf_counter()
            await execute_render_job(
                job_id="bench_portrait_9_16",
                request=RenderRequest(timeline=portrait_timeline, resolution="1080p", partial_cache=False),
                on_progress=lambda _pct, _msg: None,
            )
            dt_portrait = max(time.perf_counter() - t0, 0.001)
            cpu_port, rss_port = _measure_process_snapshot(proc)
            stages.append(
                BenchmarkStageResult(
                    stage_id="render_vertical_9_16",
                    stage_name="Vertical 9:16 (1080x1920) Reel Export",
                    duration_seconds=round(dt_portrait, 3),
                    throughput_label=f"{3.5 / dt_portrait:.2f}x realtime (1080x1920)",
                    cpu_percent_avg=cpu_port,
                    memory_rss_mb=rss_port,
                    notes="Teal & Orange grade + portrait crop/scale",
                )
            )

            vmem = psutil.virtual_memory()
            return ShowcaseBenchmarkReport(
                host_os=f"{platform.system()} {platform.release()} ({platform.machine()})",
                python_version=platform.python_version(),
                cpu_cores=hw.cpu_cores,
                ram_total_gb=round(vmem.total / (1024**3), 2),
                ffmpeg_version=bins.get("ffmpeg_version") or "ffmpeg",
                hardware_profile=hw_info,
                stages=stages,
                cold_render_seconds=round(dt_cold, 3),
                warm_cached_render_seconds=round(dt_warm, 3),
                cache_speedup_percent=speedup_pct,
                segment_cache_hits=cache_hits,
                segment_cache_misses=cache_misses,
                output_duration_seconds=round(out_duration, 2),
                realtime_speedup_x=realtime_x,
                portrait_render_seconds=round(dt_portrait, 3),
                output_file_bytes=int(cold_size),
            )
        finally:
            for key, old_val in orig_env.items():
                if old_val is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = old_val
            db_mod._db_instance = None
            config_mod.get_settings.cache_clear()
            detect_hardware_profile.cache_clear()
            clear_binary_cache()


def run_benchmark_suite(*, save_reports: bool = True) -> ShowcaseBenchmarkReport:
    """Execute the complete pipeline benchmark suite synchronously and optionally save reports."""
    report = asyncio.run(_run_isolated_benchmarks_async())
    if save_reports:
        json_path, md_path = benchmark_report_paths()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        md_path.write_text(_format_markdown_report(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run_benchmark_suite(save_reports=True)
    json_out, md_out = benchmark_report_paths()
    print(f"Benchmark completed: Cold 1080p render={result.cold_render_seconds}s, Warm cached={result.warm_cached_render_seconds}s ({result.cache_speedup_percent}% faster)")
    print(f"Saved: {json_out} and {md_out}")

