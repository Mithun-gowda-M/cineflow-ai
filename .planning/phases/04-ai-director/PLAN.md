# PHASE 4 PLAN: AI Director & Storyboard Generator

> **Phase:** 04 — AI Director  
> **Status:** READY FOR EXECUTION  
> **Goal:** Implement natural-language creative instruction parsing, local Ollama LLM planning with JSON schema output, a deterministic 4-act Rule-Based Director fallback, strict timeline safety validation (zero artificial duplication), FastAPI director routes, and live Storyboard + Director generation in `apps/web`.

---

## 🎯 Phase Objectives

1. **Director Contracts:** Add Pydantic v2 schemas for `DirectorIntent`, `StoryboardBeat`, `DirectorPlanRequest`, `DirectorPlanResponse`, and `DirectorStatusResponse`.
2. **Instruction Parser:** Extract duration, aspect ratio, color grade, pacing, opening/climax/ending cues, and theme keywords from natural prompts.
3. **Dual-Mode Director Engine (Ollama + Deterministic Fallback):**
   - Integrate local Ollama open-weight LLM REST client (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`) with fast offline detection.
   - Build 4-act narrative clip & scene sequencer (`Opening Hook` -> `Rising Action` -> `Climax` -> `Emotional Resolution`) weighted by Phase 3 OpenCV quality scores and semantic tags, excluding near-duplicates.
   - Enforce strict **no artificial footage duplication** constraint.
4. **Timeline Safety Validator:** Clamp timestamps to true media bounds, verify all `source_id`s exist in SQLite, reject duplicate segments, and verify compatibility with Phase 2 FFmpeg rendering.
5. **API & Frontend Wiring:** Expose `POST /api/v1/director/plan` and `GET /api/v1/director/status`, and wire the Next.js Editor Copilot drawer to execute real AI storyboards and populate the multi-track timeline.

---

## 🌊 Wave-Based Task Breakdown

### Wave 1 — Config, Schemas & Instruction Parser
- **Task 4.1: Ollama Config & Director Schemas**
  - Add `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT_SECONDS` to `backend/api/config.py`.
  - Add `DirectorIntent`, `StoryboardBeat`, `DirectorPlanRequest`, `DirectorPlanResponse`, `DirectorStatusResponse` to `backend/api/schemas.py`.
- **Task 4.2: Natural Language Instruction Parser**
  - Implement `parse_director_instruction(...)` supporting word/digit durations (`"two-minute"`, `"90s"`), moods, aspect ratios, pacing curves, opening/climax/ending cues, and theme keywords.
  - **Target File:** `backend/ai_director/intent_parser.py`

### Wave 2 — Narrative Sequencer, Ollama Integration & Safety Validator
- **Task 4.3: 4-Act Narrative Sequencer & Anti-Duplication Solver**
  - Rank candidate scenes/assets by OpenCV quality + semantic relevance, exclude duplicates (`duplicate_of_id`) and severely blurred clips (`< 30` unless no alternative), assign 4-act narrative beats, transitions, speed ramps, audio tracks, and subtitle cues without duplicating clips.
  - **Target File:** `backend/ai_director/sequencer.py`
- **Task 4.4: Local Ollama Client & Timeline Safety Validator**
  - Implement async Ollama availability probe and structured JSON planning (`backend/ai_director/ollama_client.py`) with automatic fallback to `sequencer.py`.
  - Implement `validate_and_finalize_timeline(...)` (`backend/ai_director/validator.py`) clamping bounds, verifying `source_id` existence, and preventing duplicate segments.
  - Implement unified orchestrator `backend/ai_director/director.py`.

### Wave 3 — FastAPI Routes, Frontend Copilot Wiring & Automated Tests
- **Task 4.5: FastAPI Director Routes**
  - Create `backend/api/routes_director.py` (`POST /api/v1/director/plan`, `GET /api/v1/director/status`) and register in `backend/api/main.py`.
- **Task 4.6: Wire Frontend Editor Copilot & Storyboard Panel**
  - Update `apps/web/src/lib/api.ts`, `apps/web/src/components/editor/AiDirectorDrawer.tsx`, and `apps/web/src/app/editor/page.tsx` to invoke `/api/v1/director/plan`, populate real timeline clips/LUT/aspect ratio/subtitles, and show the generated Storyboard rationale inside the Copilot panel.
- **Task 4.7: Automated Unit & Integration Tests (Including Render Compatibility)**
  - Test prompt parsing (`"two-minute cinematic Deepavali..."`), 4-act ordering (`Diya` intro -> `Fireworks` climax -> `Sunset` emotional ending), zero artificial duplication when footage < requested duration, mocked Ollama valid JSON vs malformed JSON fallback, and end-to-end Director plan -> Phase 2 FFmpeg real MP4 render!
  - **Target Files:**
    - `tests/unit/test_ai_director_planner.py`
    - `tests/integration/test_director_api.py`

---

## 🔍 Verification & Acceptance Gates

1. **Prompt Parsing Gate:** `"Create a two-minute cinematic Deepavali video with slow dramatic intro and fast transitions during fireworks"` parses `120.0s`, `golden_hour`, `slow_dramatic` intro, `fireworks` climax, and `emotional` outro.
2. **Narrative Ordering & Quality Gate:** High-quality `Diya` / `Establishing` scenes place in Act 1, `Fireworks` / `Action` in Act 3 with faster pacing, `Sunset` in Act 4 with slow-mo fade-out; near-duplicates and severely blurred takes are excluded.
3. **Zero Duplication Gate:** Requesting `120s` when only `6s` of unique footage exists returns `~6s` total duration (never loops clips) plus a transparent `warnings` notice.
4. **Offline & Fallback Gate:** Runs 100% deterministically with Ollama offline, and safely falls back if an LLM returns invalid JSON or nonexistent `source_id`s.
5. **Render Compatibility Gate:** The `TimelinePlan` emitted by `POST /api/v1/director/plan` renders cleanly to a verified H.264/AAC MP4 via `POST /api/v1/render`.

---

## 🚀 Execution Command

Run:
```bash
/gsd-execute-phase 4
```

