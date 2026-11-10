# PHASE 5 RESEARCH: Advanced Cinematic Engine & Audio Intelligence

> **Phase:** 05 — Advanced Cinematic Engine & Audio Intelligence  
> **Target:** Librosa Beat Synchronization, Speed Ramps, ASS Animated Typography, Bleach Bypass & Sidechain Audio Ducking  
> **Status:** Research Complete

---

## 1. Verified FFmpeg 9.0.2 Filter Capabilities

Inspection of `Gyan.FFmpeg 9.0.2` (`ffmpeg.exe -filters`) confirmed built-in support for all required Phase 5 filters:
- **`ass` (`libass`):** Vector subtitle & animated typography rendering with fade tags (`\fad`), champagne-gold styling, outlines, and drop-shadows.
- **`drawtext` (`libfreetype`):** Direct text overlays when needed.
- **`vignette` & `noise`:** Lens edge falloff and natural 35mm film grain texture.
- **`zoompan`:** Smooth Ken Burns camera push-in on still images.
- **`sidechaincompress`:** Real-time audio ducking (music automatically dips under foreground dialogue/speech).
- **`loudnorm`:** EBU R128 broadcast loudness normalization (`I=-16 LUFS`, `TP=-1.5 dBTP`).

### Windows Path Escaping for FFmpeg `ass` Filter
On Windows, FFmpeg filtergraph parsing treats `:` as an option separator and `\` as an escape character. Passing a generated `.ass` subtitle file safely requires normalizing path separators to `/` and escaping the drive-letter colon:
`C:\cineflow\cache\job.ass` → `C\:/cineflow/cache/job.ass` wrapped inside `ass=filename='...'`.

---

## 2. Audio Analysis & Beat Synchronization (`Librosa`)

- **License:** `librosa` (ISC license) + `soundfile` (BSD 3-Clause license).
- **Format Compatibility:** Compressed MP4/AAC/M4A audio streams are decoded via FFmpeg to temporary 22,050 Hz mono PCM WAV before feeding `librosa.load(...)`, ensuring identical behavior across WAV, MP3, FLAC, AAC, and video files without requiring external `audioread` codecs.
- **Beat Grid & Waveform Extraction:**
  - `tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)` computes BPM and beat timestamps.
  - Downbeats (every 4th beat) serve as anchor points for transition snapping (`±0.35s` tolerance) so scene cuts hit musical drops cleanly without distorting clip order or violating Phase 4's anti-duplication guard.
  - 64 normalized RMS energy bars (`0.0–1.0`) power real waveform visualization in the React `MultiTrackTimeline`.

---

## 3. Multi-Phase Speed Ramps & Look Science

- **Speed Ramps:** Clips support `"none"`, `"fast_to_slow"` (1.6x acceleration on opening 40% dropping to 0.65x slow-motion impact on closing 60%), `"slow_to_fast"` (0.75x build-up accelerating into 1.5x burst), and `"ease_in_out"`, implemented cleanly via split video/audio `trim` + `setpts`/`atempo` + `concat` inside the per-clip normalization branch.
- **Bleach Bypass LUT:** Emulated via desaturated high-contrast luminance blend (`eq=contrast=1.32:saturation=0.45:brightness=-0.03`).
