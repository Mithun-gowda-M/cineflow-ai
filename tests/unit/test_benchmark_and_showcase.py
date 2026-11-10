"""Unit checks for committed Full-HD sample media pack and verified benchmark reports."""

from __future__ import annotations

from pathlib import Path

from backend.api.schemas import ShowcaseBenchmarkReport
from backend.benchmarking.runner import benchmark_report_paths, load_saved_benchmark_report
from backend.media_analysis.probe import probe_media_file
from backend.showcase.sample_generator import SAMPLE_PACK_SPECS, ensure_sample_media_pack, sample_media_dir


def test_committed_sample_media_pack_is_full_hd_and_compact() -> None:
    paths = ensure_sample_media_pack(force=False)
    assert len(paths) == len(SAMPLE_PACK_SPECS)

    total_bytes = sum(p.stat().st_size for p in paths)
    assert total_bytes < 10 * 1024 * 1024  # Lightweight enough for clean Git distribution

    sdir = sample_media_dir()
    for spec in SAMPLE_PACK_SPECS:
        fp = sdir / spec.filename
        assert fp.is_file(), f"Missing committed sample file: {fp}"
        meta = probe_media_file(fp)
        if spec.media_kind == "video":
            assert meta.width == spec.width
            assert meta.height == spec.height
            assert meta.duration_seconds >= 3.5
            assert meta.codec.lower().startswith("h264")
        else:
            assert meta.duration_seconds >= 15.0
            assert meta.sample_rate == spec.fps


def test_saved_benchmark_report_schema_and_real_metrics() -> None:
    json_path, md_path = benchmark_report_paths()
    assert json_path.is_file(), "BENCHMARK_REPORT.json must be generated"
    assert md_path.is_file(), "BENCHMARK_REPORT.md must be generated"

    report = load_saved_benchmark_report()
    assert isinstance(report, ShowcaseBenchmarkReport)
    assert report.cpu_cores >= 1
    assert report.cold_render_seconds > 0
    assert report.warm_cached_render_seconds > 0
    assert report.warm_cached_render_seconds < report.cold_render_seconds
    assert report.cache_speedup_percent > 0
    assert report.segment_cache_hits >= 1
    assert report.output_file_bytes > 50_000
    assert len(report.stages) == 6
    assert "Cold 1080p Render" in md_path.read_text(encoding="utf-8")

