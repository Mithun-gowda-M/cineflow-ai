# PHASE 9 RESEARCH: Hackathon Presentation & Demonstration Package

> **Phase:** 09 — Hackathon Presentation & Demonstration Package  
> **Target:** Real Hardware & Pipeline Benchmark Suite, Interactive HD Demo Showcase Project, System Architecture Diagrams, \$0 vs Cloud API Cost Analysis, Pitch Deck Assets, and Live Jury Showcase Route (`/showcase`)  
> **Status:** Research Complete

---

## 1. Benchmark Evaluation Strategy (Zero-Fake Policy)

A central rule of **CINEFLOW AI** (`PROJECT.md` Core Tenet #3) is zero synthetic metrics or mocked performance telemetry. All numbers presented to hackathon judges must come from reproducible code running on the host machine:

- **Execution Harness (`backend/benchmarking/runner.py`):** Runs end-to-end timed stages inside an isolated workspace using synthetic Full HD (1920×1080) & Portrait HD (1080×1920) FFmpeg test footage and an audio track:
  1. **Ingestion & 720p Proxy Transcode:** `ffprobe` metadata extraction + `ffmpeg` 720p lightweight scrub proxy generation.
  2. **CV Media Intelligence:** `PySceneDetect` cut detection + `OpenCV` Laplacian blur variance, exposure, histogram, and perceptual dHash extraction.
  3. **Librosa Audio Intelligence:** 22.05 kHz mono decoding, BPM estimation, onset envelope, and beat-grid synchronization.
  4. **FFmpeg Cold Render (1080p 16:9):** Multi-clip `xfade` transition graph, LUT color grade, burnt-in `.ass` animated typography, and `amix`/`loudnorm` audio mixing.
  5. **Partial Segment Cache Warm Re-render:** Tweaking one downstream parameter/clip and measuring exact SHA-256 `SegmentCache` hits/misses and wall-clock speedup versus the cold pass.
  6. **Vertical 9:16 1080×1920 Export:** Reel aspect-ratio scaling/cropping export speed.
- **System Resource Telemetry (`psutil` + `detect_hardware_profile`):** Captures CPU logical core count, process CPU utilization, RSS memory delta (MB), disk space, OS platform, FFmpeg binary version, and verified working encoders (`h264_qsv` / `h264_nvenc` / `h264_amf` / `libx264`).
- **Artifacts Generated:** `docs/benchmarks/BENCHMARK_REPORT.json` (machine-readable) + `docs/benchmarks/BENCHMARK_REPORT.md` (human-readable tables cleanly timestamped with host specs).

---

## 2. Interactive HD Demo Showcase Project (`assets/sample_media/` + `/showcase`)

- **Git Tracking Policy:** `.gitignore` line 45 explicitly includes `!assets/sample_media/**`, allowing curated HD sample assets to be versioned in Git cleanly while keeping `data/` ignored.
- **Self-Contained Royalty-Free 1080p HD Pack (`backend/showcase/sample_generator.py` -> `assets/sample_media/`):**
  - Procedurally synthesized using native FFmpeg (`libx264` CRF 23–26 + clean visual test/cinematic motion shaders) and NumPy/Soundfile (crisp 120 BPM harmonic festival synth beat):
    - `01_diya_golden_intro_1080p.mp4` (1920×1080, 4.0s, warm amber glow + subtle motion)
    - `02_auditorium_stage_pulse_1080p.mp4` (1920×1080, 4.5s, cyan/indigo laser sweep)
    - `03_fireworks_climax_burst_1080p.mp4` (1920×1080, 4.5s, high-contrast bright bursts)
    - `04_campus_aerial_portrait_1080p.mp4` (1080×1920 vertical B-roll gradient motion, 4.0s)
    - `05_festival_beat_120bpm.wav` (16.0s crisp 120 BPM drum + chord progression WAV)
  - Keeping bitrates clean keeps the entire HD pack compact (~2–5 MB total) so cloning and loading takes seconds.
- **Showcase API & Studio Deep-Linking (`backend/api/routes_showcase.py` + `editor/page.tsx`):**
  - `POST /api/v1/showcase/load` copies `assets/sample_media/*` into the active `UPLOAD_DIR`, runs the real ingestion pipeline (proxies, thumbnails, scenes, CV scores), analyzes `05_festival_beat_120bpm.wav` with Librosa, and persists project `proj_bmsit_showcase_2026` with a populated 4-act multi-track `TimelinePlan` (V1, V2 B-roll, Audio A1, ASS Subtitle cues).
  - **Next.js 15 App Router `<Suspense>` Requirement:** Adding `?projectId=` loading in `apps/web/src/app/editor/page.tsx` via `useSearchParams()` must wrap the client consumer inside `<Suspense>` so static prerendering during `next build` passes with exit code `0`.

---

## 3. Architecture, Cost Analysis & Pitch Collateral

- **Unpopulated `docs/` Folders from Phase 0:** Inspections show `docs/architecture/`, `docs/api/`, `docs/installation/`, and `docs/maintenance/` currently hold no markdown files, while `docs/deployment/`, `docs/handover/`, and `docs/third_party_licenses/` are populated. Phase 9 completes the entire documentation suite cleanly.
- **Cost Analysis Integrity:** `docs/pitch/COST_COMPARISON_ANALYSIS.md` contrasts published/illustrative cloud subscription stacks (AI generation, cloud transcription, managed transcoding, cloud editing SaaS) against **CINEFLOW AI's verified \$0 recurring API expenditure** across single-student creators and a 50-student BMSIT Media Club deployment.
- **Interactive Jury Hub (`apps/web/src/app/showcase/page.tsx`):** Unifies the live benchmark report viewer, 1-click HD showcase project launcher, interactive TCO calculator sliders, architecture blueprint, and 10-slide navigable jury pitch deck inside CINEFLOW AI's dark obsidian & champagne-gold UI.

