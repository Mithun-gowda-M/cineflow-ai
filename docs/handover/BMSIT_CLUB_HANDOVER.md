# BMSIT Technical & Media Club Handover Manual

> **Maintainers:** BMSIT Engineering Technical / Media Club Leads  
> **Architecture:** Monorepo (`apps/web` Next.js 15 + `backend/` Python 3.12 FastAPI)  
> **Zero Recurring Cloud Billing:** FFmpeg, PySceneDetect, OpenCV, Librosa, faster-whisper, Ollama, PyJWT, psutil.

---

## 1. Repository & Service Map

| Module Path | Responsibility | Key Entry Points |
| :--- | :--- | :--- |
| `apps/web/` | Next.js 15 Studio UI (`/editor`, `/upload`, `/dashboard`, `/admin`, `/auth/*`) | `apps/web/src/lib/api.ts`, `apps/web/src/app/editor/page.tsx` |
| `backend/api/` | FastAPI REST routers, Pydantic v2 contracts, SQLite store | `backend/api/main.py`, `backend/api/database.py`, `backend/api/schemas.py` |
| `backend/authentication/` | `scrypt` password hashing, HS256 JWT RBAC, user storage quotas | `backend/authentication/security.py`, `backend/authentication/quotas.py` |
| `backend/media_analysis/` | Upload validation, FFprobe inspection, 720p proxies, PySceneDetect & OpenCV scoring | `backend/media_analysis/pipeline.py`, `backend/media_analysis/validator.py` |
| `backend/ai_director/` | Prompt parser, Ollama client + offline 4-act fallback, conversational diff & Undo/Redo | `backend/ai_director/director.py`, `backend/ai_director/conversational_editor.py` |
| `backend/audio_engine/` | Librosa BPM/beat/waveform analyzer, beat-sync cutter, sidechain ducking, Whisper STT | `backend/audio_engine/analyzer.py`, `backend/audio_engine/transcriber.py` |
| `backend/video_engine/` | Parameterized FFmpeg filtergraph (`shell=False`), ASS subtitle generator, GPU probe | `backend/video_engine/filtergraph.py`, `backend/video_engine/typography.py` |
| `backend/rendering/` | Async render orchestration, SHA-256 partial segment cache, TTL disk cleanup | `backend/rendering/renderer.py`, `backend/rendering/segment_cache.py`, `cleanup.py` |
| `backend/trend_intelligence/` | Copyright-safe reference video analyzer, curated style recipes, SSRF guard | `backend/trend_intelligence/analyzer.py`, `safety.py`, `recipe_generator.py` |
| `backend/migrations/` | PostgreSQL 15+ DDL and SQLite -> Postgres verification/migration CLI | `backend/migrations/001_postgres_initial.sql`, `sqlite_to_postgres.py` |

---

## 2. Common Club Maintainer Operations

### Adding a New Curated Color Look (LUT)
1. Add the LUT key to `ColorGradePreset` in `backend/api/schemas.py` and `apps/web/src/types/index.ts`.
2. Define its FFmpeg filter expression inside `_COLOR_GRADE_FILTERS` (`backend/video_engine/filtergraph.py`) and CSS preview filter inside `VideoPreviewCanvas.tsx`.
3. Add a unit test case verifying its filtergraph output.

### Adding a New Built-in Festival Style Recipe
- Append a specification entry to `_BUILTIN_RECIPES` inside `backend/trend_intelligence/recipe_generator.py`. Built-in presets are seeded idempotently and protected from student deletion (`403`).

### Running the Full Regression Suite Before Updating Server Branches
```powershell
# Backend unit, security/SSRF, auth/RBAC/quota, and real FFmpeg render tests
backend\.venv\Scripts\python.exe -m pytest tests -v

# Frontend production typecheck, lint & bundle
npm --prefix apps/web run build
```

---

## 3. Semester Club Lead Audit Checklist
- [ ] Rotate `SECRET_KEY` in `.env` and update Club Admin password.
- [ ] Verify FFmpeg (`ffmpeg -version`) and `Ollama` (`ollama list`, if running locally) are healthy via `/api/v1/health`.
- [ ] Run `/admin` diagnostics or `POST /api/v1/admin/cleanup` before annual cultural fest shoots to reclaim stale cache/renders cleanly.
- [ ] Back up `data/cineflow.db` (or PostgreSQL dump via `pg_dump`) prior to upgrades.

