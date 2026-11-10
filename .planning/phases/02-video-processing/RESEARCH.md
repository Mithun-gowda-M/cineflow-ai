# PHASE 2 RESEARCH: Real Video Processing & Rendering Engine

> **Phase:** 02 — Real Video Processing  
> **Target:** Deterministic FFmpeg/FFprobe Backend Pipeline & API Gateway  
> **Status:** Research Complete

---

## 1. Environment & Binary Discovery Findings

Inspection of the Windows 11 development environment (Phase 0 / Phase 2 Check):
- **Python Runtime:** `Python 3.12.10` (`C:\Users\mithu\AppData\Local\Programs\Python\Python312\python.exe`), `pip 25.0.1`
- **Pre-installed Libraries:** `numpy 2.5.4`, `scipy 1.18.1`, `pillow 12.3.0`, `requests 2.34.2`, `scikit-image 0.26.0`
- **Packages to Install (`backend/requirements.txt`):** `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `python-multipart`, `aiofiles`, `httpx`, `python-dotenv`, `pytest`, `pytest-asyncio`
- **FFmpeg & FFprobe Status:** Not currently present in system `PATH`. Package managers `winget.exe` and `choco.exe` are available on the host.
  - **Resolution:** Install `Gyan.FFmpeg` via `winget` (provides full `ffmpeg.exe` and `ffprobe.exe` binaries) and build a resilient binary locator (`backend/video_engine/ffmpeg_runner.py`) that resolves binaries in order:
    1. `.env` (`FFMPEG_PATH` / `FFPROBE_PATH`)
    2. System `PATH` (`shutil.which`)
    3. Common Windows WinGet / Chocolatey install directories (`%LOCALAPPDATA%\Microsoft\WinGet\Packages`)

---

## 2. Heterogeneous Media Normalization Strategy

Real user footage from smartphones, DSLRs, and screen recordings (20–30+ mixed videos and photos) varies wildly in resolution, frame rate, orientation, SAR/DAR, pixel format, and audio presence. Direct `concat` demuxing fails on mixed streams.

### Solution: Per-Input Filter Normalization
Every timeline clip input `[i:v]` and `[i:a]` is normalized before transition/concatenation:
1. **Still Images (`jpg`, `png`, `webp`):** Looped for `clip.duration` seconds at `30 fps` (`-loop 1 -t <dur>`), optionally with subtle Ken Burns zoom/pan or clean fit.
2. **Aspect Ratio Conforming:** Target dimensions mapped cleanly:
   - `16:9` → `1920x1080` (or `1280x720` in Low profile)
   - `9:16` → `1080x1920` (or `720x1280`)
   - `1:1` → `1080x1080` (or `720x720`)
   - `4:5` → `1080x1350`
   - `21:9` → `2560x1080`
   - Filter chain per video stream:
     `scale=W:H:force_original_aspect_ratio=decrease,pad=W:H:(ow-iw)/2:(oh-ih)/2:color=#0B0D13,setsar=1,fps=30,format=yuv420p`
3. **Speed Ramping:** Video PTS adjusted via `setpts=(PTS-STARTPTS)/<speed>`; Audio tempo adjusted via chained `atempo` filters (clamped to `[0.5, 2.0]` per stage to satisfy FFmpeg's `atempo` filter bounds).
4. **Missing Audio Safety:** Using FFprobe results, clips lacking an audio stream receive a generated silent PCM stream via `anullsrc=channel_layout=stereo:sample_rate=48000` inside the filtergraph so `acrossfade`/`amix` never fail.

---

## 3. Transition & Color Grading Filtergraph Design

### 3.1 Transitions (`xfade` & `acrossfade`)
When chaining clip $k$ and clip $k+1$ with overlap duration $d$ (clamped safely to `< min(dur_k, dur_{k+1}) / 2`):
- Accumulated timeline offset: `offset_k = sum(durations_0..k) - sum(overlaps_0..k)`
- Supported FFmpeg `xfade` mappings:
  - `crossfade` → `xfade=transition=fade`
  - `wipe_left` / `wipe_right` → `xfade=transition=wipeleft` / `wiperight`
  - `slide_left` / `slide_right` → `xfade=transition=slideleft` / `slideright`
  - `zoom_in` / `zoom_out` → `xfade=transition=circleopen` / `radial`
  - `fade_from_black` / `fade_to_black` → `fade=t=in` / `fade=t=out`
- When transition is `none` or `duration == 0`, uses zero-overlap `fade` with `d=0.01` or `concat=n=2:v=1:a=1` cleanly.

### 3.2 Color Grading Presets
Implemented with native FFmpeg `eq` and `colorbalance` filters (zero external LUT `.cube` file dependency required):
- `natural`: Passthrough
- `golden_hour`: Warm highlights/midtones (`colorbalance=rs=0.08:gs=0.02:bs=-0.08:rm=0.06:bm=-0.06`, `eq=saturation=1.22:contrast=1.08:brightness=0.02`)
- `cinematic_teal_orange`: Cool shadows, warm highlights (`colorbalance=rs=-0.10:gs=0.02:bs=0.12:rh=0.10:gh=0.02:bh=-0.10`, `eq=contrast=1.18:saturation=1.15`)
- `moody_dark`: Desaturated shadows (`eq=contrast=1.20:saturation=0.78:brightness=-0.06`)
- `vintage_film`: Warm lifted blacks (`eq=contrast=0.95:saturation=0.82:gamma=1.05`, `colorbalance=rs=0.06:gs=0.03:bs=-0.05`)
- `high_contrast_bw`: Monochrome (`hue=s=0`, `eq=contrast=1.28`)

---

## 4. Security & Input Validation Controls

- **Subprocess Safety:** Zero `shell=True`. Every `ffmpeg` and `ffprobe` call invokes `subprocess.run` / `asyncio.create_subprocess_exec` with explicit `list[str]` arguments.
- **Upload Validation:**
  - Extension whitelist (`mp4`, `mov`, `mkv`, `webm`, `avi`, `jpg`, `jpeg`, `png`, `webp`, `mp3`, `wav`, `aac`, `flac`, `m4a`).
  - Magic-byte header signature verification (`ftyp`, `RIFF`, `\x1A\x45\xDF\xA3`, `\xFF\xD8\xFF`, `\x89PNG`, `ID3`, `fLaC`) to block spoofed files.
  - Internal storage uses strict UUID filenames (`media_<uuid>.<ext>`), preventing directory traversal (`../`) and filename filtergraph injection.
- **Progress Tracking & Cancellation:** Pass `-progress pipe:1 -nostats` to FFmpeg and parse `out_time_us` against total expected timeline duration to stream accurate percentages (`0–100%`) and support safe process termination on job cancellation.

