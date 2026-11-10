# CINEFLOW AI — REST API Reference (`/api/v1`)

> **Interactive OpenAPI Docs:** Run the FastAPI server and browse `http://127.0.0.1:8000/docs` or `/redoc`.  
> **Base Prefix:** `/api/v1` (except static media mounts at `/static/{uploads,proxies,renders}`).

---

## 1. System & Hardware Health

| Method | Endpoint | Response Model | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | `HealthResponse` | FFmpeg/FFprobe paths, hardware profile (`low`/`medium`/`high`), CPU cores, detected encoders (`h264_qsv`, `libx264`). |

---

## 2. Media Ingestion, Search & Scene Intelligence (`/media`)

| Method | Endpoint | Response Model | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/media/upload` | `MediaUploadResponse` | Batch upload MP4/MOV/MKV/WebM/JPG/PNG/MP3/WAV with magic-byte checks, quota check (`413`), FFprobe, 720p proxy, & CV analysis. |
| `GET` | `/api/v1/media` | `list[MediaAsset]` | List ingested media assets with optional `media_kind` filter. |
| `GET` | `/api/v1/media/search` | `MediaSearchResponse` | Natural-language keyword, semantic tag, quality floor, & duplicate-free clip ranking. |
| `GET` | `/api/v1/media/{media_id}` | `MediaAsset` | Fetch full metadata, quality breakdown, and scenes for one asset. |
| `POST` | `/api/v1/media/{media_id}/analyze` | `MediaAsset` | Run/refresh OpenCV quality scoring, PySceneDetect cuts, and perceptual dHash. |
| `POST` | `/api/v1/media/analyze-all` | `list[MediaAsset]` | Batch-analyze unanalyzed library items. |
| `GET` | `/api/v1/media/{media_id}/scenes` | `list[DetectedScene]` | Return detected scene boundaries with sharpness & motion scores. |
| `DELETE` | `/api/v1/media/{media_id}` | `dict` | Ownership-checked asset deletion (`403` if owned by another student). |

---

## 3. Projects & Persistent Revision History (`/projects`)

| Method | Endpoint | Response Model | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/projects` | `ProjectResponse` (`201`) | Create a new editing workspace project. |
| `GET` | `/api/v1/projects` | `list[ProjectResponse]` | List persisted projects sorted by `updated_at`. |
| `GET` | `/api/v1/projects/{project_id}` | `ProjectResponse` | Fetch project metadata and active `TimelinePlan` JSON. |
| `PATCH` | `/api/v1/projects/{project_id}` | `ProjectResponse` | Update project title, aspect ratio, color grade, or `TimelinePlan`. |
| `DELETE` | `/api/v1/projects/{project_id}` | `dict` | Delete project from storage. |
| `GET` | `/api/v1/projects/{project_id}/history` | `ProjectHistoryResponse` | Retrieve timeline revision log and Undo/Redo flags. |
| `POST` | `/api/v1/projects/{project_id}/undo` | `ProjectHistoryResponse` | Step backward one timeline revision in SQLite. |
| `POST` | `/api/v1/projects/{project_id}/redo` | `ProjectHistoryResponse` | Step forward one timeline revision in SQLite. |

---

## 4. AI Director & Conversational Copilot (`/director`)

| Method | Endpoint | Response Model | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/director/status` | `DirectorStatusResponse` | Check local Ollama availability, configured model, and offline fallback status. |
| `POST` | `/api/v1/director/plan` | `DirectorPlanResponse` | Generate a 4-act storyboard & `TimelinePlan` (supports optional `style_recipe_id`). |
| `POST` | `/api/v1/director/edit` | `ConversationalEditResponse` | Parse natural language/voice command, mutate timeline, emit diff summary, & record revision. |

---

## 5. Audio Intelligence & Speech Transcription (`/audio`, `/voice`)

| Method | Endpoint | Response Model | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/audio/{media_id}/analyze` | `MediaAsset` | Compute Librosa BPM tempo, beat timestamps, downbeats, waveform peaks, & silence ratio. |
| `GET` | `/api/v1/audio/{media_id}/analysis` | `AudioAnalysisResult` | Fetch cached audio analysis metrics for a media item. |
| `POST` | `/api/v1/audio/beat-sync` | `BeatSyncResponse` | Snap video clip boundaries onto musical beats within source duration constraints. |
| `GET` | `/api/v1/voice/status` | `WhisperStatusResponse` | Report local `faster-whisper` (`tiny`/`int8`) availability & model readiness. |
| `POST` | `/api/v1/voice/transcribe` | `TranscriptionResponse` | Transcribe an uploaded voice command or dialogue clip locally on CPU. |
| `POST` | `/api/v1/voice/subtitles/{media_id}` | `TranscriptionResponse` | Generate word-timestamped subtitle cues from a project media asset. |

