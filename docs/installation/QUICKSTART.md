# CINEFLOW AI — 3-Minute Quickstart & Judge Demo Guide

> **Prerequisites:** Python 3.12+, Node.js 20+, and `ffmpeg`/`ffprobe` on PATH (or pre-configured in `backend/.venv`).

---

## 1. Local Development Startup (Two Terminals)

### Terminal 1 — FastAPI Backend Gateway
```powershell
cd "c:\Users\mithu\ai video editing"
backend\.venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload
```
Verify backend health at `http://127.0.0.1:8000/api/v1/health`.

### Terminal 2 — Next.js 15 Studio Frontend
```powershell
cd "c:\Users\mithu\ai video editing"
npm --prefix apps/web run dev
```
Open **`http://127.0.0.1:3000`** in your browser.

---

## 2. Optional Local AI Enhancements (100% Free)
- **Ollama LLM Director (optional):** Install Ollama and run `ollama pull llama3.2`. When stopped or offline, CINEFLOW AI automatically runs its deterministic 4-Act Algorithmic Director with zero interruptions.
- **Local Voice Commands (`faster-whisper`):** Installed inside `backend/.venv` (`tiny` CPU INT8 model). Works offline once the Whisper weights are cached locally.

---

## 3. Instant Hackathon Jury Demo Walkthrough
1. Visit **`/showcase`** (Hackathon Presentation Hub) to view real host benchmarks, the interactive **\$0 vs Cloud SaaS TCO Calculator**, architecture diagrams, and slide deck.
2. Click **"Load Live HD Showcase Project"** (on `/showcase` or `/dashboard`) — this executes `POST /api/v1/showcase/load`, ingests the committed Full-HD sample clips + 120 BPM WAV audio from [`assets/sample_media/`](file:///c:/Users/mithu/ai%20video%20editing/assets/sample_media) through FFprobe, PySceneDetect, OpenCV, and Librosa, and opens **`/editor?projectId=proj_bmsit_showcase_2026`**.
3. Inside `/editor`:
   - Scrub real 720p proxy playback across the 4-clip BMSIT showcase sequence.
   - Try a **Conversational Edit** (e.g., `"Switch to moody dark grading"`, `"Trim clip 2 by 1 second"`) and test **Undo (`Ctrl+Z`) / Redo (`Ctrl+Y`)**.
   - Open **Style Recipes**, apply **BMSIT Cultural Aftermovie** or **9:16 Rapid Hook Reel**, or click **Beat-Sync** to snap clip bounds to musical beats.
   - Click **Export MP4** -> watch real FFmpeg rendering complete with SHA-256 partial segment caching and download the real MP4!
4. Visit **`/admin`** and sign in with demo Club Admin credentials on `/auth/login` (`media.club@bmsit.in` / `bmsit2026admin`) to inspect live `psutil` CPU/RAM metrics, manage user quotas, trigger disk cache cleanup, and check PostgreSQL migration readiness.

