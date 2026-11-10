# PHASE 6 PLAN: Voice & Conversational Editing

> **Phase:** 06 — Voice & Conversational Editing  
> **Status:** READY FOR EXECUTION  
> **Goal:** Install `faster-whisper` cleanly in `backend/.venv`, build local Whisper speech-to-text & auto-captioning (`POST /api/v1/voice/transcribe`), implement incremental conversational editing (`POST /api/v1/director/edit`) with Ollama + deterministic command parser, compute timeline diffs & SQLite Undo/Redo revision history, accelerate re-exports with partial segment caching, and wire real microphone voice capture + Chat Copilot diff feedback into the Next.js Studio UI.

---

## 🎯 Phase Objectives

1. **Local Whisper Speech-to-Text (`faster-whisper`):** Install `faster-whisper` in `backend/.venv`, add `WHISPER_*` settings in `config.py`, and implement `backend/audio_engine/transcriber.py` (FFmpeg 16 kHz mono WAV preprocessing, word-level timestamps, `SubtitleCue` generation, and offline status reporting).
2. **Voice & Auto-Subtitle Endpoints:** Create `backend/api/routes_voice.py` (`/api/v1/voice/status`, `/api/v1/voice/transcribe`, `/api/v1/voice/subtitles/{media_id}`) and register it in `backend/api/main.py`.
3. **Conversational Editor & Timeline Diff Engine:** Build `backend/ai_director/conversational_editor.py` and `backend/ai_director/diff_engine.py` supporting natural iterative commands (clip replace/swap, trim, speed/speed-ramp, LUT/effects, transitions, aspect ratio, reorder/delete, beat-sync, subtitles) with structural diffs and `POST /api/v1/director/edit`.
4. **State History Manager (Undo / Redo Persistence):** Add `timeline_revisions` SQLite table + repository methods in `backend/api/database.py` and expose `/api/v1/projects/{id}/history`, `/undo`, `/redo` in `backend/api/routes_projects.py`.
5. **Partial Segment Re-Rendering Cache:** Add deterministic per-clip segment caching (`backend/rendering/segment_cache.py`) integrated into `backend/rendering/renderer.py` + `RenderJobStatus` (`segment_cache_hits`, `segment_cache_misses`, `partial_rerender_used`).
6. **Frontend Voice Capture, Chat Copilot & Undo/Redo Sync:** Build `VoiceCommandButton.tsx`, upgrade `AiDirectorDrawer.tsx`, `ExportModal.tsx`, `api.ts`, and `editor/page.tsx` with real mic capture, "Chat Edit" vs "New Cut" modes, diff summaries, Auto-Caption button, and full multi-property Undo/Redo snapshots.

---

## 🌊 Wave-Based Task Breakdown

