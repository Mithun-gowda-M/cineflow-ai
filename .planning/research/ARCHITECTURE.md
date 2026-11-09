# CINEFLOW AI — SYSTEM ARCHITECTURE & TECHNICAL SPECIFICATION

> **Document Version:** 1.0.0  
> **Classification:** Core Technical Architecture Document (Phase 0)  
> **Authors:** Principal Software Architect & Systems Engineering Team

---

## 1. High-Level Architecture Overview

CINEFLOW AI is architected as an asynchronous, local-first video production platform with strict separation of concerns:

```
┌────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                              │
│  apps/web (Next.js 15, React 19, TypeScript, Tailwind CSS, Lucide)     │
│  ┌───────────────────────┬───────────────────┬──────────────────────┐  │
│  │     Landing Page      │ Project Dashboard │ Multi-Track Timeline │  │
│  │   & Feature Preview   │ & Media Inspector │ & Real-Time Preview  │  │
│  └───────────────────────┴───────────────────┴──────────────────────┘  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ REST APIs / SSE / WebSockets
┌────────────────────────────────────▼───────────────────────────────────┐
│                           API GATEWAY LAYER                            │
│  backend/api (FastAPI Async, Pydantic v2, CORS, Static Media Mounts)   │
│  ┌───────────────────────┬───────────────────┬──────────────────────┐  │
│  │ Project & Media API   │ AI Director API   │ Export Job API       │  │
│  └───────────────────────┴───────────────────┴──────────────────────┘  │
└──────┬─────────────────────────────┬────────────────────────────┬──────┘
       │                             │                            │
┌──────▼──────────────┐       ┌──────▼──────────────┐      ┌──────▼──────┐
│  AI DIRECTOR ENGINE │       │ MEDIA INTELLIGENCE  │      │AUDIO ENGINE │
│  - Ollama Local LLM │       │ - PySceneDetect     │      │- Librosa    │
│  - Heuristic Engine │       │ - OpenCV Blur/Color │      │- Whisper.cpp│
│  - Storyboard Gen   │       │ - Metadata Probing  │      │- Beat Sync  │
└──────┬──────────────┘       └──────┬──────────────┘      └──────┬──────┘
       │                             │                            │
       └─────────────────────────────┼────────────────────────────┘
                                     │
                      ┌──────────────▼──────────────┐
                      │    FFmpeg RENDER ENGINE     │
                      │ - Filtergraph Assembly      │
                      │ - Color LUTs & Grading      │
                      │ - Transitions & Speed Ramps │
                      │ - Hardware Enc (NVENC/CPU)  │
                      └──────────────┬──────────────┘
                                     │
                      ┌──────────────▼──────────────┐
                      │    LOCAL STORAGE & DATA     │
                      │ - SQLite Database           │
                      │ - Original Media Storage    │
                      │ - 720p Scrubbing Proxies    │
                      │ - Rendered Final MP4s       │
                      └─────────────────────────────┘
```

---

## 2. Core Data Models & Schemas

The heart of CINEFLOW AI is the declarative **Timeline Plan**. Instead of opaque scripts, the AI Director emits a typed JSON structure validated by Pydantic before rendering:

### 2.1 Timeline Schema (`TimelinePlan`)
```json
{
  "version": "1.0",
  "project_id": "proj_bmsit_01",
  "title": "Deepavali Festival Highlights",
  "aspect_ratio": "16:9",
  "target_duration_seconds": 120.0,
  "fps": 30,
  "color_grade": "golden_hour",
  "tracks": {
    "video_tracks": [
      {
        "id": "v1",
        "name": "Main Narrative",
        "clips": [
          {
            "clip_id": "clip_01",
            "source_id": "media_raw_diya_04.mp4",
            "start_time_seconds": 1.2,
            "end_time_seconds": 4.5,
            "timeline_start_seconds": 0.0,
            "playback_speed": 0.8,
            "transition_in": { "type": "fade_from_black", "duration_seconds": 0.8 },
            "transition_out": { "type": "crossfade", "duration_seconds": 0.5 },
            "tags": ["diya", "warm", "opening_hook"]
          }
        ]
      }
    ],
    "audio_tracks": [
      {
        "id": "a1",
        "name": "Soundtrack",
        "source_id": "music_festive_instrumental.mp3",
        "volume": 0.85,
        "ducking": {
          "enabled": true,
          "duck_volume": 0.25,
          "fade_time_seconds": 0.4
        }
      }
    ],
    "subtitle_tracks": [
      {
        "id": "t1",
        "style": "cinematic_gold_bottom",
        "cues": [
          {
            "start_seconds": 1.5,
            "end_seconds": 4.0,
            "text": "A Festival of Lights and Unity"
          }
        ]
      }
    ]
  }
}
```

---

## 3. Hardware-Adaptive Profiles

To guarantee optimal operation on both modest student laptops and high-end workstations, CINEFLOW automatically assigns one of three processing profiles:

| Specification | Low Profile (Entry Laptop) | Medium Profile (Balanced) | High Profile (Workstation) |
| :--- | :--- | :--- | :--- |
| **Target Hardware** | 4 Cores, 8GB RAM, Intel Iris/UHD | 6-8 Cores, 16GB RAM, Entry GPU | 8+ Cores, 32GB RAM, Dedicated GPU |
| **Video Encoder** | `libx264 -preset veryfast` | `libx264 -preset medium` or QSV | `h264_nvenc` / `h264_amf` (GPU) |
| **Proxy Resolution** | 540p 24fps | 720p 30fps | 1080p 30fps |
| **PySceneDetect Mode** | Downscaled 360p, 4 fps skip | Downscaled 480p, 2 fps skip | Native 720p frame analysis |
| **Whisper Model** | `tiny.en` / `base` (INT8 quantized) | `base` / `small` (INT8 quantized) | `small` / `medium` |
| **Ollama Model** | `llama3.2:1b` or Heuristic Fallback | `llama3.2:3b` | `mistral:7b` / `llama3.1:8b` |
| **Concurrent Jobs** | 1 render at a time | 2 concurrent renders | 4 concurrent renders |

---

## 4. Audio-Visual Beat Synchronization Pipeline

1. **Audio Analysis:** Librosa calculates the tempo (BPM) and onset strength curve of the user's selected music track.
2. **Beat Grid Generation:** Downbeat timestamps are generated where musical energy peaks occur.
3. **Clip Alignment:** The AI Director prioritizes cut points that snap to the nearest downbeat timestamp within a tolerance of ±0.15s, creating an instinctively satisfying, musical rhythm in the rendered output.
4. **Speech Ducking:** Spoken dialogue detected via Whisper automatically triggers a volume envelope reduction (`volume=0.25`) on the music track with smooth 0.3s crossfades.

---

## 5. Security Architecture & Shell Injection Defense

CINEFLOW completely eliminates shell-injection vulnerabilities:
- **No `shell=True`:** All external binaries (`ffmpeg`, `ffprobe`, `ollama`) are invoked strictly through `subprocess.run(args_list, shell=False)`.
- **Strict Path Validation:** Filenames uploaded by users are slugified into UUID-based internal identifiers (`media_uuid.mp4`), preventing path traversal exploits (`../../`).
- **MIME & Header Verification:** File extensions are cross-checked with binary magic bytes using `python-magic` / header probing.
- **Quota Enforcers:** Local storage caps per project prevent disk exhaustion attacks.

