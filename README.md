# CINEFLOW AI 🎬✨
> **Your AI. Your Story. Your Cinema.**  
> *Transform raw footage and photos into festival-worthy cinematic stories with an intelligent, local-first AI Video Director.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows | Linux | macOS](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue.svg)](#)
[![Zero Cloud Subscriptions](https://img.shields.io/badge/Cost-Zero%20Paid%20APIs-brightgreen.svg)](#)
[![Institution: BMSIT](https://img.shields.io/badge/Developed%20for-BMSIT%20%26%20Global%20Hackathons-gold.svg)](#)

---

## 📽️ Product Overview

**CINEFLOW AI** is a professional-grade, local-first AI video production platform designed for filmmakers, content creators, student storytellers, and hackathon competitors. Users upload raw video clips and photos, provide creative voice or text instructions (e.g. *"Create a high-energy two-minute college festival recap synchronized with electronic music and warm golden-hour grading"*), and receive a rendered MP4 with full multi-track timeline control.

### Why CINEFLOW AI?
- **Zero Recurring Costs:** Runs entirely on free and open-source technologies (FFmpeg, PySceneDetect, OpenCV, Librosa, Whisper, and Ollama). No mandatory paid APIs or cloud GPU rental.
- **Hardware-Adaptive:** Runs on ordinary laptops (CPU-first profile) up to high-end workstations with hardware acceleration.
- **True Multi-Track Timeline:** Not a black-box renderer; outputs a full, editable timeline with video tracks, B-roll, subtitles, and audio layers.
- **Conversational Editing:** Ask the AI Director to tweak cuts, replace scenes, alter pacing, or apply color grades naturally.
- **Institutional & Hackathon Ready:** Built with a clean monorepo architecture, role-based student access, security isolation, and thorough documentation for club handover.

---

## 🏛️ System Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │               CLIENT LAYER                   │
                    │   Next.js 15 / React / Tailwind / Lucide    │
                    │   Dark Cinematic UI & Multi-Track Canvas     │
                    └──────────────────────┬───────────────────────┘
                                           │ REST / WebSocket
                    ┌──────────────────────▼───────────────────────┐
                    │            API GATEWAY & BACKEND             │
                    │        FastAPI (Python 3.12, Async)          │
                    └──────┬──────────────┬───────────────┬────────┘
                           │              │               │
        ┌──────────────────┴──┐    ┌──────┴──────┐    ┌───┴────────────────┐
        │   AI DIRECTOR CORE  │    │ MEDIA ENGINE│    │   AUDIO ENGINE     │
        │ - Natural NLP Plan  │    │ - FFmpeg/CV │    │ - Librosa Beats    │
        │ - Ollama / Heuristic│    │ - Scenes    │    │ - Whisper Subtitles│
        │ - Timeline JSON Gen │    │ - Scoring   │    │ - Ducking & Sync   │
        └──────────┬──────────┘    └──────┬──────┘    └───┬────────────────┘
                   │                      │               │
                   └──────────────────────┼───────────────┘
                                          │
                    ┌─────────────────────▼────────────────────────┐
                    │              RENDERING PIPELINE              │
                    │    Native FFmpeg Filtergraphs / HW Accel    │
                    │        Real MP4 Export (1080p / 4K)          │
                    └──────────────────────────────────────────────┘
```

---

## 💻 Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS, Lucide Icons, Framer Motion |
| **Backend** | Python 3.12, FastAPI, Pydantic v2, Uvicorn, SQLite / PostgreSQL |
| **Video Engine** | FFmpeg, FFprobe, OpenCV (`opencv-python-headless`), PySceneDetect |
| **Audio Engine** | Librosa, SoundFile, Whisper.cpp / `faster-whisper` |
| **AI Director** | Ollama local open weights (`llama3.2`, `mistral`) + Smart Rule Fallback Engine |
| **Design System** | Midnight charcoal `#0B0D13`, deep obsidian `#11141E`, champagne gold `#E5B869` |

---

## 📁 Repository Structure

```
cineflow-ai/
├── apps/
│   ├── web/                     # Next.js 15 premium frontend interface
│   └── local-agent/             # Desktop pairing / hardware bridge
├── backend/
│   ├── api/                     # FastAPI routing and endpoints
│   ├── authentication/          # User auth, JWT, student role control
│   ├── ai_director/             # Storyboard & timeline planner
│   ├── media_analysis/          # CV quality scoring, blur & scene detection
│   ├── trend_intelligence/      # Creative style recipe analyzer
│   ├── video_engine/            # FFmpeg filtergraph builder & transitions
│   ├── audio_engine/            # Librosa beat detection & Whisper sync
│   ├── rendering/               # Export pipeline & proxy generator
│   └── job_manager/             # Async task queue & background progress
├── packages/
│   ├── shared_types/            # Shared TypeScript/JSON interfaces
│   ├── editing_presets/         # Cinematic LUTs, aspect ratios, motion curves
│   └── design_system/           # Reusable UI tokens, themes, components
├── docs/                        # Architecture, licenses, guides
├── assets/                      # Sample clips, sound effects, typography
├── tests/                       # Unit, integration, rendering & security tests
└── .planning/                   # GSD specification, roadmap, requirements
```

---

## 🚀 Quick Start (Development)

### Prerequisites
- **Node.js** v20+ / v24+
- **Python** 3.11+ / 3.12+
- **FFmpeg** installed and accessible in PATH (or configured in `.env`)

### Setup Backend
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

### Setup Frontend
```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to launch the CINEFLOW AI interface.

---

## 🎓 Handover & Institutional Maintenance
Developed for **BMSIT** student innovators, media clubs, and competitive hackathon teams. For deployment guidelines, see `docs/deployment/DEPLOYMENT.md`.

Distributed under the **MIT License**.