### Wave 1 — Dependencies, Schemas, Database History & Whisper Transcriber
- **Task 6.1: Install `faster-whisper` & Extend Config/Schemas/SQLite**
  - Install `faster-whisper>=1.0.3` inside `backend/.venv`.
  - Add `WHISPER_MODEL`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE`, `WHISPER_LOCAL_FILES_ONLY`, and `MAX_SEGMENT_CACHE_MB` in `backend/api/config.py`.
  - Add Pydantic schemas in `backend/api/schemas.py`: `TranscriptWord`, `TranscriptSegment`, `TranscriptionResponse`, `WhisperStatusResponse`, `ConversationalEditRequest`, `ConversationalEditResponse`, `TimelineDiffSummary`, `TimelineRevisionRecord`, `ProjectHistoryResponse`; add `partial_cache: bool = True` on `RenderRequest` and `segment_cache_hits` / `segment_cache_misses` / `partial_rerender_used` on `RenderJobStatus`.
  - Add `timeline_revisions` table + cursor-based revision save/undo/redo methods in `backend/api/database.py`.
- **Task 6.2: Local Whisper Transcriber & Voice API Routes**
  - Implement FFmpeg 16 kHz mono WAV audio extraction + `faster-whisper` transcription + `SubtitleCue` builder in `backend/audio_engine/transcriber.py`.
  - Create `backend/api/routes_voice.py` (`/voice/status`, `/voice/transcribe`, `/voice/subtitles/{media_id}`) and register `voice_router` in `backend/api/main.py`.

### Wave 2 — Conversational Editing Parser, Diff Calculator & Partial Segment Cache
- **Task 6.3: Timeline Diff Engine & Conversational Editor**
  - Implement `compute_timeline_diff(before, after)` in `backend/ai_director/diff_engine.py`.
  - Implement `apply_conversational_edit(...)` in `backend/ai_director/conversational_editor.py` with deterministic multi-operation NLP parsing + optional Ollama JSON patch assist + validator safety clamping & revision recording.
  - Expose `POST /api/v1/director/edit` in `backend/api/routes_director.py` and `/history`, `/undo`, `/redo` in `backend/api/routes_projects.py`.
- **Task 6.4: Partial Segment Caching & Selective Re-Rendering**
  - Implement `backend/rendering/segment_cache.py` computing per-clip SHA-256 content keys, pre-rendering cache-miss clips via FFmpeg intermediate encodes, reusing cache-hit clips directly, and enforcing cache size limits.
  - Integrate segment cache into `backend/rendering/renderer.py` & `backend/job_manager/queue.py` (exposing `segment_cache_hits`, `segment_cache_misses`, `partial_rerender_used` cleanly without breaking existing `filtergraph.py` contracts).

### Wave 3 — Frontend Voice Capture, Conversational Copilot & Automated Tests
- **Task 6.5: Real Microphone Component, Chat Edit Drawer & Multi-Property Undo/Redo**
  - Create `apps/web/src/components/editor/VoiceCommandButton.tsx` (Whisper `MediaRecorder` upload + Web Speech API live dictation fallback).
  - Upgrade `apps/web/src/lib/api.ts`, `apps/web/src/components/editor/AiDirectorDrawer.tsx`, `apps/web/src/components/editor/ExportModal.tsx`, and `apps/web/src/app/editor/page.tsx`:
    - Chat Edit mode calling `POST /api/v1/director/edit` and rendering diff summaries (`modified`, `added`, `removed`, `preserved`).
    - Auto-Transcribe Audio/Video to `T1` Subtitles button (`POST /api/v1/voice/subtitles/{media_id}`).
    - Full `TimelineSnapshot` Undo/Redo (`clips`, `subtitles`, `colorGrade`, `aspectRatio`, `cinematicEffects`).
    - Export modal display of partial segment cache speedup (`segment_cache_hits` / `partial_rerender_used`).
- **Task 6.6: Unit & Integration Test Suites**
  - `tests/unit/test_conversational_editor_and_diff.py`: Test clip replacement, trim/speed edits, LUT/vignette/aspect mutations, reorder/delete, diff counts, and segment cache hash invalidation/hit logic.
  - `tests/unit/test_transcriber_unit.py`: Test FFmpeg 16 kHz mono WAV extraction on synthetic audio, `TranscriptSegment` -> `SubtitleCue` chunking, and offline missing-model graceful handling.
  - `tests/integration/test_voice_and_partial_render_api.py`: End-to-end API tests for `/voice/status`, `/voice/transcribe` (with monkeypatched Whisper decoder), `/director/edit`, `/projects/{id}/history` -> `undo` -> `redo`, and two sequential MP4 renders verifying `segment_cache_hits > 0` & `partial_rerender_used is True` on the second edited render, verified by `probe_media_file`.

---

## 🔍 Verification & Acceptance Gates

1. **Speech-to-Text Gate:** `POST /api/v1/voice/transcribe` converts uploaded WebM/WAV audio cleanly via FFmpeg to 16 kHz mono WAV, returns segments + `SubtitleCue` suggestions, and degrades gracefully offline if Whisper weights are uncached.
2. **Conversational Edit & Diff Gate:** Sending natural commands (e.g., *"Replace clip 2 with broll"*, *"Trim clip 1 by 1 second"*, *"Change to bleach bypass"*) updates only affected timeline parts, reports accurate `TimelineDiffSummary`, and persists revision snapshots.
3. **Undo/Redo State History Gate:** `POST /projects/{id}/undo` and `POST /projects/{id}/redo` restore full multi-track + grading/subtitle state accurately.
4. **Partial Re-Render Cache Gate:** Rendering an edited timeline after an initial render yields `segment_cache_hits >= 1`, `partial_rerender_used is True`, and a valid H.264/AAC MP4 verified by `ffprobe`.
5. **Full Regression & Build Gate:** All `pytest tests -v` suites pass (`100%`) and `npm --prefix apps/web run build` exits `0`.

---

## 🚀 Execution Command

Run:
```bash
/gsd-execute-phase 6
```
