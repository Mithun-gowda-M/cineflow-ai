# PHASE 4 RESEARCH: AI Director & Storyboard Generator

> **Phase:** 04 — AI Director & Storyboard Generator  
> **Target:** Dual-Mode Local LLM (Ollama) + Deterministic Narrative Engine  
> **Status:** Research Complete

---

## 1. Dual-Mode Local-First Architecture

CINEFLOW AI cannot depend on mandatory cloud LLM subscriptions (OpenAI/Anthropic) and must remain 100% functional even on offline student laptops without a GPU running Ollama:
- **Primary Mode (`Ollama`):** Local open-weight models (`llama3.2`, `mistral`, `qwen2.5`) accessed via `http://localhost:11434/api/chat` with `format="json"` and a strict 2.5s health timeout.
- **Deterministic Fallback Mode (`Rule-Based Director`):** Whenever Ollama is unreachable, disabled, or returns malformed JSON, the deterministic 4-act narrative sequencer automatically plans the exact storyboard and `TimelinePlan` with zero failure.

---

## 2. Prompt & Narrative Structure Design

### 2.1 Instruction Parsing (`DirectorIntent`)
Natural prompts such as *"Create a two-minute cinematic Deepavali video. Start with a slow dramatic introduction. Use fast transitions during the fireworks. Make the ending emotional."* decompose cleanly into:
- **Duration Target:** Number/word extraction (`two-minute` → `120s`, `90s` → `90s`, default `60s`).
- **Aspect Ratio:** (`9:16` / `Reels` / `Shorts`, `1:1`, `21:9`, `16:9`).
- **Color Grade:** Semantic mapping (`Deepavali`/`Golden` → `golden_hour`, `Travel`/`Cinema` → `cinematic_teal_orange`, `Emotional`/`Moody` → `moody_dark`, `Wedding`/`Vintage` → `vintage_film`).
- **Pacing Curve:** 4-Act pacing curve (`Hook` → `Rising Action` → `Climax` → `Emotional Resolution`) with per-act speed and transition assignments.

### 2.2 Strict Anti-Duplication Constraint
Per the CINEFLOW Master Specification:
- **Zero Artificial Looping:** The sequencer tracks used `(source_id, start_time, end_time)` intervals and forbids reusing identical segments to pad up to `target_duration_seconds`.
- **Transparent Shortfall Warning:** If total unique usable source media is less than `target_duration_seconds`, the Director produces the maximum unique timeline and returns an explicit warning explaining the source duration limit.

---

## 3. Safety & Validation Boundary

Language models are never trusted to execute shell commands or reference arbitrary filesystem paths:
1. LLM receives only abstract asset/scene metadata (`id`, `tags`, `quality_score`, `duration_seconds`).
2. LLM output is parsed as JSON and cross-checked against `Database` records.
3. Invalid IDs, out-of-bounds trim timestamps, out-of-range speeds (`[0.25, 4.0]`), or duplicate intervals are clamped or rejected by `validate_and_sanitize_timeline(...)` before the `TimelinePlan` reaches the user or Phase 2 FFmpeg renderer.
