# PHASE 2 PLAN: Real Video Processing & Rendering Engine

> **Phase:** 02 — Real Video Processing  
> **Status:** READY FOR EXECUTION  
> **Goal:** Install/verify FFmpeg & FastAPI backend dependencies, implement secure batch media upload with FFprobe inspection & 720p proxy generation, build an FFmpeg complex-filtergraph rendering engine (trimming, aspect conforming, transitions, color grading, audio mixing), and connect real MP4 export end-to-end with automated tests.

---

## 🎯 Phase Objectives

1. **FFmpeg & Python Runtime Readiness:** Verify/install `ffmpeg` + `ffprobe` binaries and Python FastAPI dependencies; auto-detect CPU/GPU encoders (`h264_nvenc`, `h264_qsv`, `h264_amf`, fallback `libx264`).
2. **Secure Media Ingestion & Probing:** Batch upload endpoint accepting videos, photos, and audio tracks; strict extension & magic-byte validation; FFprobe metadata extraction; thumbnail + 720p fast-start proxy generation.
3. **Database & Project Persistence:** Lightweight SQLite persistence (`data/cineflow.db`) tracking media assets, projects, timelines, and render job states.
4. **Native FFmpeg Filtergraph Rendering Pipeline:** Trimming, speed scaling, heterogeneous aspect-ratio conforming (`16:9`, `9:16`, `1:1`, `4:5`, `21:9`), `xfade` transitions, color grading filters, missing-audio fallback (`anullsrc`), and multi-track music mixing with volume ducking.
5. **Async Job Runner & Real MP4 Export:** Background render execution with live FFmpeg `-progress` percentage tracking, cancellation support, and playable `.mp4` streaming download.
6. **Frontend-Backend Integration & Automated Test Suite:** Wire Next.js Upload & Editor Export workflows to FastAPI (with explicit offline demo fallback) and validate end-to-end with unit, security, and real FFmpeg rendering tests.

---

## 🌊 Wave-Based Task Breakdown

