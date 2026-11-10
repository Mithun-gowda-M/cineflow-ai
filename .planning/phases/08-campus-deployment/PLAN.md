# PHASE 8 PLAN: Institutional Campus Deployment & Security

> **Phase:** 08 — Institutional Campus Deployment & Security  
> **Status:** READY FOR EXECUTION  
> **Goal:** Install `PyJWT` & `psutil` in `backend/.venv`, implement secure salted-`scrypt` student authentication + HS256 JWT + RBAC, enforce per-student storage quotas & TTL cache cleanup policies, build live Admin Diagnostics APIs & PostgreSQL migration tooling (`001_postgres_initial.sql` + `sqlite_to_postgres.py`), replace frontend Auth/Admin/Dashboard stubs with live backend integration, and author BMSIT campus handover guides.

---

## 🎯 Phase Objectives

1. **Auth, JWT & RBAC (`backend/authentication/` + `routes_auth.py`):** Hash passwords with `hashlib.scrypt`, sign/verify HS256 JWT tokens via `PyJWT`, seed institutional student/admin demo accounts safely, support college domain gating, and expose `/api/v1/auth/{register,login,me,quota}`.
2. **Per-User Quotas & Automated Cleanup (`quotas.py`, `cleanup.py`, `routes_media.py`, `main.py`):** Track `owner_id` across assets & projects, block quota-exceeding uploads with HTTP `413`, clean stale temp artifacts cleanly at startup, and provide manual/TTL cache purging.
3. **Institutional Admin Backend (`routes_admin.py`):** Expose RBAC-protected `/api/v1/admin/{overview,users,users/{id},cleanup,migration-status}` backed by live `psutil` metrics and real disk accounting.
4. **PostgreSQL Deployment & Migrations (`backend/migrations/`):** Deliver production `001_postgres_initial.sql` DDL and `sqlite_to_postgres.py` verification/migration runner alongside updated `.env.example`.
5. **Frontend Auth, Quota & Live Admin UI (`apps/web`):** Upgrade `login/page.tsx`, `register/page.tsx`, `admin/page.tsx`, `dashboard/page.tsx`, `Navbar.tsx`, and `lib/api.ts` so every auth, quota, and admin action runs against real FastAPI endpoints.
6. **BMSIT Club Deployment & Handover Docs (`docs/`):** Write comprehensive `docs/deployment/CAMPUS_DEPLOYMENT_GUIDE.md` and `docs/handover/BMSIT_CLUB_HANDOVER.md`.

---

## 🌊 Wave-Based Task Breakdown

### Wave 1 — Dependencies, Security Core, Schemas & SQLite User/Quota Schema
- **Task 8.1: Install `PyJWT` & `psutil` and Update Requirements/Config/Schemas**
  - Install `PyJWT>=2.9.0` and `psutil>=6.0.0` in `backend/.venv` and add to `backend/requirements.txt`.
  - Add campus auth/quota config flags in `backend/api/config.py`: `JWT_ALGORITHM="HS256"`, `JWT_EXPIRE_MINUTES=720`, `RESTRICT_COLLEGE_EMAIL_DOMAIN=False`, `ALLOWED_AUTH_DOMAINS="bmsit.in,bmsit.ac.in"`, `REQUIRE_AUTH_FOR_MEDIA=False`, `CACHE_TTL_HOURS=24`, `DATABASE_URL="sqlite:///./data/cineflow.db"`.
  - Add Phase 8 schemas in `backend/api/schemas.py`: `UserRole`, `UserPublic`, `RegisterRequest`, `LoginRequest`, `AuthTokenResponse`, `QuotaStatusResponse`, `AdminUserUpdateRequest`, `AdminOverviewResponse`, `CleanupRequest`, `CleanupResponse`, `MigrationStatusResponse`.
- **Task 8.2: SQLite Users, Ownership & Migrations**
  - Extend `backend/api/database.py` with `users` table and `owner_id` column migrations (`media_assets`, `projects`) + user CRUD, default demo seeding (`student.innovator@bmsit.in`, `media.club@bmsit.in`), per-user storage summation (`get_user_storage_bytes`), and table row-count audit (`get_schema_table_counts`).

