# PHASE 3 RESEARCH: AI Media Intelligence & Scene Detection

> **Phase:** 03 — AI Media Intelligence  
> **Target:** PySceneDetect + OpenCV Quality, Semantic Tagging, Deduplication & Searchable Library  
> **Status:** Research Complete

---

## 1. Library & Dependency Evaluation

To meet CINEFLOW AI's zero-subscription, CPU-friendly laptop requirements on Python 3.12 (Windows & Linux):
- **`opencv-python-headless` (`>=4.10.0`)**: Apache 2.0 license. Avoids GUI toolkit conflicts (`Qt`/`GTK`) on servers and headless workers while providing full frame decoding, Laplacian blur detection, HSV color histograms, Farneback optical flow, and built-in Haar cascade face detection (`cv2.data.haarcascades`).
- **`scenedetect[opencv]` (`>=0.6.4`)**: BSD 3-Clause license. Provides `ContentDetector` and `AdaptiveDetector` for accurate cut/fade boundary detection. Downscale factor (`downscale=2` or `3`) and `frame_skip` keep runtime under ~1–3 seconds per clip on standard CPUs.
- **`numpy` (`>=1.26.0`)**: BSD 3-Clause license. Used for vectorized histogram analysis, perceptual `dHash` computation, and dominant color clustering. Note: Verify `opencv-python-headless` and `scenedetect` compatibility with NumPy 2.x vs 1.26 in `backend/.venv` cleanly during Wave 1.

---

## 2. Transparent Quality Scoring Formulas

Rather than an opaque score, CINEFLOW exposes four explicit sub-metrics (`0.0–100.0`) plus a weighted composite score and human-readable explanation:

1. **Sharpness (`sharpness_score`):**
   - Measure Laplacian variance: $v = \text{Var}(\nabla^2 I_{\text{gray}})$ across sampled frames.
   - Normalized piece-wise curve: $v < 20 \to 0\text{–}35$ (Blurry), $20 \le v < 120 \to 35\text{–}75$ (Soft/Acceptable), $v \ge 120 \to 75\text{–}100$ (Crisp).
2. **Exposure (`exposure_score`):**
   - Compute grayscale luminance mean $\mu \in [0, 255]$, clipped shadow fraction ($I < 12$), and blown highlight fraction ($I > 245$).
   - Penalize severe underexposure ($\mu < 40$), overexposure ($\mu > 220$), and high clipping (>20% crushed/blown pixels).
3. **Motion & Camera Stability (`stability_score`):**
   - Compare consecutive sampled frames using downscaled optical flow / absolute frame difference and flow variance.
   - Distinguish steady tripod/static shots, smooth pans, energetic action, and erratic camera shake.
4. **Composition & Subject Visibility (`composition_score`):**
   - Detect faces via OpenCV's built-in `haarcascade_frontalface_default.xml` (plus edge/saliency balance when no faces exist).
   - Reward clear subject centering or rule-of-thirds placement and clean foreground edge density.
5. **Composite Weighting:**
   - **Video:** $0.30 \cdot \text{Sharpness} + 0.25 \cdot \text{Exposure} + 0.25 \cdot \text{Stability} + 0.20 \cdot \text{Composition}$
   - **Image:** $0.40 \cdot \text{Sharpness} + 0.35 \cdot \text{Exposure} + 0.25 \cdot \text{Composition}$

---

## 3. Perceptual Duplicate Detection (`dHash`)

To stop the AI Director or user timelines from placing identical retakes consecutively:
- Compute a 64-bit Difference Hash (`dHash`) on a $9 \times 8$ grayscale thumbnail (`col[x+1] > col[x]`).
- Compare Hamming distance between uploaded media assets (and detected scenes):
  - Hamming distance $0\text{–}3$: Exact / near-exact duplicate (`similarity >= 95%`)
  - Hamming distance $4\text{–}7$: Visually similar retake (`similarity >= 89%`)
- Flag `duplicate_of_id` and `similarity_percent` non-destructively so users can toggle duplicate filtering in the library.

---

## 4. Rule-Based Semantic Tagging & Natural Search

Deterministic HSV + structural rules extract meaningful tags without paid Vision APIs:
- **Lighting & Color Mood:** `Golden-Warm`, `Vibrant`, `Night / Low-Light`, `Bright Daylight`, `Cool-Toned`.
- **Scene Semantics:**
  - Dark background + localized bright warm spikes → `Fireworks` / `Diya` / `Night Lights`
  - Warm upper gradient + horizontal horizon edges → `Sunset` / `Landscape`
  - 1 detected face (>4% frame area) → `Portrait`, `People`; 2+ faces → `Group`, `Celebration`
  - High motion energy → `Action`; steady wide framing → `Establishing`
- **Search Query Ranking:** Tokenizes natural queries like `"find the best fireworks clips"` or `"brightest diya shots"`, strips stop-words (`find`, `the`, `best`, `most`, `clips`, `shots`), matches tags + filenames + explanations, and adjusts sort priority (`"best"` → quality, `"brightest"` → brightness/exposure, `"sharpest"` → sharpness).
