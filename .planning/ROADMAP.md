# ROADMAP: CINEFLOW AI

> **Strategy:** Phased Delivery from Verified Foundation to Institutional Deployment  
> **Current Phase:** Phase 0 (Research & Architecture) Completed  
> **Next Immediate Phase:** Phase 1 (Premium Frontend Design System & Workspaces)

---

## Roadmap Overview

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6 ──► Phase 7 ──► Phase 8 ──► Phase 9
Foundations  Premium UI   Rendering   CV Intel    AI Director Cinematic   Voice/Chat  Trends      Campus      Hackathon
& Research   & Timeline   Pipeline    & Scenes    Engine      & Beats     Editing     Recipes     Deployment  Pitch Kit
```

---

## Detailed Phase Breakdown

### 🟢 Phase 0 — Research, Environment & System Architecture
- [x] Inspect development environment (Node.js 24, Python 3.12, Git 2.56, Hardware).
- [x] Initialize Git repository with `main` branch, `.gitignore`, and `.env.example`.
- [x] Create monorepo directory layout (`apps/web`, `backend/`, `packages/`, `docs/`, `tests/`).
- [x] Conduct deep research on 10 target open-source repositories & verify license compatibility.
- [x] Generate `docs/third_party_licenses/THIRD_PARTY_LICENSES.md`.
- [x] Define system architecture, data models, timeline JSON specification, and hardware profiles.
- [x] Establish GSD planning suite (`PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `config.json`).

---

### 🟡 Phase 1 — Premium Frontend Design System & Workspaces
- [ ] Initialize Next.js 15 app in `apps/web` with TypeScript, Tailwind CSS, Lucide icons, Framer Motion.
- [ ] Establish CINEFLOW dark cinematic design tokens (Midnight `#0B0D13`, Obsidian `#11141E`, Champagne Gold `#E5B869`, Cyan `#38BDF8`).
- [ ] Build high-converting Cinematic Landing Page ("Your Footage Deserves a Director") with hero teaser and interactive workflow simulation.
- [ ] Build Student Project Dashboard (project creation, storage quota gauge, recent projects list).
- [ ] Build Media Ingestion Workspace (drag-and-drop batch dropzone, metadata cards, asset pool).
- [ ] Build Professional Multi-Track Video Editor Workspace:
  - Video Preview Canvas with custom playback controls and timecode readout.
  - Multi-track timeline (Video V1/V2, Audio A1/A2, Subtitles T1).
  - Zoomable timeline ruler and scrubbable playhead.
  - Right-side AI Director drawer with prompt interface and clip inspector.
- [ ] Build Export Modal (aspect ratios: 16:9, 9:16, 1:1, 21:9, resolution selectors).

---

### 🟡 Phase 2 — Real Video Processing & Rendering Engine
- [ ] Configure and verify FFmpeg / FFprobe integration (with static bundling/PATH detection).
- [ ] Implement backend media upload endpoint in FastAPI with file validation and secure naming.
- [ ] Implement FFprobe metadata extractor (codec, resolution, duration, bitrate, audio channels).
- [ ] Implement automated 720p proxy generator for instant browser scrubbing.
- [ ] Build native FFmpeg filtergraph rendering pipeline:
  - Precise timestamp-based clip trimming.
  - Aspect ratio conforming (pad, crop, blur-fill).
  - Seamless concatenations with crossfade transitions (`xfade`).
  - Audio mixing and background music ducking (`amix`, `volume`).
- [ ] Implement export job runner with progress tracking and real MP4 export download endpoint.
- [ ] Create automated rendering integration test suite.

---

### 🟡 Phase 3 — AI Media Intelligence & Scene Detection
- [ ] Integrate PySceneDetect (`ContentDetector`, `AdaptiveDetector`) for automated scene splitting.
- [ ] Integrate OpenCV (`opencv-python-headless`) for frame quality analysis:
  - Laplacian variance sharpness / blur calculation.
  - Luminosity and contrast exposure assessment.
  - Dominant color palette extraction.
- [ ] Build multi-factor scoring engine (0–100 quality score with transparent metrics).
- [ ] Implement rule-based semantic auto-tagging (Diya, Fireworks, Landscape, Action, Portrait, Low-Light).
- [ ] Implement duplicate / near-duplicate shot detection.
- [ ] Expose media intelligence APIs to enrich the frontend asset library with badges and filters.

---

### 🟡 Phase 4 — AI Director & Storyboard Generator
- [ ] Create Pydantic schema for `TimelinePlan`, `SceneClip`, `TransitionSpec`, and `AudioCue`.
- [ ] Implement prompt parser for natural language creative instructions.
- [ ] Integrate local Ollama client (`llama3.2`, `mistral`) with structured JSON schema output.
- [ ] Implement algorithmic Rule-Based Director Fallback (guaranteeing 100% offline functionality).
- [ ] Build intelligent clip sequencer:
  - Narrative pacing curve (Opening hook -> Rising tempo -> Climax -> Resolution).
  - Quality score weighting (favor sharp, well-exposed shots).
  - Duration constraint solver (no artificial looping).
- [ ] Implement timeline validation and safety check before handing to renderer.

---

### 🟡 Phase 5 — Advanced Cinematic Engine & Audio Intelligence
- [ ] Integrate Librosa for audio beat tracking, tempo estimation, and onset strength.
- [ ] Implement beat-synchronized video cutting (snapping transitions to musical downbeats).
- [ ] Implement speed ramps (fast-motion acceleration into slow-motion impact).
- [ ] Implement cinematic color grading filtergraphs (Teal & Orange, Golden Hour, Moody Dark, Bleach Bypass).
- [ ] Implement animated typography and subtitle overlay filtergraphs (`drawtext` / ASS subtitles).
- [ ] Implement audio ducking and volume smoothing.

---

### 🟡 Phase 6 — Voice & Conversational Editing
- [ ] Integrate local Whisper (`faster-whisper` / `whisper.cpp`) for speech-to-text.
- [ ] Build frontend microphone voice-command capture component.
- [ ] Implement conversational command parser (e.g. *"Replace clip 2 with the sunset"*, *"Make the cut faster"*).
- [ ] Build timeline diff calculator and State History Manager (Undo / Redo support).
- [ ] Implement partial re-rendering for edited timeline segments.

---

### 🟡 Phase 7 — Trend Intelligence (Optional Style Recipes)
- [ ] Build reference video analyzer (extract cut frequency, motion velocity, color mood).
- [ ] Implement original style recipe generator (transforming reference patterns into abstract editing rules).
- [ ] Ensure strict adherence to copyright safety: zero private data scraping, zero unauthorized downloads.

---

### 🟡 Phase 8 — Institutional Campus Deployment & Security
- [ ] Implement student authentication (JWT, role-based access for students and club admins).
- [ ] Implement user storage quotas and automated cache cleanup policies.
- [ ] Build Institutional Admin Dashboard (system resource monitor, queue stats, storage usage).
- [ ] Implement database migrations (SQLite dev -> PostgreSQL campus deployment).
- [ ] Write comprehensive BMSIT technical club handover documentation.

---

### 🟡 Phase 9 — Hackathon Presentation & Demonstration Package
- [ ] Create benchmark evaluation report (render speed, CPU usage, quality metrics).
- [ ] Prepare interactive demo showcase project with sample high-definition footage.
- [ ] Produce architecture diagrams, cost comparison analysis ($0 vs cloud APIs), and pitch slide assets.