---

## 6. FFmpeg Rendering & Segment Cache (`/render`)

| Method | Endpoint | Response Model | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/render` | `RenderJobStatus` (`202`) | Validate timeline assets and enqueue async FFmpeg filtergraph render (`partial_cache=true`). |
| `GET` | `/api/v1/render/{job_id}` | `RenderJobStatus` | Poll progress %, current stage, and segment cache hit/miss counts. |
| `POST` | `/api/v1/render/{job_id}/cancel` | `RenderJobStatus` | Terminate an in-flight render subprocess cleanly. |
| `GET` | `/api/v1/render/{job_id}/download` | `FileResponse` | Stream verified `video/mp4` render output (`409` if incomplete). |

---

## 7. Trend Intelligence & Copyright-Safe Style Recipes (`/trends`)

| Method | Endpoint | Response Model | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/trends/recipes` | `list[StyleRecipe]` | List curated BMSIT recipes and user-extracted style templates. |
| `GET` | `/api/v1/trends/recipes/{recipe_id}` | `StyleRecipe` | Retrieve a single `StyleRecipe` and its `TrendSafetyAudit`. |
| `POST` | `/api/v1/trends/analyze-media/{media_id}` | `StyleRecipe` | Extract cut cadence, motion velocity, & color mood from a library video. |
| `POST` | `/api/v1/trends/analyze-upload` | `StyleRecipe` | Ephemerally extract a style recipe from an uploaded clip, deleting raw footage after math extraction. |
| `POST` | `/api/v1/trends/analyze-url` | `StyleRecipe` | SSRF-guarded zero-download reference URL style mapping (`media_downloaded=false`). |
| `POST` | `/api/v1/trends/recipes/{recipe_id}/apply` | `StyleApplyResponse` | Apply abstract pacing, LUT, speed ramp, and effects onto a project timeline with Undo history. |
| `DELETE` | `/api/v1/trends/recipes/{recipe_id}` | `dict` | Delete user-created recipes (`403` protection on built-in recipes). |

---

## 8. Campus Auth, Admin & Hackathon Showcase (`/auth`, `/admin`, `/showcase`)

| Method | Endpoint | Response Model | Purpose |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | `AuthTokenResponse` (`201`) | Register student/club account with salted `scrypt` password & optional `@bmsit.in` domain gate. |
| `POST` | `/api/v1/auth/login` | `AuthTokenResponse` | Authenticate and return HS256 Bearer JWT. |
| `GET` | `/api/v1/auth/me` | `UserPublic` | Return authenticated profile (`401` if unauthenticated). |
| `GET` | `/api/v1/auth/quota` | `QuotaStatusResponse` | Return user's live disk usage vs. storage quota bytes. |
| `GET` | `/api/v1/admin/overview` | `AdminOverviewResponse` | Admin-only (`403` for students) `psutil` CPU/RAM/disk telemetry & render queue stats. |
| `GET` | `/api/v1/admin/users` | `list[AdminUserRecord]` | List institutional users with per-user bytes & project counts. |
| `PATCH` | `/api/v1/admin/users/{user_id}` | `AdminUserRecord` | Adjust user quota GB, role, or activation state. |
| `POST` | `/api/v1/admin/cleanup` | `CleanupResponse` | Purge expired temp/segment/render caches cleanly without touching source uploads. |
| `GET` | `/api/v1/admin/migration-status` | `MigrationStatusResponse` | Audit SQLite row counts and PostgreSQL 15+ DDL readiness. |
| `GET` | `/api/v1/showcase/status` | `ShowcaseStatusResponse` | Inspect committed Full-HD sample pack, seeded showcase project, and benchmark report status. |
| `POST` | `/api/v1/showcase/load` | `ShowcaseLoadResponse` | Ingest `assets/sample_media/*` via FFprobe/OpenCV/Librosa and seed `proj_bmsit_showcase_2026`. |
| `GET` | `/api/v1/showcase/benchmarks` | `ShowcaseBenchmarkReport` | Return latest measured host performance telemetry JSON. |
| `POST` | `/api/v1/showcase/benchmarks/run` | `ShowcaseBenchmarkReport` | Trigger a fresh isolated subprocess benchmark run cleanly. |

