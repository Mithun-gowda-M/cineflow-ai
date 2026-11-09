# REQUIREMENTS SPECIFICATION: CINEFLOW AI

> **Status:** Approved Baseline (Phase 0)  
> **Traceability:** Aligned with CINEFLOW Master Specification & GSD Phase Structure

---

## 1. Functional Requirements (FR)

### FR-01: Media Ingestion & Inspection
- **FR-01.1:** System shall accept batch uploads of 20 to 30+ media assets (MP4, MOV, MKV, WebM, JPG, PNG, WebP).
- **FR-01.2:** System shall extract technical metadata via FFprobe (codec, resolution, framerate, duration, bitrate, audio sample rate, channels, rotation/aspect ratio).
- **FR-01.3:** System shall generate fast thumbnail strips and lightweight proxy videos (720p 30fps H.264) for real-time browser preview without high CPU load.
- **FR-01.4:** System shall validate file extensions, MIME signatures, and file size limits (rejecting corrupted or malicious files).

### FR-02: Computer Vision & Media Intelligence
- **FR-02.1:** System shall detect scene cuts and boundaries in video clips using PySceneDetect (`ContentDetector` / `AdaptiveDetector`).
- **FR-02.2:** System shall compute frame sharpness and blur detection using OpenCV Laplacian variance.
- **FR-02.3:** System shall evaluate exposure, contrast, and dominant color palette for every scene.
- **FR-02.4:** System shall assign transparent quality scores (0–100) and semantic tags (e.g., Landscape, Action, Portrait, Low-Light, Diya, Celebration).
- **FR-02.5:** System shall detect and flag duplicate or near-duplicate shots to prevent monotonous edits.

### FR-03: AI Director & Storyboard Generator
- **FR-03.1:** System shall parse natural language editing instructions (e.g. *"Create a 90-second cinematic festive recap with slow dramatic intro and high energy ending"*).
- **FR-03.2:** System shall output a validated, structured `TimelinePlan` JSON specifying scenes, in/out timestamps, transitions, speed ramps, and color grade presets.
- **FR-03.3:** System shall support local Ollama open-weight LLMs (`llama3.2`, `mistral`, `qwen2.5`).
- **FR-03.4:** System shall provide a resilient Rule-Based Director Fallback that constructs professional storyboards when LLMs are offline.
- **FR-03.5:** System shall enforce that footage is not artificially duplicated to meet duration targets unless explicitly requested by the user.

### FR-04: Audio Intelligence & Rhythm Sync
- **FR-04.1:** System shall accept user-provided audio tracks (MP3, WAV, AAC, FLAC) and analyze tempo (BPM) and beat timestamps using Librosa.
- **FR-04.2:** System shall automatically snap video cut points to musical downbeats and energy drops.
- **FR-04.3:** System shall calculate audio energy envelopes and perform automated audio ducking (lowering music during speech/dialogue).
- **FR-04.4:** System shall transcribe spoken audio using local Whisper and produce word-level timestamped subtitle cues.

### FR-05: Cinematic Video Rendering Engine
- **FR-05.1:** System shall construct parameterized FFmpeg filtergraphs for video trimming, scaling, padding, and concatenation.
- **FR-05.2:** System shall support cinematic transitions (dissolve, wipe, slide, fade to black/white, zoom).
- **FR-05.3:** System shall apply color grading presets (Cinematic Teal & Orange, Golden Hour, Moody Monochrome, Vintage Film).
- **FR-05.4:** System shall render real, uncorrupted MP4 files (H.264/AAC) playable in standard browsers and media players.
- **FR-05.5:** System shall render multiple aspect ratios: 16:9 (Landscape YouTube), 9:16 (Shorts/Reels), 1:1 (Square), and 21:9 (Anamorphic Cinema).

