# CINEFLOW AI — Verified Pipeline & Hardware Benchmark Report

> **Generated At:** `2026-11-10T15:41:22Z`  
> **Host Environment:** `Windows 11 (AMD64)` | Python `3.12.10` | 16 Logical Cores | 15.7 GB RAM  
> **FFmpeg Binary:** `ffmpeg version 9.0.2-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers`  
> **Hardware Profile:** `high` (`h264_qsv`, working encoders: `h264_qsv, libx264`)

Every metric below was recorded directly on this machine using real 1920x1080 Full-HD showcase clips and 120 BPM audio — zero mocked timings.

## 1. Stage-by-Stage Throughput Summary

| Stage | Wall Time (s) | Throughput | Process CPU (%) | Process RSS (MB) | Notes |
| :--- | ---: | :--- | ---: | ---: | :--- |
| FFprobe & 720p Proxy Generation | 4.315 | 4 HD clips in 4.32s (0.93 clips/s) | 2.5% | 67.4 | 3x 1920x1080 + 1x 1080x1920 -> 720p proxies (h264_qsv) |
| OpenCV CV Scoring & PySceneDetect | 84.654 | 0.05 clips/s (5 scenes) | 131.8% | 143.4 | Mean quality score 79.9/100 across 1080p footage |
| Librosa Tempo & Beat Tracking | 3.776 | 4.24x realtime (60.1 BPM) | 75.2% | 296.0 | 15 beats detected on 16.0s track |
| Cold 1080p Multi-Clip MP4 Render | 19.401 | 0.49x realtime (9.6s @ 1920x1080) | 0.9% | 296.2 | Encoder: h264_qsv; LUT + ASS captions + xfade + loudnorm |
| Warm Partial-Cache Re-Render | 7.633 | 60.7% faster (2/3 cached) | 0.8% | 296.5 | SHA-256 segment cache reuses untouched 1080p clips |
| Vertical 9:16 (1080x1920) Reel Export | 2.311 | 1.51x realtime (1080x1920) | 0.0% | 296.6 | Teal & Orange grade + portrait crop/scale |

## 2. Cold 1080p Render vs. SHA-256 Partial Segment Cache

| Metric | Measured Value |
| :--- | :--- |
| **16:9 1080p Multi-Clip Cold Render** | **19.401 s** |
| **16:9 1080p Warm Partial Re-render** | **7.633 s** (2 cache hits / 1 rebuild) |
| **Partial Cache Speedup** | **60.7% faster** vs. cold build |
| **Output Duration & Speed Ratio** | 9.60 s final MP4 (**0.49x realtime**) |
| **Portrait 9:16 (1080x1920) Render** | **2.311 s** |
| **Final H.264/AAC MP4 Size** | 3.64 MB |

## 3. Reproducing These Benchmarks

```powershell
backend\.venv\Scripts\python.exe -m backend.benchmarking.runner
```
