# PHASE 3 PLAN: AI Media Intelligence & Scene Detection

> **Phase:** 03 — AI Media Intelligence  
> **Status:** READY FOR EXECUTION  
> **Goal:** Install OpenCV (`opencv-python-headless`) and PySceneDetect (`scenedetect`), implement automated scene splitting, transparent multi-factor frame quality scoring, perceptual duplicate detection, semantic auto-tagging, searchable clip ranking APIs, and live UI inspection inside `apps/web`.

---

## 🎯 Phase Objectives

1. **CV Runtime Setup:** Install and verify `opencv-python-headless`, `scenedetect[opencv]`, and `numpy` inside `backend/.venv`.
2. **PySceneDetect Scene Splitting:** Automatically detect natural cut/transition boundaries in uploaded videos and extract per-scene keyframe thumbnails and metrics.
3. **OpenCV Visual & Quality Analyzer:** Compute Laplacian blur/sharpness, exposure & lighting balance, motion stability, built-in Haar face presence & composition, and top-3 dominant hex color swatches.
4. **Transparent Scoring, Semantic Tagging & Deduplication:** Produce `0–100` transparent quality breakdowns with plain-English explanations, deterministic semantic tags (`Fireworks`, `Diya`, `Sunset`, `Portrait`, `Group`, `Action`, `Landscape`, `Low-Light`), and 64-bit `dHash` duplicate shot flags.
5. **Media Intelligence & Search APIs:** Persist CV analysis and detected scenes in SQLite (`data/cineflow.db`), run analysis on upload / `/analyze`, and expose ranked search (`GET /api/v1/media/search`).
6. **Frontend Media Hub & Studio Integration:** Display real CV scores, color palettes, duplicate badges, scene sub-clips, and semantic search in `/upload` and `/editor`.

---

## 🌊 Wave-Based Task Breakdown

### Wave 1 — Dependencies, Schemas & Database Extensions
- **Task 3.1: Install CV Packages & Extend Contracts**
  - Install `opencv-python-headless`, `scenedetect[opencv]`, and compatible `numpy` in `backend/.venv`.
  - Extend `backend/api/schemas.py` with `QualityBreakdown`, `DetectedScene`, `MediaAnalysisResult`, and `MediaSearchResult`.
  - Extend `backend/api/database.py` (with safe schema migration for existing DBs) to store `analysis_json` on `media_assets` and a `detected_scenes` table.
  - **Target Files:**
    - `backend/requirements.txt`
    - `backend/api/schemas.py`
    - `backend/api/database.py`

### Wave 2 — Scene Detection & OpenCV Frame Intelligence
- **Task 3.2: PySceneDetect Integration**
  - Implement `detect_video_scenes(...)` using `scenedetect.open_video`, `SceneManager`, `ContentDetector` / `AdaptiveDetector` tuned by hardware profile (`low`/`medium`/`high`), generating per-scene midpoint thumbnails in `data/proxies/`.
  - **Target Files:**
    - `backend/media_analysis/scene_detector.py`
- **Task 3.3: OpenCV Quality, Color & Face Analyzer**
  - Implement sampled-frame video & image analyzer computing Laplacian variance, luminance/clipping, optical-flow/frame-diff motion stability, Haar cascade face detection, composition balance, and dominant hex swatches.
  - **Target Files:**
    - `backend/media_analysis/cv_analyzer.py`

### Wave 3 — Transparent Scoring, Semantic Tagger, Deduplicator & Pipeline
- **Task 3.4: Scoring Engine, Semantic Tagger & Perceptual Deduplicator**
  - Implement weighted scoring (`Sharpness`, `Exposure`, `Stability`, `Composition`) with plain-English explanation strings.
  - Implement rule-based semantic tagger (`Fireworks`, `Diya`, `Rangoli`, `Sunset`, `People`, `Portrait`, `Group`, `Action`, `Landscape`, `Celebration`, `Low-Light`).
  - Implement 64-bit `dHash` generator + Hamming-distance duplicate detector against existing library items.
  - **Target Files:**
    - `backend/media_analysis/scoring.py`
    - `backend/media_analysis/tagger.py`
    - `backend/media_analysis/deduplicator.py`
    - `backend/media_analysis/pipeline.py` (Unified `analyze_media_asset` orchestrator)

### Wave 4 — Search/Ranking APIs, Frontend Integration & Automated Tests
- **Task 3.5: Media Intelligence & Natural Search Endpoints**
  - Auto-run intelligence pipeline during `/api/v1/media/upload` (configurable via `?analyze=true` default).
  - Add `POST /api/v1/media/{media_id}/analyze`, `POST /api/v1/media/analyze-all`, `GET /api/v1/media/{media_id}/scenes`, and `GET /api/v1/media/search` with natural-language query ranking (`"best fireworks"`, `"brightest diya"`, `"sharpest sunset"`).
  - **Target Files:**
    - `backend/api/routes_media.py`
- **Task 3.6: Enrich Frontend Media Hub & Editor Library**
  - Update `apps/web/src/lib/api.ts`, `apps/web/src/types/index.ts`, `apps/web/src/app/upload/page.tsx`, and `apps/web/src/components/editor/MediaLibraryDrawer.tsx` to display real CV sub-scores, explanations, hex color palettes, duplicate warnings, detected scenes insertion, and ranked search.
  - **Target Files:**
    - `apps/web/src/lib/api.ts`
    - `apps/web/src/types/index.ts`
    - `apps/web/src/app/upload/page.tsx`
    - `apps/web/src/components/editor/MediaLibraryDrawer.tsx`
- **Task 3.7: Automated CV, Scene Detection & Search Test Suite**
  - Test sharp vs blurred synthetic videos (`GaussianBlur`), bright vs dark exposure scoring, multi-scene synthetic cut splitting (red -> blue -> bright gold scene transitions detected by PySceneDetect), exact/near-duplicate `dHash` flagging, semantic tagging, and ranked search APIs.
  - **Target Files:**
    - `tests/unit/test_cv_scoring_and_tagging.py`
    - `tests/integration/test_media_intelligence_api.py`

---

## 🔍 Verification & Acceptance Gates

1. **Scene Splitting Gate:** A multi-scene synthetic video with distinct visual transitions is split into `>= 2` `DetectedScene` intervals with valid `start_seconds < end_seconds` and JPEG thumbnails on disk.
2. **Quality Discrimination Gate:** A crisp, well-lit image/video scores significantly higher (`>= 20` points) than an artificially Gaussian-blurred or severely underexposed video, with transparent sub-metrics and accurate `quality_explanation`.
3. **Duplicate Flagging Gate:** Uploading two identical or nearly identical media files marks the second asset with `duplicate_of_id` and `similarity_percent >= 90%`.
4. **Search & Ranking Gate:** `GET /api/v1/media/search?q=best+sharp+sunset` returns matching assets ordered descending by quality/sharpness.
5. **Full Test & Build Gate:** All existing Phase 2 tests + new Phase 3 `pytest` tests pass, and `apps/web` `npm run build` exits cleanly with code `0`.

---

## 🚀 Execution Command

Run:
```bash
/gsd-execute-phase 3
```
