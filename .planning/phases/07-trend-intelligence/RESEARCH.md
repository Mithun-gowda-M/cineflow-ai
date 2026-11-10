# PHASE 7 RESEARCH: Trend Intelligence (Optional Style Recipes)

> **Phase:** 07 — Trend Intelligence (Optional Style Recipes)  
> **Target:** Reference Video Style Analyzer (Cut Frequency, Motion Velocity, Color Mood), Abstract Style Recipe Generator, AI Director Style Transfer, and Strict Copyright-Safe Guardrails  
> **Status:** Research Complete

---

## 1. Existing Analysis Primitives Available for Reuse

Inspection of the Phase 3–6 backend confirmed that all computational primitives needed for quantitative reference video analysis already exist inside `backend/.venv`:

- **Cut & Pacing Extraction (`backend/media_analysis/scene_detector.py`):**
  - Reuses PySceneDetect `ContentDetector` intervals across sampled frames to measure cut count, cuts per minute (`cuts / duration * 60`), average shot duration (`duration / shots`), and cadence tier (`rapid`, `moderate`, `deliberate`).
- **Color Mood & Luminance Analysis (`backend/media_analysis/cv_analyzer.py`):**
  - Reuses `analyze_video_segment(...)` to extract `mean_luminance`, `warm_pixel_ratio`, `saturation_mean`, `dominant_colors`, `dark_with_bright_spikes`, and frame-to-frame luminance delta stability scores, mapping deterministically to all 7 CINEFLOW color looks (`natural`, `golden_hour`, `cinematic_teal_orange`, `moody_dark`, `vintage_film`, `bleach_bypass`, `high_contrast_bw`) plus vignette / 35mm film grain cues.
- **Motion Velocity & Speed Ramps:**
  - Computing consecutive frame grayscale pixel delta + stability variance produces a continuous `motion_velocity_score` (`0.0–100.0`) classifying clips into `static`, `smooth_glide`, `dynamic_burst`, or `high_velocity` and deriving matching `speed_ramp` presets (`fast_to_slow`, `slow_to_fast`, `ease_in_out`, `none`).

---

## 2. Copyright Safety & Zero-Scraping Architecture (`FR-08.2`)

To enforce strict academic, hackathon, and legal compliance:

1. **Zero Unauthorized Media Downloads:** No `yt-dlp`, third-party video grabbers, HTML scrapers, or social media cookie-harvesting libraries are ever added or executed.
2. **Ephemeral Reference Uploads:** Temporary reference uploads analyzed via `POST /api/v1/trends/analyze-upload` are validated with `media_analysis/validator.py` magic-byte/extension guards, analyzed purely for numeric editing statistics, and deleted immediately inside a `finally:` block so zero raw frames, subtitles, or reference audio persist or leak into timelines.
3. **SSRF & Private URL Guard (`safety.py`):** URL pattern requests (`POST /api/v1/trends/analyze-url`) validate URL syntax, reject non-HTTP(S) schemes (`file://`, `ftp://`, `javascript:`), block private/loopback/link-local/metadata IP targets (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`, `localhost`), perform zero stream fetching or scraping (`media_downloaded=False`), and convert user-supplied descriptors + URL aspect cues (e.g., `/shorts/`, `/reel/`) cleanly into original abstract editing rules.

---

## 3. Abstract Style Recipe Data Model & AI Director Integration

- Each `StyleRecipe` encapsulates abstract, copyright-free parameters (`cuts_per_minute`, `avg_shot_duration_seconds`, `motion_velocity_score`, `color_mood`, `recommended_color_grade`, `recommended_aspect_ratio`, `recommended_pacing`, `recommended_speed_ramp`, `recommended_transition`, `cinematic_effects`, `dominant_palette`, `prompt_hint`, `copyright_safe=True`).
- Stored in SQLite `style_recipes` table alongside 5 curated built-in studio templates (protected from accidental deletion).
- Wired directly into `POST /api/v1/director/plan` via optional `style_recipe_id` and applied 1-click onto active timelines via `POST /api/v1/trends/recipes/{recipe_id}/apply` with full diff calculation (`diff_engine.py`) and Undo/Redo revision tracking (`database.py`).
