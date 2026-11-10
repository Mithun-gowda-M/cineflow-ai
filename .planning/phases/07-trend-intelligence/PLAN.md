# PHASE 7 PLAN: Trend Intelligence (Optional Style Recipes)

> **Phase:** 07 — Trend Intelligence (Optional Style Recipes)  
> **Status:** COMPLETED  
> **Goal:** Implement a strict copyright-safe Reference Video Style Analyzer (extracting cut frequency, motion velocity, and color mood via OpenCV & PySceneDetect), an Original Abstract Style Recipe Generator persisted in SQLite (`style_recipes`), AI Director & 1-click timeline style transfer integration, and Studio UI Style Recipe Extractor & Selector controls.

---

## 🎯 Phase Objectives

1. **Copyright Safety Validator (`backend/trend_intelligence/safety.py`):** Reject `file://`, SSRF loopback/private/link-local hosts, and unauthorized download attempts while auditing zero-copy / zero-scraping compliance on every recipe.
2. **Reference Video Analyzer (`backend/trend_intelligence/analyzer.py`):** Measure quantitative cut frequency (`cuts_per_minute`, `avg_shot_duration_seconds`), optical motion velocity (`motion_velocity_score`, `motion_profile`), and color mood (`color_mood`, dominant palette hex codes, recommended LUT & vignette/grain toggles) from user-authorized local videos without retaining frames or audio.
3. **Original Style Recipe Generator & Persistence (`backend/trend_intelligence/recipe_generator.py`, `database.py`):** Seed curated royalty-free style templates and persist custom extracted/pattern-based `StyleRecipe` records in SQLite (`style_recipes` table).
4. **FastAPI Trend Endpoints & AI Director Integration (`routes_trends.py`, `director.py`):**
   - Expose `GET /api/v1/trends/recipes`, `POST /api/v1/trends/analyze-media/{media_id}`, `POST /api/v1/trends/analyze-upload`, `POST /api/v1/trends/analyze-url`, `POST /api/v1/trends/recipes/{recipe_id}/apply`, and `DELETE /api/v1/trends/recipes/{recipe_id}`.
   - Allow `DirectorPlanRequest.style_recipe_id` to steer storyboarding pacing, color grade, aspect ratio, speed ramps, and cinematic effects.
