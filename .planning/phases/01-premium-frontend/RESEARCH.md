# PHASE 1 RESEARCH: Premium Frontend Design System & Workspaces

> **Phase:** 01 — Premium Frontend  
> **Target:** International-Grade Dark Cinematic Web Application  
> **Status:** Research Complete

---

## 1. Design System & Visual Philosophy

### 1.1 Palette & Tokens
CINEFLOW AI requires an original, high-end cinematic visual identity that differentiates it completely from generic dashboards or Tailwind templates:

- **Midnight Obsidian (Background 0):** `#0B0D13` (Deep, luxurious, zero eye-fatigue)
- **Charcoal Surface (Background 1):** `#11141E` (Panel backgrounds, editor drawers)
- **Elevated Glass (Background 2):** `rgba(22, 27, 39, 0.75)` with `backdrop-filter: blur(16px)` and subtle `1px solid rgba(229, 184, 105, 0.12)` borders
- **Champagne Gold (Brand Primary):**
  - Highlight: `#F5D485`
  - Core: `#E5B869`
  - Deep Bronze: `#B38634`
- **Electric Cyan (Timeline & Metrics Accent):** `#38BDF8` (Active playhead, sync markers, wave peaks)
- **Film Lavender (AI Director Accent):** `#A78BFA` (AI suggestions, prompt chips)
- **Status Accents:**
  - Success / Render Ready: Emerald `#10B981`
  - Processing / Beat Sync: Amber `#F59E0B`
  - Error / Invalid Format: Crimson `#EF4444`

### 1.2 Typography
- **Headlines & Cinematic Statements:** Syne / Cinzel font-family fallback with tracked uppercase styling (`tracking-wider`).
- **UI Metrics, Labels & Timecodes:** Inter / JetBrains Mono for monospaced timestamps (`00:01:24:12`) and timeline markers.

---

## 2. Key Screen Workspaces Architecture

### 2.1 Screen 1: Cinematic Landing Page (`/`)
- **Hero Section:**
  - Headline: *"Your Footage Deserves a Director."*
  - Subtitle: *"Transform raw moments into cinematic stories with intelligent AI editing."*
  - Primary CTA: *"Launch CINEFLOW Studio"* (Direct route to `/editor`)
  - Secondary CTA: *"Explore Sample Projects"* (Loads interactive demo reel)
- **Interactive Product Simulation:**
  - A real-time visual simulation showing raw clips snapping to beat drops, color grade transitioning from flat to Golden Hour, and timeline tracks populating live.
- **Workflow Stepper:**
  1. Ingest Raw Footage (20-30+ clips)
  2. Natural Language Creative Direction
  3. AI Scene Detection & Quality Ranking
  4. Audio Beat Synchronization
  5. Multi-Track Preview & 4K MP4 Export
- **Institutional & Hackathon Trust Banner:** BMSIT permanent project, 100% open-source, zero recurring subscription cost.

### 2.2 Screen 2: Student Dashboard (`/dashboard`)
- **Metrics Bar:** Total Projects, Storage Quota (e.g. `4.2 GB / 20 GB used`), Renders Completed.
- **New Project Quick Creator Modal:** Name, aspect ratio (16:9, 9:16, 1:1, 21:9), target duration (30s, 60s, 120s, Custom), director style preset.
- **Project Grid:** Recent projects with live video/image thumbnails, duration badges, aspect ratio tags, and direct actions (Open in Editor, Duplicate, Export).

### 2.3 Screen 3: Multi-Track Video Editor (`/editor`)
This is the flagship core of CINEFLOW AI:
- **Top Command Bar:**
  - Project Title & Auto-Save status
  - Aspect Ratio Selector (16:9 Landscape, 9:16 Shorts/Reels, 1:1 Square, 21:9 Anamorphic)
  - Timecode display (`00:00:00:00` / Current & Total)
  - Undo (`Ctrl+Z`) and Redo (`Ctrl+Y`) with state stack
  - Export Button (`Export Video`) triggering full render modal
- **Left Media Library:**
  - Tab 1: Uploaded Clips (drag-and-drop or file selector, with duration, resolution, quality score badges)
  - Tab 2: AI Detected Scenes (PySceneDetect split subclips)
  - Tab 3: B-Roll & Visual Assets
  - Tab 4: Licensed Audio & Sound Effects
- **Center Canvas Preview:**
  - HTML5 Video Player + Overlay Canvas
  - Real-time scrubbing with responsive time tracking
  - Live Color Grading simulation via CSS/WebGL filters (Teal & Orange, Golden Hour, Moody Dark)
  - Play, Pause, Jump 1s Forward/Back, Frame Step, Fullscreen
  - Aspect Ratio viewport mask (letterboxing / pillarboxing)
- **Right AI Director Drawer:**
  - Conversational AI Prompt Box: *"Make the ending more dramatic and speed up the fireworks"*
  - Voice Command Microphone simulator
  - Style Presets: Deepavali Festive, Cinematic Travel, High-Energy Reel, Documentary, Wedding Film
  - Clip Inspector: Selected clip in/out trim handles, playback speed slider (0.25x to 4x), volume, transition picker
- **Bottom Multi-Track Timeline:**
  - Zoomable timeline ruler (0s to 120s+) with draggable playhead
  - Track 1 (V1 - Main Video): Snappable clip blocks with thumbnail previews
  - Track 2 (V2 - B-Roll / Overlays): Cutaways and secondary media
  - Track 3 (A1 - Dialogue / Voice): Audio waveform display
  - Track 4 (A2 - Soundtrack / Music): Audio waveform with beat-grid markers
  - Track 5 (T1 - Animated Subtitles / Typography): Subtitle cues
  - Track controls: Mute, Solo, Lock per track

### 2.4 Screen 4: Media Upload & Quality Workspace (`/upload`)
- Multi-file dropzone supporting 20-30+ files simultaneously
- Immediate client-side probe (file size, resolution, duration)
- Quality score preview cards with blur/sharpness metrics and semantic tags

### 2.5 Screen 5: Campus Admin & Health Dashboard (`/admin`)
- Real-time system monitoring: CPU usage, memory, disk storage
- Active rendering queue monitor
- Student user management and storage quota configuration

---

## 3. Technology Stack & Dependencies

- **Framework:** Next.js 15 (App Router) + React 19 + TypeScript
- **Styling:** Tailwind CSS with customized cinematic theme tokens
- **Icons:** `lucide-react` (Camera, Film, Sparkles, Sliders, Play, Volume2, Mic, Scissors, Layers, CheckCircle, Download, etc.)
- **State Management:** Pure React state + custom Timeline context / store supporting undo/redo history stacks and real-time playback synchronization.
