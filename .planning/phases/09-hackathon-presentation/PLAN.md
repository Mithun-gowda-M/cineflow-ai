# PHASE 9 PLAN: Hackathon Presentation & Demonstration Package

> **Phase:** 09 — Hackathon Presentation & Demonstration Package  
> **Status:** READY FOR EXECUTION  
> **Goal:** Build and execute a reproducible hardware/pipeline benchmark suite producing verified speed/CPU/quality reports (`docs/benchmarks/`), generate and commit a compact Full-HD sample media pack (`assets/sample_media/`) wired to a 1-click live showcase seeder (`routes_showcase.py`) and `?projectId=` hydration in `/editor`, complete system architecture/API/quickstart docs (`docs/`), build the interactive `/showcase` Hackathon Presentation & Cost Calculator UI, and pass 100% backend + Next.js verification gates.

---

## 🎯 Phase Objectives

1. **Real Hardware & Pipeline Benchmark Suite (`backend/benchmarking/runner.py` + `docs/benchmarks/`):**
   - Measure real host execution latency, speed vs. realtime ratio, `psutil` CPU/RAM footprint, and cold vs. warm SHA-256 `SegmentCache` speedup across FFprobe, 720p proxy transcoding, PySceneDetect + OpenCV CV scoring, Librosa BPM tracking, and 1080p 16:9 + 9:16 FFmpeg MP4 renders.
   - Output verified machine-readable `docs/benchmarks/BENCHMARK_REPORT.json` and formatted `docs/benchmarks/BENCHMARK_REPORT.md` generated directly from the live host run.