5. **Frontend Style Recipe Modal & Copilot Selector (`apps/web`):** Add [`StyleRecipeModal`](file:///c:/Users/mithu/ai%20video%20editing/apps/web/src/components/editor/StyleRecipeModal.tsx), trend client helpers in `lib/api.ts`, and 1-click recipe application in `AiDirectorDrawer.tsx` & `editor/page.tsx` (with full Undo/Redo snapshot support).

---

## 🌊 Wave-Based Task Breakdown

### Wave 1 — Copyright Safety, Schemas, SQLite Storage & Reference Style Analyzer
- **Task 7.1: Schemas & SQLite `style_recipes` Table**
  - Add Pydantic contracts in `backend/api/schemas.py`: `StyleRecipeSourceType`, `MotionProfile`, `StyleRecipe`, `StyleAnalyzeUrlRequest`, `StyleApplyRequest`, `StyleApplyResponse`, `TrendSafetyAudit`, and add optional `style_recipe_id: Optional[str] = None` on `DirectorPlanRequest`.
  - Add `style_recipes` table + CRUD/seed methods (`seed_builtin_style_recipes`, `list_style_recipes`, `get_style_recipe`, `save_style_recipe`, `delete_style_recipe`) in `backend/api/database.py`.
- **Task 7.2: Copyright Safety Guard & OpenCV/PySceneDetect Style Analyzer**
  - Implement `validate_safe_reference_url(...)` in `backend/trend_intelligence/safety.py` enforcing HTTP/HTTPS scheme checks and SSRF/private-IP blocking (with zero network media download).
  - Implement `analyze_reference_video(...)` in `backend/trend_intelligence/analyzer.py` reusing `detect_video_scenes` & OpenCV frame metrics to extract `cuts_per_minute`, `avg_shot_duration_seconds`, `motion_velocity_score`, `motion_profile`, color mood, dominant hex palette, and recommended LUT/effects/speed-ramp parameters.

### Wave 2 — Recipe Generator, AI Director Integration & Trend API Routes
- **Task 7.3: Original Style Recipe Generator & Style Transfer Applier**
  - Implement `backend/trend_intelligence/recipe_generator.py`:
    - Built-in curated original recipes (*BMSIT Cultural Aftermovie*, *9:16 Rapid Hook Reel*, *Golden Sunset Travelogue*, *Gritty Bleach Docu-Cut*, *Vintage Campus Memories*).
    - `create_recipe_from_video(...)` (ephemeral upload or local media analysis).
    - `create_recipe_from_url_pattern(...)` (zero-download compliant URL + descriptor mapping).
    - `apply_style_recipe_to_timeline(...)` applying abstract rules (aspect ratio, color grade, vignette/grain, speed ramp, transitions, pacing normalization) cleanly while returning `TimelineDiffSummary` & pushing revision history.
- **Task 7.4: FastAPI Routes & Director Plan Support**
  - Create `backend/api/routes_trends.py` implementing all `/api/v1/trends/*` endpoints and register `trends_router` in `backend/api/main.py`.
  - Update `backend/ai_director/director.py` to apply `request.style_recipe_id` cleanly during storyboard planning when specified.

### Wave 3 — Studio UI Integration & Automated Tests
- **Task 7.5: Frontend Trend Style Recipe Modal & Copilot Integration**
  - Add trend API types & helpers in `apps/web/src/lib/api.ts`.
  - Create `apps/web/src/components/editor/StyleRecipeModal.tsx` allowing students to browse curated recipes, analyze an uploaded reference clip (ephemeral) or safe URL descriptor, inspect extracted Cut/Velocity/Color telemetry + copyright compliance badge, and apply any recipe onto their timeline.
  - Wire recipe selection & 1-click application into `AiDirectorDrawer.tsx` and `editor/page.tsx` cleanly using Undo/Redo snapshots.
- **Task 7.6: Automated Unit, Security & Integration Tests**
  - `tests/unit/test_trend_intelligence.py`: Test URL SSRF/private-IP/file-scheme blocking, motion velocity & cut cadence extraction on synthetic multi-cut MP4s, color mood mapping (`golden_hour` vs `moody_dark`), and timeline style transfer clamping.
  - `tests/integration/test_trend_recipes_api.py`: End-to-end API tests verifying seeded built-in recipes, ephemeral reference MP4 upload analysis (confirming temporary upload deletion after analysis!), safe URL recipe creation, SSRF/blocked-scheme 400/422 guards, `POST /director/plan` with `style_recipe_id`, and `POST /trends/recipes/{id}/apply` with Undo/Redo diff check.

---

## 🔍 Verification & Acceptance Gates

1. **Reference Analysis Accuracy Gate:** Analyzing a multi-cut synthetic MP4 detects cuts/minute, non-zero motion velocity score, color palette hex swatches, and recommends a matching LUT/ramp without retaining raw reference media.
2. **Copyright Safety & SSRF Gate:** Requests targeting `file://`, `http://127.0.0.1`, `http://169.254.169.254`, `http://192.168.1.1`, or invalid schemes are strictly blocked (`400`/`422`), and URL pattern analysis sets `media_downloaded=False` and `copyright_safe=True`.
3. **Style Transfer & Director Gate:** Applying a `StyleRecipe` via `POST /trends/recipes/{id}/apply` or `POST /director/plan` (`style_recipe_id`) modifies timeline color grade, effects, pacing/ramps, and produces a valid `TimelineDiffSummary` + revision record.
4. **Full Regression & Build Gate:** All `pytest tests -v` suites pass (`100%`) and `npm --prefix apps/web run build` exits `0`.

---

## 🚀 Execution Command

Run:
```bash
/gsd-execute-phase 7
```

