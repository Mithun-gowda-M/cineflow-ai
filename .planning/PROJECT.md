# PROJECT: CINEFLOW AI

> **Tagline:** Your AI. Your Story. Your Cinema.  
> **Status:** Phase 0 Architecture & Research Complete  
> **Target:** National & International Hackathon Winner / Permanent BMSIT Institutional Software Product

---

## 1. Executive Summary & Vision

**CINEFLOW AI** is an intelligent AI video director and production studio designed to democratize high-end cinematic filmmaking. Users upload 20–30+ raw video clips and photos, provide creative voice or text instructions (e.g., *"Craft a fast-paced, emotional two-minute college cultural fest montage synchronized to beat drops with warm golden-hour color grading"*), and receive a rendered, broadcast-quality MP4 accompanied by an interactive multi-track editing timeline.

### Non-Negotiable Core Tenets
1. **No Paid Subscriptions or Mandatory Cloud APIs:** Built on 100% free and open-source software (FFmpeg, PySceneDetect, OpenCV, Librosa, Whisper, Ollama). No OpenAI, Runway, or Midjourney billing meters.
2. **Hardware Adaptive:** Operates seamlessly across low-spec student laptops (CPU proxy pipeline) to high-spec multi-core GPU rigs.
3. **No Fake Dashboards:** Every button, timeline cut, audio ducking control, and export trigger executes real computational media pipelines.
4. **Clean Handover to BMSIT Club:** Engineered with institutional code hygiene, modular interfaces, comprehensive docs, and zero proprietary lock-in.

---

## 2. Stakeholders & Constraints

- **Lead Architect / Founder:** Single primary developer transitioning to BMSIT technical club maintainers.
- **Target Audience:** BMSIT engineering students, media club storytellers, hackathon jurors, indie filmmakers.
- **Budget Constraint:** ₹0 recurring subscriptions. Maximum one-time hardware/domain budget of ₹5,000 only when strictly justified.
- **Operating System Environment:** Primary development on Windows 11; deployment targets Windows, Linux (Docker/bare-metal), and macOS.

---

## 3. Design System & User Experience

### 3.1 Visual Language
- **Base Background:** Deep Obsidian Charcoal (`#0B0D13` / `#11141E`)
- **Surface Elevation:** Translucent Dark Glass (`rgba(22, 27, 39, 0.75)` with 16px blur)
- **Primary Accent:** Champagne Gold (`#E5B869` / `#D4A24E`)
- **Secondary Accent:** Electric Cyan Accent (`#38BDF8`) for timeline active playhead & highlights
- **Semantic Signals:** Emerald (`#10B981`) for completed renders, Amber (`#F59E0B`) for warnings, Crimson (`#EF4444`) for errors
- **Typography:** Inter / SF Pro Display for clean UI metrics, Cinzel / Syne for cinematic headlines

### 3.2 Key Application Surfaces
1. **Cinematic Landing Page:** Immediate emotional pull ("Your Footage Deserves a Director"), interactive product preview, feature walkthrough, live workflow simulation.
2. **Student Dashboard & Project Hub:** Quick project setup, storage quota meter, recent edits, preset library.
3. **Media Upload & Inspection Hub:** Drag-and-drop batch uploader (20–30+ files), real-time metadata extraction, thumbnail strip, quality badges.
4. **AI Director Command Center:** Prompt input, style tone selectors (Festive, Documentary, High-Energy Reel, Travelogue), duration targets, music selection.
5. **Multi-Track Professional Editor:**
   - Left: Media Pool & Tagged Asset Inspector
   - Center: Real-time Video Canvas Preview with scrubbing controls
   - Right: Conversational AI Director Assistant & Inspector
   - Bottom: Zoomable Multi-track Timeline (Video V1/V2, Audio A1/A2, Subtitles/Text T1, Overlays)
6. **Export & Delivery Center:** Aspect ratio toggles (9:16 Shorts/Reels, 16:9 Landscape, 1:1 Square), bitrate selectors, resolution up to 4K, proxy toggle.
7. **Institutional Admin Dashboard:** Club management, user quotas, rendering queue metrics, system diagnostics.

---

## 4. Technical Architecture & Component Breakdown

### 4.1 Frontend (`apps/web`)
- **Framework:** Next.js 15 (React 19, TypeScript)
- **Styling:** Tailwind CSS + Custom CSS Variables for the Champagne-Gold / Obsidian palette
- **State Management:** Zustand for timeline state, playback synchronization, and active project memory
- **Timeline Engine:** Canvas + HTML5 Video synchronized playback with virtualized tracks

### 4.2 Backend Gateway (`backend/api`)
- **Framework:** Python 3.12 + FastAPI with asynchronous worker endpoints
- **Data Validation:** Pydantic v2 schemas for all timeline events, media metadata, and export jobs
- **Security:** CSRF protection, file extension and MIME-type validation, path traversal defense, strictly parameterized FFmpeg execution (preventing shell injection)

### 4.3 Media Analysis Engine (`backend/media_analysis`)
- **PySceneDetect:** Content-aware boundary detection (`ContentDetector`, `AdaptiveDetector`)
- **OpenCV:** Laplacian variance blur detection, histogram luminosity analysis, color palette extraction, aspect ratio classification
- **Scoring Pipeline:** Multi-factor scoring (Sharpness 30%, Exposure 25%, Motion Stability 25%, Audio Clarity 20%)

### 4.4 AI Director Engine (`backend/ai_director`)
- **Primary LLM:** Local Ollama (`llama3.2:3b` or `mistral:7b`) with structured JSON schema output
- **Resilient Fallback:** Algorithmic Rule Director that constructs a balanced storyboard (Opening hook -> Rising action -> Climax -> Resolution) even when Ollama is offline
- **Output:** Validated `TimelinePlan` JSON specifying clip in/out points, transitions, speeds, color LUTs, and audio ducking

### 4.5 Audio Intelligence Engine (`backend/audio_engine`)
- **Librosa:** Beat tracking (`librosa.beat.beat_track`), onset strength envelope detection, tempo (BPM) estimation
- **Cut Synchronization:** Aligns video cut points precisely to musical downbeats and energy peaks
- **Whisper.cpp / faster-whisper:** Local speech transcription with word-level timestamps for dynamic subtitle animation

### 4.6 Video Rendering Engine (`backend/video_engine` & `backend/rendering`)
- **FFmpeg 6/7:** Filtergraph generation (`xfade`, `scale`, `eq`, `colorchannelmixer`, `amix`, `loudnorm`)
- **Hardware Acceleration:** Auto-detection of NVENC (`h264_nvenc`), Intel QSV (`h264_qsv`), AMD AMF (`h264_amf`), with standard CPU `libx264` fallback
- **Proxy Pipeline:** Generates lightweight 720p 30fps fast-start proxies for instant in-browser timeline scrubbing

---

## 5. Security & Privacy Commitments
1. **Zero Cloud Leaks:** All footage stays on the student's machine or self-hosted campus server.
2. **No Shell Injections:** All media processing tools run through validated Python argument lists (`subprocess.run(["ffmpeg", "-i", ...])`), never raw unescaped shell strings.
3. **Storage Quotas:** Automatic file expiry and size caps to safeguard local disk space.
4. **Clean Git:** Strictly zero credentials, keys, or raw media in Git history.

