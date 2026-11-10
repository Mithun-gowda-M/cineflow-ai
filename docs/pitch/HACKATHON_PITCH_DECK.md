# CINEFLOW AI — Hackathon Pitch Deck & Live Demo Script

> **Tagline:** *Your AI. Your Story. Your Cinema.*  
> **Target Audience:** Hackathon Jury, Institutional Sponsors, BMSIT Faculty & Technical Club Leads

---

## 1. 10-Slide Deck Outline & Speaker Notes

### Slide 1 — Title & Hook
- **Visual:** CINEFLOW AI Studio hero screenshot (Midnight Obsidian `#0B0D13` + Champagne Gold `#E5B869`).
- **Hook:** *"College clubs shoot 30+ raw clips at every fest — and then spend 12 hours trimming footage or hitting SaaS paywalls. Meet CINEFLOW AI: an AI video director and NLE studio that runs 100% locally for ₹0."*

### Slide 2 — The Problem
- Existing proprietary cloud editors lock students behind \$20–\$60/month paywalls, watermarks, upload queues, and privacy leaks of campus footage.
- Black-box "prompt-to-video" generators invent fake pixels instead of editing the student's **authentic memories**, and never allow frame-level timeline fixes.

### Slide 3 — Our Solution: Director + Interactive Multi-Track Studio
- Drop 20–30+ raw clips -> computer vision scores quality & cuts -> Librosa maps musical beats -> AI Director drafts a validated **4-act multi-track `TimelinePlan`** -> students tweak visually OR conversationally before exporting native H.264 MP4s.

### Slide 4 — Architectural Innovation: Zero-Failure Dual-Mode AI Director
- **Online-with-Ollama:** `llama3.2` emits structured storyboard JSON.
- **Zero-Failure Fallback:** When offline or at low-spec hackathon booths, our deterministic Algorithmic Sequencer enforces balanced narrative arcs (Hook -> Rising -> Climax -> Finale), enforces zero duplicate footage unless requested, and supports iterative Undo/Redo (`Ctrl+Z`).

### Slide 5 — Computer Vision & Beat-Synced Audio Intelligence
- **PySceneDetect + OpenCV:** Laplacian variance sharpness scoring (`>100` sharp vs blurred detection), exposure/luminance histograms, perceptual dHash deduplication, and semantic tagging.
- **Librosa + `faster-whisper`:** Beat grid extraction (`4.24x` realtime measured) and CPU INT8 local speech subtitles burned cleanly via FFmpeg `.ass` filters with automatic music sidechain ducking.

### Slide 6 — Rendering Performance & SHA-256 Partial Segment Caching
- Measured live on a standard 16-core, 15.7 GB RAM Windows laptop (`h264_qsv`):
  - **4 Full-HD clips ingested -> 720p scrub proxies:** `4.315 s`.
  - **Cold 1080p multi-clip MP4 render:** `19.401 s`.
  - **Warm Partial Re-Render (`SegmentCache`):** `7.633 s` (**`60.7%` faster** when tweaking one clip, reusing untouched segments via SHA-256 fingerprints!).
  - **Portrait 9:16 (1080×1920) Reel Export:** `2.311 s` (`1.51x` realtime).

### Slide 7 — Copyright-Safe Trend Style Recipes
- Reference style extraction measures **purely mathematical editing features** (cuts/min, optical motion velocity, dominant color palette, speed-ramp cadence) — SSRF-guarded (`127.0.0.1` / `169.254.169.254` blocked) and deletes ephemeral reference uploads immediately after extraction.

### Slide 8 — Institutional Campus Deployment & Security (BMSIT Ready)
- Salted `hashlib.scrypt` auth + HS256 JWT RBAC (`student`, `club_lead`, `admin`).
- Per-student disk quota enforcement (HTTP `413` protection), startup & manual TTL cache pruning (`psutil` live Admin monitor), SQLite dev -> PostgreSQL 15+ migration scripts, and strict `shell=False` FFmpeg invocation.

### Slide 9 — Unit Economics (\$0 vs Cloud SaaS)
- Solo creator saves **~\$540/yr**; 50-member BMSIT Technical & Media Club saves **~\$27,000/yr** with zero cloud lock-in, full offline operation, and institutional data sovereignty.

### Slide 10 — Live Proof & Handover Roadmap
- **Verification Status:** Automated backend security/unit/integration/render test suites + TypeScript Next.js 15 build + live `/showcase` demo ready right now on localhost.

---

## 2. 3-Minute Live Jury Demo Choreography

| Time Window | Action on Screen | Proof Highlighted to Judges |
| :--- | :--- | :--- |
| **0:00 – 0:40** | Open `/showcase` -> show real host metrics & TCO slider (`50` club students = `\$0/yr`). | Proves zero fake numbers (measured from `BENCHMARK_REPORT.json`). |
| **0:40 – 1:25** | Click **Launch Live HD Showcase** -> `/editor?projectId=proj_bmsit_showcase_2026`. Inspect PySceneDetect scene splits, OpenCV quality scores, and 120 BPM waveform. | Shows real local Full-HD proxy playback and multi-track timeline hydration. |
| **1:25 – 2:10** | Type/speak conversational command: `"Switch to golden hour and tighten intro 1 second"` -> press **Ctrl+Z Undo** -> apply **9:16 Rapid Hook Reel** Style Recipe. | Shows real deterministic timeline diffing, Undo/Redo persistence, and style transfer. |
| **2:10 – 2:45** | Click **Export MP4** -> download real H.264/AAC MP4; show warm partial-cache segment hits (`2/3 cached`). | Proves real FFmpeg rendering + 60.7% partial cache speedup. |
| **2:45 – 3:00** | Briefly open `/admin` (`media.club@bmsit.in`) showing live `psutil` CPU/RAM, quota adjustment, and Postgres migration status. | Proves production institutional campus readiness for BMSIT handover. |

---

## 3. Jury Q&A Rapid Defense Sheet

- **Q: What happens if Ollama isn't running or the venue Wi-Fi drops?**  
  *A:* Every pipeline runs 100% locally with zero internet dependency. Even without Ollama, our Rule-Based 4-Act Director generates balanced, conflict-free timelines deterministically.
- **Q: Does Style Recipe trend analysis scrape YouTube or steal copyrighted video?**  
  *A:* Strictly no. URLs undergo SSRF/private-IP validation with zero media downloading (`media_downloaded=false`), and local reference uploads are ephemerally analyzed for pure math vectors (cuts/min, motion score, palette hexes) and immediately deleted (`raw_frames_retained=false`).
- **Q: How do you prevent students from blowing up disk space or injecting shell commands via filenames?**  
  *A:* Every uploaded filename is sanitized, MIME magic-byte verified, and quota-checked (`413`) before hitting disk; all FFmpeg calls run via validated argument lists (`shell=False`), never unescaped shell strings.

