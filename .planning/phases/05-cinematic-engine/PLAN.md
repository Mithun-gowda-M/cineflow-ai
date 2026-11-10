# PHASE 5 PLAN: Advanced Cinematic Engine & Audio Intelligence

> **Phase:** 05 — Advanced Cinematic Engine & Audio Intelligence  
> **Status:** COMPLETED  
> **Goal:** Install `librosa` and `soundfile`, implement beat/tempo/waveform/silence extraction, build beat-synchronized timeline alignment, add multi-phase speed ramps, Ken Burns image zoom, `bleach_bypass` grading, vignette/film-grain effects, ASS animated typography burn-in, sidechain audio ducking + `loudnorm`, and enrich the Studio UI with live waveforms, beat markers, and look/text controls.

---

## 🎯 Phase Objectives

1. **Audio Engine Dependencies:** Install and verify `librosa` and `soundfile` inside `backend/.venv`.
2. **Librosa Audio Intelligence (`backend/audio_engine/analyzer.py`):** Extract BPM, beat timestamps, downbeats, 64-bar normalized waveform peaks, silence intervals, and audio energy peaks from uploaded audio and video streams.
3. **Beat-Synchronized Cut Aligner (`backend/audio_engine/beat_sync.py`):** Snap timeline clip transitions toward musical downbeats within tolerance (`±0.35s`) while respecting source duration limits and anti-duplication rules.
4. **Cinematic Video & Typography Engine:**
   - Add `bleach_bypass` LUT, toggleable `vignette` & `film_grain`, `zoompan` Ken Burns motion for still images, and multi-phase `speed_ramp` presets (`fast_to_slow`, `slow_to_fast`).
   - Implement `.ass` animated subtitle/typography generator (`backend/video_engine/typography.py`) burned directly into MP4 renders via FFmpeg `libass`.
   - Upgrade audio mixing (`backend/audio_engine/mixer.py`) with `sidechaincompress` ducking and EBU R128 `loudnorm`.
5. **FastAPI Audio Endpoints & Director Beat-Sync:** Expose `/api/v1/audio/{id}/analyze` & `/api/v1/audio/beat-sync`, and optionally align AI Director plans automatically when music tracks exist.
6. **Frontend Studio Enrichment & Automated Tests:** Display real Librosa BPM/waveform/beat-grid markers on `MultiTrackTimeline`, expose `Bleach Bypass`, Vignette, Film Grain, Speed Ramp, and Beat-Sync controls in the Editor UI, and verify real rendered outputs via `pytest`.

---

## 🌊 Wave-Based Task Breakdown

### Wave 1 — Dependencies, Schemas & Librosa Audio Intelligence

- **Task 5.1: Install Librosa & Extend Schemas/DB**
  - Install `librosa` and `soundfile` in `backend/.venv`.
  - Extend `backend/api/schemas.py` (`ColorGradePreset` adds `"bleach_bypass"`; `SpeedRampPreset`, `CinematicEffects`, `AudioAnalysisResult`, `BeatSyncRequest`, `BeatSyncResponse`) and update `backend/api/database.py` with `audio_analysis_json` migration.
- **Task 5.2: Librosa Beat, Tempo, Waveform & Silence Analyzer**
  - Implement `analyze_audio_file(...)` with FFmpeg PCM WAV extraction fallback for compressed containers (`mp4`, `mp3`, `aac`), computing BPM, beats, downbeats, 64-bar waveform, energy peaks, and silence ratio.
  - **Target File:** `backend/audio_engine/analyzer.py`

### Wave 2 — Beat Sync, Animated Typography, Speed Ramps & Sidechain Ducking

- **Task 5.3: Beat-Synchronized Cut Aligner**
  - Implement `align_timeline_to_beats(...)` aligning clip cuts/transitions to musical beats & downbeats cleanly while preserving source trim bounds and anti-duplication guarantees.
  - **Target File:** `backend/audio_engine/beat_sync.py`
- **Task 5.4: ASS Animated Typography & Enhanced Cinematic Filtergraph**
  - Implement `generate_ass_subtitles(...)` with Windows-safe FFmpeg filter path escaping (`backend/video_engine/typography.py`).
  - Upgrade `backend/video_engine/filtergraph.py` with `bleach_bypass`, `vignette`, `film_grain`, `zoompan` on still images, multi-phase `speed_ramp` splitting, and `.ass` subtitle burn-in.
  - Upgrade `backend/audio_engine/mixer.py` with `sidechaincompress` ducking and `loudnorm` loudness normalization.

### Wave 3 — API Routes, Director Integration, Frontend Studio & Automated Tests

- **Task 5.5: FastAPI Audio Routes & Automatic Audio Analysis**
  - Auto-run `analyze_audio_file` when audio assets are ingested (`routes_media.py` / `pipeline.py`).
  - Create `backend/api/routes_audio.py` (`/audio/{id}/analyze`, `/audio/{id}/analysis`, `/audio/beat-sync`) and register in `main.py`; wire optional beat sync into `ai_director/director.py`.
- **Task 5.6: Frontend Cinematic Controls, Live Waveforms & Beat Grid**
  - Update `apps/web/src/lib/api.ts`, `types/index.ts`, `MultiTrackTimeline.tsx`, `AiDirectorDrawer.tsx`, `VideoPreviewCanvas.tsx`, and `editor/page.tsx` with `Bleach Bypass`, Vignette, Film Grain, Speed Ramp picker, Beat-Sync trigger, and real waveform + beat markers!
- **Task 5.7: Unit & Real Rendering Integration Tests**
  - Test Librosa BPM & beat extraction on synthetic rhythmic click-track WAVs (e.g., 120 BPM drum/tone pulses!), beat-sync alignment accuracy, ASS subtitle file generation & Windows filter escaping, speed ramps + `bleach_bypass` + `vignette` + `film_grain` + `sidechaincompress` + `loudnorm` real FFmpeg MP4 render verified via `ffprobe`!
  - **Target Files:**
    - `tests/unit/test_audio_and_typography.py`
    - `tests/integration/test_cinematic_engine_api.py`

---

## 🔍 Verification & Acceptance Gates

1. **Librosa Beat Accuracy Gate:** Analyzing a synthetic 120 BPM rhythmic pulse WAV returns tempo within `115–125 BPM` (or octave `60`/`240`), non-empty beat/downbeat timestamps, and 64 normalized waveform peaks.
2. **Beat-Sync Alignment Gate:** `POST /api/v1/audio/beat-sync` snaps clip transitions cleanly toward beat/downbeat timestamps without exceeding source durations or duplicating clips.
3. **Cinematic Render Gate:** Rendering a `TimelinePlan` with `bleach_bypass`, `vignette=True`, `film_grain=True`, `speed_ramp="fast_to_slow"`, burned-in `SubtitleCue`s, and ducked background music (`sidechaincompress` + `loudnorm`) produces a valid H.264/AAC MP4 verified by `ffprobe`.
4. **Full Regression & Build Gate:** All Phase 2–5 `pytest` tests pass (`100%`) and `apps/web` `npm run build` exits with code `0`.

---

## 🚀 Execution Command

Run:

```bash
/gsd-execute-phase 5
```