### Wave 1 — Foundation, Binary Discovery, Config & Persistence
- **Task 2.1: Backend Environment & FFmpeg Verification**
  - Verify/install `ffmpeg` and `ffprobe` on Windows 11 (`winget install Gyan.FFmpeg` or portable binary check) and install core FastAPI dependencies (`fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `python-multipart`, `aiofiles`, `httpx`, `python-dotenv`, `pytest`).
  - **Target Files:**
    - `backend/api/config.py` (Settings loaded from `.env` + path initialization for `data/uploads`, `data/proxies`, `data/renders`, `data/cache`)
    - `backend/video_engine/ffmpeg_runner.py` (Safe `shell=False` FFmpeg/FFprobe binary locator and subprocess wrapper)
    - `backend/video_engine/hardware.py` (CPU core count, GPU encoder detection, `low`/`medium`/`high` hardware profile resolver)
- **Task 2.2: SQLite Storage & Pydantic v2 Contracts**
  - Mirror `packages/shared_types/timeline.ts` into validated Pydantic v2 schemas and create SQLite schema/repository layer.
  - **Target Files:**
    - `backend/api/schemas.py` (`MediaAsset`, `ProjectCreate`, `ProjectResponse`, `TimelinePlan`, `MediaClip`, `AudioTrackCue`, `RenderJobStatus`, `HardwareProfileInfo`)
    - `backend/api/database.py` (Thread-safe SQLite repository for `projects`, `media_assets`, and `render_jobs`)

### Wave 2 — Media Ingestion, FFprobe & Proxy Generation
- **Task 2.3: FFprobe Metadata Extractor & Proxy Pipeline**
  - Extract streams, codecs, resolution, FPS, rotation, duration, audio channels, and bitrate via `ffprobe -of json`.
  - Generate crisp preview thumbnails (`_thumb.jpg`) and lightweight `720p` H.264 `+faststart` scrubbing proxies (`_proxy.mp4`).
  - **Target Files:**
    - `backend/media_analysis/probe.py`
    - `backend/media_analysis/proxy.py`
    - `backend/media_analysis/validator.py` (Extension whitelist, magic-byte check, path traversal defense, size quota check)
- **Task 2.4: FastAPI Gateway & Media/Project Endpoints**
  - Assemble the FastAPI app with CORS, exception handlers, static media routes, health endpoint, batch upload endpoint (`POST /api/v1/media/upload`), media CRUD, and project CRUD.
  - **Target Files:**
    - `backend/api/main.py`
    - `backend/api/routes_media.py`
    - `backend/api/routes_projects.py`

### Wave 3 — Filtergraph Assembly, Audio Mixing & Async Rendering
- **Task 2.5: Video Filtergraph Builder & Audio Mixer**
  - Build composable, deterministic FFmpeg filtergraph generator supporting videos + still images, aspect ratio conforming, speed ramps (`setpts`, `atempo`), `xfade` transitions, color grading LUT presets, and multi-track audio mixing (`amix`, ducking, `loudnorm`).
  - **Target Files:**
    - `backend/video_engine/filtergraph.py`
    - `backend/audio_engine/mixer.py`
- **Task 2.6: Async Render Job Queue & Download Streaming**
  - Implement async job runner parsing FFmpeg `-progress pipe:1` `out_time_us`, supporting cancellation, recovery on restart, and `FileResponse` MP4 download.
  - **Target Files:**
    - `backend/job_manager/queue.py`
    - `backend/rendering/renderer.py`
    - `backend/api/routes_render.py`

### Wave 4 — Frontend Integration & Comprehensive Test Suite
- **Task 2.7: Connect Frontend (`apps/web`) to Live FastAPI Backend**
  - Add typed API client (`apps/web/src/lib/api.ts`) and wire `/upload`, `/dashboard`, and `/editor` (`ExportModal`, `MediaLibraryDrawer`, `VideoPreviewCanvas`) to real backend endpoints with clear fallback notice when backend server is offline.
  - **Target Files:**
    - `apps/web/src/lib/api.ts`
    - `apps/web/src/app/upload/page.tsx`
    - `apps/web/src/components/editor/ExportModal.tsx`
    - `apps/web/src/app/editor/page.tsx`
- **Task 2.8: Automated Unit, Security & Real Rendering Tests**
  - Write and execute pytest suite using synthetic FFmpeg `lavfi` test videos, images, and sine audio to prove real end-to-end MP4 rendering across landscape (`16:9`) and portrait (`9:16`) targets.
  - **Target Files:**
    - `tests/unit/test_schemas_and_filtergraph.py`
    - `tests/security/test_upload_security.py`
    - `tests/rendering/test_real_render_pipeline.py`

---

## 🔍 Verification & Acceptance Gates

1. **Binary & Health Check:** `GET /api/v1/health` returns `200 OK` with verified `ffmpeg` and `ffprobe` versions and detected encoder profile.
2. **Batch Upload & Probe:** Uploading multiple mixed `.mp4` and `.jpg` files via `POST /api/v1/media/upload` extracts exact resolution/duration/fps and persists thumbnails + proxies.
3. **Security Gate:** Spoofed extensions, path-traversal filenames (`../../evil.mp4`), and empty/corrupt payloads return `400`/`415` without writing outside `data/uploads`.
4. **Real MP4 Render Gate:** Submitting a multi-clip `TimelinePlan` (video + image + crossfade + `golden_hour` color grade + background music) to `POST /api/v1/render` produces a real `.mp4` verified by `ffprobe` (`codec_name=h264`, `aac` audio, exact target resolution `1920x1080` or `1080x1920`, non-zero duration matching timeline).
5. **Test Suite Pass:** `pytest` passes 100% of unit, security, and rendering tests, and `apps/web` compiles cleanly (`npm run build`).

---

## 🚀 Execution Command

To execute this plan end-to-end, run:
```bash
/gsd-execute-phase 2
```