### Wave 2 — Auth Routes, Quota Enforcement, Cleanup Engine, Admin APIs & PostgreSQL Tooling
- **Task 8.3: Auth, JWT Dependencies & Quota Guards**
  - Implement `backend/authentication/security.py` (`hash_password`, `verify_password`, `create_access_token`, `decode_access_token`, `get_current_user`, `get_optional_current_user`, `require_admin_user`, `validate_college_domain`).
  - Implement `backend/authentication/quotas.py` (`enforce_upload_quota`, `get_user_quota_status`) and integrate ownership + quota enforcement into `backend/api/routes_media.py` & `backend/api/routes_projects.py`.
  - Create `backend/api/routes_auth.py` (`/auth/register`, `/auth/login`, `/auth/me`, `/auth/quota`).
- **Task 8.4: Storage Cleanup, Admin Telemetry Routes & PostgreSQL Migration Scripts**
  - Implement `backend/rendering/cleanup.py` (`compute_directory_sizes`, `purge_storage_caches`, `collect_system_metrics` via `psutil`).
  - Create `backend/api/routes_admin.py` (`/admin/overview`, `/admin/users`, `PATCH /admin/users/{id}`, `/admin/cleanup`, `/admin/migration-status`) enforcing admin RBAC, and register `auth_router` & `admin_router` in `backend/api/main.py` (with safe startup orphaned-temp cleanup).
  - Create `backend/migrations/001_postgres_initial.sql`, `backend/migrations/sqlite_to_postgres.py` (`--dry-run` / `--inspect` / copy CLI), and update `.env.example`.

### Wave 3 — Frontend Live Auth/Admin/Dashboard UI, Campus Docs & Verification Tests
- **Task 8.5: Frontend Campus Auth, Admin & Quota Integration**
  - Add auth token management, `Auth` & `Admin` API helpers, and authenticated fetch wrapper in `apps/web/src/lib/api.ts`.
  - Upgrade `apps/web/src/app/auth/login/page.tsx`, `apps/web/src/app/auth/register/page.tsx`, `apps/web/src/app/admin/page.tsx`, `apps/web/src/app/dashboard/page.tsx`, and `apps/web/src/components/Navbar.tsx` to authenticate via JWT, display active student identity/quota bar, and control real admin quotas + cache purges.
- **Task 8.6: Institutional Deployment & BMSIT Handover Documentation**
  - Author `docs/deployment/CAMPUS_DEPLOYMENT_GUIDE.md` and `docs/handover/BMSIT_CLUB_HANDOVER.md`.
- **Task 8.7: Unit, Security & Integration Tests**
  - `tests/unit/test_auth_and_migrations.py`: Verify `scrypt` password hashing, JWT issuance/expiration/tampering checks, college domain gating, PostgreSQL DDL parity + dry-run SQLite table audit.
  - `tests/integration/test_campus_auth_quota_admin_api.py`: Verify registration/login, `401` unauthenticated `/auth/me` & `/admin/overview`, `403` student access blocked on `/admin/*`, admin quota adjustment + real HTTP `413` quota block on upload, and real disk temp/render cleanup (`purge_storage_caches`) reclaiming bytes cleanly.

---

## 🔍 Verification & Acceptance Gates

1. **Auth & RBAC Security Gate:** Passwords are stored strictly as salted `scrypt` digests; tampered/expired/missing JWTs return `401`; non-admin student tokens return `403` on `/api/v1/admin/*`.
2. **Quota & Cleanup Gate:** Setting a user quota cap lower than incoming upload size strictly blocks upload (`413`), and admin cleanup (`POST /api/v1/admin/cleanup`) physically deletes expired temp/render files without touching user source uploads.
3. **Migration Parity Gate:** `001_postgres_initial.sql` covers every table in SQLite and `sqlite_to_postgres.py --dry-run` verifies schema/row counts cleanly (`exit 0`).
4. **Full Regression & Build Gate:** All `pytest tests -v` suites pass (`100%`) and `npm --prefix apps/web run build` exits `0`.

---

## 🚀 Execution Command

Run:
```bash
/gsd-execute-phase 8
```
