# PHASE 6 RESEARCH: Voice & Conversational Editing

> **Phase:** 06 — Voice & Conversational Editing  
> **Target:** Local `faster-whisper` Speech-to-Text, Microphone Voice Capture, Conversational Timeline Editor, Diff & Revision History Manager, and Partial Segment Re-Rendering  
> **Status:** Research Complete

---

## 1. Local Speech-to-Text (`faster-whisper` & `FR-04.4`)

- **Selected Engine:** `faster-whisper>=1.0.3` (MIT License, already declared in `backend/requirements.txt`) built on CTranslate2 (`INT8` CPU quantization).
- **Audio Preprocessing Pipeline:** Incoming microphone recordings (`audio/webm`, `audio/ogg`, `audio/wav`, `audio/mp3`) and uploaded video/audio assets are decoded via parameterized FFmpeg (`shell=False`) to `16,000 Hz` mono `pcm_s16le` WAV (`-vn -ac 1 -ar 16000 -f wav`) before transcription.
- **Word-Level Caption Generation:** `model.transcribe(..., word_timestamps=True)` yields timestamped segments and word timings grouped automatically into readable `SubtitleCue` blocks (`<= 7` words per cue) ready for Track `T1` preview and ASS subtitle burn-in.
- **Offline & Missing-Weight Resilience (`V-07`):**
  - Exposes `GET /api/v1/voice/status` reporting `package_installed`, `model_name`, `model_cached`, and `ready`.
  - When Whisper weights are not yet cached offline, server startup and editing continue cleanly without network hangs; missing-model transcription calls return clear HTTP `503` guidance while unit/integration tests support injectable transcriber verification cleanly offline.

---

## 2. Conversational Editing & Diff Architecture (`FR-07.1`, `FR-07.2`)

Whereas Phase 4 (`POST /api/v1/director/plan`) creates a fresh 4-act storyboard from scratch, Phase 6 adds incremental conversational editing (`POST /api/v1/director/edit`) over an active `TimelinePlan`:

1. **Deterministic Command Parser (Zero-Cost Offline Baseline):**
   - **Clip Replacement / Swap:** *"Replace clip 2 with the sunset"*, *"Swap clip 1 with fireworks"* -> resolves 1-based clip index or keyword match, finds best unique non-duplicate asset/scene via CV search & tag ranking, clamps trim bounds to valid source duration.
   - **Trimming, Speed & Ramps:** *"Trim clip 1 by 2 seconds"*, *"Make the cut faster"*, *"Slow down clip 2"*, *"Apply fast to slow ramp on clip 1"* -> scales speeds safely inside `[0.25, 4.0]`, updates `duration_seconds`, and cascades downstream `timeline_start_seconds`.
   - **Color Grade, Effects, Aspect Ratio & Transitions:** *"Change to golden hour"*, *"Switch to bleach bypass"*, *"Add film grain and vignette"*, *"Switch to 9:16 vertical reel"*, *"Change clip 2 transition to wipe left"*.
   - **Structural & Beat/Subtitle Edits:** *"Remove clip 3"*, *"Move clip 3 before clip 1"*, *"Snap cuts to music beats"*, *"Remove subtitles"*.
2. **Optional Ollama Assist:** When `use_llm=True` and Ollama is reachable, structured patch proposals are validated against source media bounds before applying, falling back deterministically if Ollama is offline or returns malformed output.
3. **Timeline Diff Calculator (`diff_engine.py`):** Computes exact `added_clip_ids`, `removed_clip_ids`, `modified_clip_ids`, `shifted_clip_ids`, `unchanged_clip_ids`, `global_visual_changed`, `affected_segment_indices`, and human-readable `changes`.
4. **Persistent Undo/Redo History (`timeline_revisions` SQLite table):** Stores cursor-indexed project revisions so Undo/Redo works reliably across edits (`clips`, `subtitles`, `color_grade`, `aspect_ratio`, `cinematic_effects`).

---

## 3. Partial Segment Caching & Fast Re-Rendering

Inspecting `backend/video_engine/filtergraph.py` and `backend/rendering/renderer.py` shows Stage 1 per-clip normalization performs the heaviest work (source decode, scale/pad, `zoompan` Ken Burns, `split+setpts` speed ramps, color LUT):

- Computing a deterministic SHA-256 `segment_key` per clip (`source_id`, file size, trims, `playback_speed`, `speed_ramp`, effective `color_grade`, `ken_burns_on_images`, target `width` x `height`, `fps`, and edge fade flags) allows untouched normalized clips to be cached in `data/cache/segments/{segment_key}.mp4`.
- On subsequent renders after a single-clip conversational edit (or caption/audio change), unchanged clips are read directly from cached intermediate MP4s (`segment_cache_hits`), while only modified/added clips are re-encoded (`segment_cache_misses`), reporting `partial_rerender_used`, `segment_cache_hits`, and `segment_cache_misses` on `RenderJobStatus`.

---

## 4. Browser Voice Command Capture

- Replaces the Phase 1 simulated `setTimeout` microphone stub in `AiDirectorDrawer.tsx` with a real [`VoiceCommandButton`](file:///c:/Users/mithu/ai%20video%20editing/apps/web/src/components/editor/VoiceCommandButton.tsx) supporting:
  1. **Whisper Microphone Capture:** `navigator.mediaDevices.getUserMedia` + `MediaRecorder` uploading audio blobs to `POST /api/v1/voice/transcribe` when local Whisper is ready.
  2. **Browser Web Speech API Fallback:** Live `SpeechRecognition` / `webkitSpeechRecognition` dictation when offline without local Whisper model weights.
