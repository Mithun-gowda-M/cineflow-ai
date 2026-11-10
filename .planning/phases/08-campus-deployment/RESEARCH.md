# PHASE 8 RESEARCH: Institutional Campus Deployment & Security

> **Phase:** 08 — Institutional Campus Deployment & Security  
> **Target:** Student JWT Auth & RBAC, Per-User Storage Quotas, Automated Cache Cleanup, Live Admin Diagnostics Dashboard, SQLite -> PostgreSQL Migration Toolkit, and BMSIT Handover Docs  
> **Status:** Research Complete

---

## 1. Authentication & Role-Based Access Control (RBAC)

- **Packages:** `PyJWT>=2.9.0` (MIT License) for RFC 7519 HS256 JWT token signing/verification + Python 3.12 standard-library `hashlib.scrypt` (`N=16384, r=8, p=1`) + `hmac.compare_digest` for salted password storage (eliminating Windows C-compiler `bcrypt` friction).
- **Roles:**
  - `student`: Upload media within assigned storage quota, create/edit/render own projects.
  - `club_lead`: Elevated studio storage cap and shared club workspace visibility.
  - `admin`: Full Institutional Admin Dashboard access (`/api/v1/admin/*`), quota calibration, user account activation/revocation, cache cleanup, and DB migration diagnostics.
- **Backward Compatibility & Dual Campus Mode:**
  - Strict JWT + RBAC enforcement protects `/api/v1/auth/me` and all `/api/v1/admin/*` routes unconditionally (`401 Unauthorized` without valid Bearer JWT, `403 Forbidden` when role is `"student"` on admin routes).
  - Controlled via `REQUIRE_AUTH_FOR_MEDIA` (`false` in single-user workstation dev so existing Phase 2–7 studio calls remain frictionless, `true` in institutional multi-student campus deployments via `.env`).
  - Optional `RESTRICT_COLLEGE_EMAIL_DOMAIN` validates `@bmsit.in` / `@bmsit.ac.in` registrations cleanly.

---

## 2. Storage Quotas & Automated Cache Cleanup

- **Media Ownership & Quota Enforcement:** Adding `owner_id` columns (via idempotent `PRAGMA table_info` migration) on `media_assets` and `projects` tracks cumulative uploaded bytes per user. Uploads exceeding `user.storage_quota_bytes` fail fast with HTTP `413 Payload Too Large` before touching disk.
- **Disk Telemetry & TTL Purge:**
  - Uses `psutil>=6.0.0` (BSD 3-Clause License) for cross-platform CPU load %, RAM allocation, and partition disk space alongside recursive byte audits of `data/uploads`, `data/proxies`, `data/renders`, and `data/cache` (including `data/cache/segments`).
  - `purge_storage_caches(...)` cleans expired temporary artifacts (`.tmp.mp4`, `.ass`, stale segment caches, and old completed exports beyond `max_age_hours`) cleanly without harming user source uploads, running automatically on startup for orphaned temp files and on-demand from the Admin Dashboard.

---

## 3. SQLite Dev -> PostgreSQL Campus Migration Architecture

- **Schema Parity:** Existing SQLite schema spans 7 application tables (`users`, `media_assets`, `detected_scenes`, `projects`, `render_jobs`, `timeline_revisions`, `style_recipes`).
- **Migration Artifacts:**
  - `backend/migrations/001_postgres_initial.sql`: Idempotent PostgreSQL 15+ DDL with `JSONB`, `TIMESTAMPTZ`, `BIGINT`, and relational foreign keys.
  - `backend/migrations/sqlite_to_postgres.py`: Deterministic verification, JSON dump / dry-run inspector, and live PostgreSQL copier (when `psycopg` + `DATABASE_URL=postgresql://...` are configured).

---

## 4. Existing UI Pages to Upgrade from Demo Stubs

Inspecting `apps/web/src/app/` confirmed three existing Phase 1 stub views ready for real API wiring:
1. `apps/web/src/app/auth/login/page.tsx`: Replace direct `router.push("/dashboard")` with real `POST /api/v1/auth/login`.
2. `apps/web/src/app/auth/register/page.tsx`: Replace direct `router.push("/dashboard")` with real `POST /api/v1/auth/register`.
3. `apps/web/src/app/admin/page.tsx`: Replace hardcoded `studentAccounts` array and simulated `setTimeout` purge button with live `/api/v1/admin/overview`, `/api/v1/admin/users`, quota updates (`PATCH`), and real disk cache cleanup (`POST`).