2. **High-Definition Sample Media Pack & Interactive Demo Showcase (`assets/sample_media/` + `backend/showcase/` + `routes_showcase.py`):**
   - Generate crisp, lightweight, 100% copyright-free Full-HD (1920×1080 & 1080×1920) sample clips and a 120 BPM festive WAV track in `assets/sample_media/` via [`sample_generator.py`](file:///c:/Users/mithu/ai%20video%20editing/backend/showcase/sample_generator.py).
   - Provide `POST /api/v1/showcase/load`, `GET /api/v1/showcase/status`, `GET /api/v1/showcase/benchmarks`, and `POST /api/v1/showcase/benchmarks/run` so judges can hydrate `proj_bmsit_showcase_2026` through the real ingestion, CV, audio, and director pipelines with one click.
3. **Deep Studio Project Hydration & Jury Showcase Hub (`apps/web`):**
   - Upgrade [`editor/page.tsx`](file:///c:/Users/mithu/ai%20video%20editing/apps/web/src/app/editor/page.tsx) to read `?projectId=` inside a Next.js 15 `<Suspense>` boundary, loading persisted backend timelines and real local static proxy streams.
   - Upgrade [`dashboard/page.tsx`](file:///c:/Users/mithu/ai%20video%20editing/apps/web/src/app/dashboard/page.tsx) with 1-click **Load Live HD Showcase Project** and direct project-specific studio launch links (`/editor?projectId=...`).
   - Create [`showcase/page.tsx`](file:///c:/Users/mithu/ai%20video%20editing/apps/web/src/app/showcase/page.tsx) (linked in [`Navbar.tsx`](file:///c:/Users/mithu/ai%20video%20editing/apps/web/src/components/Navbar.tsx)) featuring live measured benchmark charts, interactive \$0 vs Cloud SaaS TCO calculator, visual pipeline architecture blueprint, and a 10-slide interactive pitch deck viewer.
4. **Architecture, API, Cost & Pitch Documentation (`docs/`):**
   - Author [`docs/architecture/SYSTEM_ARCHITECTURE.md`](file:///c:/Users/mithu/ai%20video%20editing/docs/architecture/SYSTEM_ARCHITECTURE.md), [`docs/api/API_REFERENCE.md`](file:///c:/Users/mithu/ai%20video%20editing/docs/api/API_REFERENCE.md), [`docs/installation/QUICKSTART.md`](file:///c:/Users/mithu/ai%20video%20editing/docs/installation/QUICKSTART.md), [`docs/maintenance/MAINTENANCE_AND_TESTING.md`](file:///c:/Users/mithu/ai%20video%20editing/docs/maintenance/MAINTENANCE_AND_TESTING.md), [`docs/pitch/COST_COMPARISON_ANALYSIS.md`](file:///c:/Users/mithu/ai%20video%20editing/docs/pitch/COST_COMPARISON_ANALYSIS.md), and [`docs/pitch/HACKATHON_PITCH_DECK.md`](file:///c:/Users/mithu/ai%20video%20editing/docs/pitch/HACKATHON_PITCH_DECK.md).

---

## 🌊 Wave-Based Task Breakdown

### Wave 1 — Schemas, HD Sample Media Generator, Benchmark Engine & Showcase Seeder
- **Task 9.1: Showcase & Benchmark Pydantic Schemas**
  - Extend `backend/api/schemas.py` with `BenchmarkStageResult`, `ShowcaseBenchmarkReport`, `ShowcaseStatusResponse`, and `ShowcaseLoadResponse`.
- **Task 9.2: High-Definition Sample Footage Generator & Committed Pack**
  - Create `backend/showcase/__init__.py` and `backend/showcase/sample_generator.py` to procedurally generate copyright-free 1080p MP4 clips (`01_diya_golden_intro_1080p.mp4`, `02_auditorium_stage_pulse_1080p.mp4`, `03_fireworks_climax_burst_1080p.mp4`, `04_campus_aerial_portrait_1080p.mp4`) and `05_festival_beat_120bpm.wav` in `assets/sample_media/`.
  - Execute the generator to populate `assets/sample_media/` and verify every clip with `ffprobe` (confirming real HD frames, codecs, audio channels, and compact total footprint < 6 MB).
- **Task 9.3: Real Hardware & Pipeline Benchmark Runner**
  - Create `backend/benchmarking/__init__.py` and `backend/benchmarking/runner.py` to benchmark ingestion/proxy, PySceneDetect + OpenCV CV analysis, Librosa BPM/beat detection, 1080p cold render, warm partial segment cache render, and 9:16 portrait render using real media & `psutil`.
  - Execute `backend\.venv\Scripts\python.exe -m backend.benchmarking.runner` to generate verified `docs/benchmarks/BENCHMARK_REPORT.json` and `docs/benchmarks/BENCHMARK_REPORT.md` from actual local measurements.

### Wave 2 — Backend Showcase API & Full Architecture/Cost/Pitch Docs
- **Task 9.4: Showcase Seeder & FastAPI Showcase Router**
  - Create `backend/showcase/seeder.py` to ingest `assets/sample_media/*` into SQLite/storage via `ingest_media_file` + `analyze_audio_file` and persist `proj_bmsit_showcase_2026` with a multi-track 4-act `TimelinePlan`.
  - Create `backend/api/routes_showcase.py` (`/showcase/status`, `/showcase/load`, `/showcase/benchmarks`, `/showcase/benchmarks/run`) and register `showcase_router` in `backend/api/main.py`.
- **Task 9.5: Architecture, API, Quickstart, Cost Analysis & Pitch Deck Collateral**
  - Author Mermaid diagrams & architecture blueprint in `docs/architecture/SYSTEM_ARCHITECTURE.md`.
  - Author `docs/api/API_REFERENCE.md`, `docs/installation/QUICKSTART.md`, `docs/maintenance/MAINTENANCE_AND_TESTING.md`.
  - Author transparent \$0 vs Cloud SaaS TCO breakdown in `docs/pitch/COST_COMPARISON_ANALYSIS.md` and full 10-slide script + 3-minute live demo cues in `docs/pitch/HACKATHON_PITCH_DECK.md`.

### Wave 3 — Frontend Showcase Hub, Project Deep-Linking & Verification Suite
- **Task 9.6: Frontend API Client, Editor `?projectId=` Hydration & Dashboard Showcase CTA**
  - Add Showcase, Benchmark, and `fetchBackendProject` helpers in `apps/web/src/lib/api.ts`.
  - Update `apps/web/src/app/editor/page.tsx` with `<Suspense>` + `?projectId=` hydration (loading project timeline, audio waveform/BPM data, and local backend media streams) cleanly while preserving fallback showcase behavior.
  - Update `apps/web/src/app/dashboard/page.tsx` with 1-click **Load Live HD Showcase Project** and direct project studio launch links (`/editor?projectId=...`).
- **Task 9.7: Interactive Hackathon Presentation Hub (`/showcase`) & Navigation**
  - Build `apps/web/src/app/showcase/page.tsx` (and embed verified benchmark JSON snapshot cleanly alongside live `/api/v1/showcase/benchmarks` refresh) featuring live benchmark telemetry, interactive \$0 vs Cloud SaaS calculator, pipeline blueprint, and 10-slide interactive pitch viewer.
  - Add `/showcase` link in `apps/web/src/components/Navbar.tsx` and Landing CTA in `apps/web/src/components/landing/HeroSection.tsx` / `OpenSourceShowcase.tsx` (optional polish if non-intrusive).
- **Task 9.8: Automated Unit & Integration Tests + Full Gate Verification**
  - Create `tests/unit/test_benchmark_and_showcase.py` (verify `assets/sample_media/` HD integrity via `ffprobe`, sample generator idempotency, benchmark report serialization/sanity).
  - Create `tests/integration/test_showcase_and_benchmark_api.py` (verify `GET /api/v1/showcase/status`, `POST /api/v1/showcase/load` real ingestion + project persistence + render readiness, and `GET /api/v1/showcase/benchmarks`).
  - Verify `pytest tests -v` (`100%` pass) and `npm --prefix apps/web run build` (`exit 0`).

---

## 🔍 Verification & Acceptance Gates

1. **Sample HD Pack Gate:** `assets/sample_media/` contains verified Full-HD (`1920x1080` / `1080x1920`) MP4 clips + 120 BPM WAV audio tracked cleanly under `.gitignore` rule `!assets/sample_media/**`.
2. **Real Benchmark Gate:** `docs/benchmarks/BENCHMARK_REPORT.json` & `.md` are produced by actual timed pipeline runs on the host machine (including verified cold vs. warm partial segment cache speedup) with zero hardcoded/fake numbers.
3. **Interactive Showcase Hydration Gate:** `POST /api/v1/showcase/load` ingests real assets/scenes/BPM and opens cleanly in `/editor?projectId=proj_bmsit_showcase_2026` ready for live MP4 rendering.
4. **Full Regression & Build Gate:** All `pytest tests -v` tests pass (`100%`) and `npm --prefix apps/web run build` exits `0` cleanly (including static prerender of `/showcase` and `<Suspense>`-wrapped `/editor`).

---

## 🚀 Execution Command

Run:
```bash
/gsd-execute-phase 9
```
