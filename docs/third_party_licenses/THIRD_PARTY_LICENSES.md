# CINEFLOW AI — Third-Party Licenses and Evaluation

This document satisfies the licensing, redistribution, and architecture compatibility requirements of CINEFLOW AI (Phase 0). Every third-party library and supporting technology is documented with its upstream license, purpose, resource requirements, and architectural role.

---

## 1. Primary Open-Source Technologies

| Dependency | Repository URL | Version Target | License | Architectural Role | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FFmpeg** | `https://github.com/FFmpeg/FFmpeg` | 6.x / 7.x | LGPL v2.1+ (GPL v2+ optional) | Primary video and audio rendering, filtering, muxing, demuxing, probing | **Mandatory** |
| **OpenCV (opencv-python)** | `https://github.com/opencv/opencv` | 4.10.x | Apache 2.0 | Frame extraction, blur detection (Laplacian variance), exposure, color analysis | **Mandatory** |
| **PySceneDetect** | `https://github.com/Breakthrough/PySceneDetect` | 0.6.x | BSD 3-Clause | Automated video cut detection, scene transition identification, boundary generation | **Mandatory** |
| **Ollama** | `https://github.com/ollama/ollama` | Latest / 0.3+ | MIT | Local open-weight LLM inference (Llama 3.2, Mistral, Qwen) for AI Director | **Supported (Graceful Fallback)** |
| **Whisper.cpp / faster-whisper** | `https://github.com/ggml-org/whisper.cpp` | Latest / 1.5+ | MIT | Local speech-to-text, subtitle generation, voice command parsing on CPU | **Modular / Optional** |
| **Librosa** | `https://github.com/librosa/librosa` | 0.10.x | ISC | Audio beat tracking, tempo estimation, spectral energy analysis for sync cuts | **Mandatory (Audio Engine)** |
| **FFmpeg-Python** | `https://github.com/kkroening/ffmpeg-python` | 0.2.x | MIT | Declarative Python filtergraph assembly and subprocess pipeline execution | **Supporting Library** |
| **MoviePy** | `https://github.com/Zulko/moviepy` | 2.x | MIT | High-level compositing and animation reference; native FFmpeg preferred for production | **Reference / Utility** |
| **Editly** | `https://github.com/mifi/editly` | 0.14.x | MIT | Timeline structure and JSON editing plan reference specification | **Reference Model** |
| **Auto-Editor** | `https://github.com/WyattBlue/auto-editor` | 23.x | Unlicense | Audio silence thresholding and jump-cut sequencing blueprint | **Algorithm Blueprint** |

---

## 2. Detailed License & Compatibility Analysis

### 2.1 FFmpeg
- **Upstream License:** LGPL v2.1 (can be built with GPL v2/v3 if `--enable-gpl` or `--enable-nonfree` is used).
- **Redistribution Conditions:** CINEFLOW AI interacts with FFmpeg as an external binary executable via subprocesses (`spawn`/`Popen`). Source code of FFmpeg is not modified or statically linked into proprietary binaries, adhering strictly to LGPL v2.1 dynamic executable usage rules.
- **Hardware/System Impact:** Cross-platform (Windows, Linux, macOS). Supports software (CPU) encoding `libx264`/`aac` as universal baseline, with hardware acceleration (`h264_nvenc`, `h264_qsv`, `h264_amf`) when detected.

### 2.2 OpenCV (`opencv-python-headless`)
- **Upstream License:** Apache 2.0.
- **Redistribution Conditions:** Permissive license. Allows commercial and academic use, distribution, and modification with copyright notice preservation.
- **Hardware/System Impact:** Uses `opencv-python-headless` to eliminate GUI window dependencies on headless servers or student laptops. Low CPU and memory footprint during batch frame analysis.

### 2.3 PySceneDetect
- **Upstream License:** BSD 3-Clause.
- **Redistribution Conditions:** Highly permissive. Requires retention of copyright notice and disclaimer.
- **Hardware/System Impact:** Efficient scene transition detection using content and adaptive detectors; configured with frame skipping (e.g., analyzing 4 fps instead of 30/60 fps) to run smoothly on lower-spec machines.

### 2.4 Ollama
- **Upstream License:** MIT.
- **Model Licenses:** Dependent on user-selected model weights (e.g., Llama 3.2 Community License, Mistral Apache 2.0).
- **Graceful Degradation:** When Ollama is offline or not installed, CINEFLOW AI activates the **Rule-Based Director Fallback** (heuristic scene selection, duration distribution, and tempo matching) so the application remains 100% operational with zero failures.

### 2.5 Whisper.cpp / faster-whisper
- **Upstream License:** MIT.
- **Model Weights:** OpenAI Whisper weights (MIT License).
- **Hardware/System Impact:** Uses quantized `base` or `tiny` models (under 150MB) on CPU with INT8 quantization, enabling instant speech recognition even on entry-level student laptops.

### 2.6 Librosa
- **Upstream License:** ISC (equivalent to 2-Clause BSD / MIT).
- **Redistribution Conditions:** Permissive; requires copyright preservation.
- **Hardware/System Impact:** Uses SciPy/NumPy; audio is loaded at 22,050 Hz mono for lightning-fast beat detection and onset peak extraction without heavy RAM overhead.

---

## 3. Originality & Clean-Room Architecture Guarantee

CINEFLOW AI maintains **complete architectural originality**:
1. All AI director algorithms, storyboard generation schemas, multi-track timeline representations, and rendering orchestration are original CINEFLOW implementations.
2. Third-party tools serve purely as low-level engine primitives (e.g., FFmpeg executes the filtergraph; Librosa calculates tempo; PySceneDetect spots cut frames).
3. No proprietary, restrictive, or viral-copyleft code is copied or embedded. All CINEFLOW AI code is released under the **MIT License**.
