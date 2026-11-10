# CINEFLOW AI — Maintenance & Automated Testing Reference

> **Target Maintainers:** BMSIT Technical Club Engineering Leads  
> **Suite Status Command:** `backend\.venv\Scripts\python.exe -m pytest tests -v`

---

## 1. Automated Verification Matrix

| Scope | Test Files | What Is Verified |
| :--- | :--- | :--- |
| **Security & Upload Defense** | [`test_upload_security.py`](file:///c:/Users/mithu/ai%20video%20editing/tests/security/test_upload_security.py) | Path traversal sanitization, invalid extensions, spoofed magic bytes, zero `shell=True` subprocess guarantees. |
| **Real FFmpeg Rendering** | [`test_real_render_pipeline.py`](file:///c:/Users/mithu/ai%20video%20editing/tests/rendering/test_real_render_pipeline.py) | Health probe, batch upload, real 16:9 & 9:16 H.264/AAC MP4 output verified with FFprobe. |
| **CV, Audio, Director, Voice & Trends (Unit)** | [`tests/unit/`](file:///c:/Users/mithu/ai%20video%20editing/tests/unit) | Laplacian blur, dHash dedupe, 4-act director constraints, Librosa BPM & beat snapping, ASS caption escaping, SSRF URL blocking, scrypt/JWT/DDL parity, showcase & benchmark checks. |
| **End-to-End Integration** | [`tests/integration/`](file:///c:/Users/mithu/ai%20video%20editing/tests/integration) | Media search/scenes, Ollama/fallback director -> render, audio beat-sync -> MP4 render, voice Undo/Redo + partial render, trend recipe apply, campus JWT RBAC/quota `413`/cleanup, showcase loader & benchmarks API. |
| **Frontend Production Bundle** | `npm --prefix apps/web run build` | TypeScript strict checking, Next.js ESLint rules, and App Router static prerendering (`/` through `/showcase`). |

---

## 2. Running Checks & Benchmarks

```powershell
# 1. Run all backend unit, security, rendering, and integration tests
backend\.venv\Scripts\python.exe -m pytest tests -v

# 2. Run the Next.js TypeScript + production bundle build
npm --prefix apps/web run build

# 3. Refresh real hardware & pipeline performance benchmarks cleanly in isolation
backend\.venv\Scripts\python.exe -m backend.benchmarking.runner

# 4. Dry-run audit SQLite -> PostgreSQL 15+ schema parity
backend\.venv\Scripts\python.exe -m backend.migrations.sqlite_to_postgres --dry-run
```

---

## 3. Operational Notes & Troubleshooting

- **Windows Loopback / Sandboxed Runs:** Integration tests using Starlette `TestClient` or `asyncio.run` rely on Windows `socket.socketpair()`. Run them in a standard developer shell (not a socket-restricted container).
- **Storage Hygiene:** Runtime uploads (`data/uploads/`), 720p proxies (`data/proxies/`), temporary segment caches (`data/cache/segments/`), and completed exports (`data/renders/`) are excluded from Git via [`.gitignore`](file:///c:/Users/mithu/ai%20video%20editing/.gitignore). Only the committed Full-HD sample showcase pack under `assets/sample_media/` is version-controlled (`!assets/sample_media/**`).
- **Disk Quota & Cache Recovery:** Startup executes orphaned `.tmp`/`.ass` cache cleanup (`purge_storage_caches`) automatically, while full TTL pruning runs cleanly from `/admin` (`POST /api/v1/admin/cleanup`).

