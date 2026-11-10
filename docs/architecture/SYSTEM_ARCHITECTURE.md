# CINEFLOW AI — System Architecture & Technical Blueprint

> **Architecture Style:** Local-First Monorepo (`apps/web` Next.js 15 + `backend/` Python 3.12 FastAPI)  
> **Core Guarantee:** Zero mandatory paid cloud APIs, strictly parameterized subprocesses (`shell=False`), and deterministic offline fallback across every AI stage.

---

## 1. End-to-End Platform Architecture

```mermaid
flowchart TB
    subgraph Client["Next.js 15 Frontend Studio (apps/web)"]
        UI_HOME["Landing / Showcase Hub<br/>/, /features, /showcase"]
        UI_HUB["Media Hub & Dashboard<br/>/upload, /dashboard"]
        UI_STUDIO["Multi-Track Studio<br/>/editor (?projectId=...)"]
        UI_ADMIN["Institutional Admin<br/>/admin, /auth/*"]
    end

    subgraph Gateway["FastAPI API Gateway (backend/api/main.py — /api/v1)"]
        AUTH["Auth & Quota Guard<br/>scrypt + PyJWT + quotas.py"]
        ROUTERS["REST Routers<br/>media, projects, director, audio,<br/>voice, trends, render, admin, showcase"]
        QUEUE["Async Render Queue<br/>job_manager/queue.py"]
    end

    subgraph Engines["100% Open-Source Local Engines"]
        CV["Media Intelligence<br/>FFprobe + PySceneDetect + OpenCV<br/>720p Proxy + dHash Dedupe"]
        AUDIO["Audio Intelligence<br/>Librosa BPM / Beats / Ducking<br/>faster-whisper (CPU INT8)"]
        DIR["Dual-Mode AI Director<br/>Ollama (llama3.2) OR<br/>Algorithmic 4-Act Sequencer"]
        TREND["Trend Style Analyzer<br/>SSRF Guard + Ephemeral CV<br/>Abstract StyleRecipe Store"]
        RENDER["FFmpeg Rendering Engine<br/>filter_complex + ASS Captions<br/>SHA-256 SegmentCache + qsv/x264"]
    end

    subgraph Storage["Local / Institutional Persistence"]
        DB[("SQLite WAL (Dev)<br/>or PostgreSQL 15+ (Campus)")]
        DISK[("Managed Storage<br/>uploads/, proxies/, renders/,<br/>cache/segments/")]
    end

    UI_HOME & UI_HUB & UI_STUDIO & UI_ADMIN -->|JSON / Multipart / Static| ROUTERS
    ROUTERS --> AUTH
    ROUTERS --> CV & AUDIO & DIR & TREND
    ROUTERS --> QUEUE --> RENDER
    CV & AUDIO & RENDER --> DISK
    ROUTERS & AUTH & QUEUE --> DB
```

---

## 2. Dual-Mode AI Director & Conversational Edit Flow

```mermaid
sequenceDiagram
    actor Student
    participant Studio as Editor Studio (/editor)
    participant API as FastAPI (/director/plan, /director/edit)
    participant Ollama as Local Ollama (llama3.2)
    participant Rule as Deterministic 4-Act Fallback
    participant DB as SQLite/PostgreSQL Revisions
    participant Render as FFmpeg + SegmentCache

    Student->>Studio: Enter prompt or speak voice cue
    Studio->>API: POST /api/v1/director/plan (prompt, aspect_ratio, style_recipe_id)
    API->>Ollama: Check /api/tags & request structured TimelinePlan JSON
    alt Ollama Available & Valid JSON
        Ollama-->>API: Structured storyboard choices
    else Ollama Offline or Invalid Schema
        API->>Rule: Parse intent + score shots -> 4-act sequence (zero clip dupes)
        Rule-->>API: Validated TimelinePlan + StoryboardBeat[]
    end
    API->>DB: Save timeline + push revision snapshot
    API-->>Studio: Hydrate V1/V2/A1/Subtitles tracks

    Student->>Studio: "Make it golden hour and trim intro 2s" (or Undo Ctrl+Z)
    Studio->>API: POST /api/v1/director/edit
    API->>DB: Compute TimelineDiffSummary + persist revision
    Student->>Studio: Export 1080p MP4
    Studio->>API: POST /api/v1/render
    API->>Render: Reuse untouched clips via SHA-256 SegmentCache
    Render-->>Studio: Stream /api/v1/render/{job_id}/download
```

---

## 3. Security, Subprocess Isolation & Campus RBAC Architecture

- **Zero Shell Injection:** Every binary invocation (`ffmpeg`, `ffprobe`) flows through [`ffmpeg_runner.py`](file:///c:/Users/mithu/ai%20video%20editing/backend/video_engine/ffmpeg_runner.py) using argument arrays with `shell=False` and strict path validation.
- **Upload Defense-in-Depth:** [`validator.py`](file:///c:/Users/mithu/ai%20video%20editing/backend/media_analysis/validator.py) enforces path sanitization (`../` stripped), extension allow-lists, and binary magic-byte verification (rejecting renamed payloads).
- **SSRF & Copyright Guard:** [`safety.py`](file:///c:/Users/mithu/ai%20video%20editing/backend/trend_intelligence/safety.py) rejects non-HTTP(S) schemes, credentials in URLs, loopback/private/link-local hosts (`127.0.0.1`, `169.254.169.254`, RFC 1918 subnets), and zero raw copyrighted media is retained after ephemeral feature extraction.
- **Campus Authentication & Quotas:** [`security.py`](file:///c:/Users/mithu/ai%20video%20editing/backend/authentication/security.py) hashes passwords with salted `hashlib.scrypt` and signs HS256 JWTs (`PyJWT`), guarding `/api/v1/auth/*` and `/api/v1/admin/*`, while [`quotas.py`](file:///c:/Users/mithu/ai%20video%20editing/backend/authentication/quotas.py) rejects quota-exceeding uploads with HTTP `413`.