### FR-06: Interactive Multi-Track Editor (UI/UX)
- **FR-06.1:** Interface shall feature a premium dark cinematic theme with midnight backgrounds (`#0B0D13`) and champagne-gold accents (`#E5B869`).
- **FR-06.2:** System shall render a multi-track timeline displaying Video Tracks (V1, V2), Audio Tracks (A1, A2), and Subtitle/Overlay Tracks (T1).
- **FR-06.3:** Users shall be able to scrub, play/pause, adjust clip boundaries, swap clips, and change transition styles interactively.
- **FR-06.4:** System shall provide real-time preview synchronized with the audio playhead.

### FR-07: Conversational Editing
- **FR-07.1:** Users shall be able to type or speak natural commands into an AI Director chat drawer (e.g. *"Trim the intro by 3 seconds"*, *"Change to golden hour grading"*).
- **FR-07.2:** System shall parse the command, compute timeline diffs, and update the multi-track state with full Undo/Redo support.

### FR-08: Trend Intelligence (Optional / Safe)
- **FR-08.1:** Users may provide reference video URLs or uploads to analyze abstract editing style recipes (cut frequency, motion velocity, color mood).
- **FR-08.2:** System shall strictly forbid scraping private data or downloading copyrighted audio/video; only permissible metadata and user-authorized uploads are processed.

### FR-09: Institutional Platform & Student Access
- **FR-09.1:** System shall support student authentication (JWT/local session) and college domain email recognition.
- **FR-09.2:** System shall enforce storage quotas per user and automatic cleanup of expired render caches.
- **FR-09.3:** System shall provide an institutional Admin Dashboard for club leads to monitor system health, storage, and queue performance.

---

## 2. Non-Functional Requirements (NFR)

### NFR-01: Cost & Open Source Guarantee
- **NFR-01.1:** 100% of core features must function without paid API keys (zero OpenAI, zero ElevenLabs, zero Runway subscription requirements).
- **NFR-01.2:** All third-party libraries must carry permissive open-source licenses (MIT, Apache 2.0, BSD, LGPL v2.1).

### NFR-02: Performance & Hardware Adaptability
- **NFR-02.1:** Low profile mode shall allow real MP4 rendering on standard quad-core CPU laptops with 8GB RAM without memory exhaust.
- **NFR-02.2:** System shall detect and utilize NVENC, QSV, or AMF GPU acceleration when present.
- **NFR-02.3:** In-browser timeline scrubbing shall run at 30+ FPS using generated lightweight proxies.

### NFR-03: Security & Code Safety
- **NFR-03.1:** All FFmpeg/external subprocess calls must use validated argument lists — no raw shell execution (`shell=False`).
- **NFR-03.2:** Strict path sanitization on all uploaded filenames to prevent directory traversal (`../`).
- **NFR-03.3:** Zero secrets, tokens, or raw user footage committed to Git.

### NFR-04: Maintainability & Handover
- **NFR-04.1:** Clean monorepo structure with automated unit tests for timeline schemas, probe parsers, and filtergraph generators.
- **NFR-04.2:** Complete architectural and deployment documentation for BMSIT technical club members.

---

## 3. Acceptance Verification Matrix (Release 1.0 MVP)

| ID | Description | Verification Method |
| :--- | :--- | :--- |
| **V-01** | Multi-file batch upload (20+ files) | Upload test suite with varied resolutions and formats |
| **V-02** | Metadata extraction & proxy generation | Automated unit tests on FFprobe JSON outputs |
| **V-03** | Scene detection & OpenCV quality scoring | PySceneDetect & blur analysis on benchmark video files |
| **V-04** | AI Director JSON timeline generation | Schema validation against Pydantic `TimelinePlan` |
| **V-05** | Real MP4 render & playback | FFmpeg execution producing valid MP4 playable in HTML5 video |
| **V-06** | Dark cinematic UI responsiveness | Lighthouse audit & multi-viewport layout validation |
| **V-07** | Zero external API runtime dependency | Full offline test pass with internet disconnected |

