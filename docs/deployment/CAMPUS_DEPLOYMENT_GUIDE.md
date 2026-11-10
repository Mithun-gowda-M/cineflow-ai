# CINEFLOW AI — Institutional Campus Deployment Guide (BMSIT)

> **Target Environments:** Campus On-Premise Linux Server (Ubuntu 22.04+ / Docker), Windows Lab Workstation, Local LAN Intranet  
> **Zero External Cloud Cost:** Uses local PostgreSQL 15+, local FFmpeg, Ollama, Librosa, and CPU `faster-whisper`.

---

## 1. Environment Hardening (`.env`)

Copy `.env.example` to `.env` before deploying in institutional multi-student mode:

```ini
ENVIRONMENT="production"
SECRET_KEY="generate-a-64-char-cryptographically-random-hex-secret"
ALLOWED_ORIGINS="https://cineflow.bmsit.ac.in,http://localhost:3000"

# Institutional Campus RBAC & Email Gating
REQUIRE_AUTH_FOR_MEDIA=true
RESTRICT_COLLEGE_EMAIL_DOMAIN=true
ALLOWED_AUTH_DOMAINS="bmsit.in,bmsit.ac.in"
USER_STORAGE_QUOTA_GB=20.0
JWT_EXPIRE_MINUTES=720

# Hardware Profile & Cache Retention
HARDWARE_PROFILE="auto"
MAX_CONCURRENT_RENDERS=2
MAX_SEGMENT_CACHE_MB=2048
CACHE_TTL_HOURS=24

# Database (PostgreSQL 15+ recommended for multi-user campus labs)
DATABASE_URL="postgresql://cineflow:CHANGE_PASSWORD@127.0.0.1:5432/cineflow"
```

---

## 2. Database Migration: SQLite Dev -> PostgreSQL 15+

1. Create the PostgreSQL database and load the verified production DDL ([001_postgres_initial.sql](file:///c:/Users/mithu/ai%20video%20editing/backend/migrations/001_postgres_initial.sql)):
   ```bash
   psql "$DATABASE_URL" -f backend/migrations/001_postgres_initial.sql
   ```
2. Verify schema & row counts before migrating from local dev SQLite:
   ```bash
   backend/.venv/Scripts/python.exe -m backend.migrations.sqlite_to_postgres --dry-run
   ```
3. Execute transactional migration (requires `pip install "psycopg[binary]"`):
   ```bash
   backend/.venv/Scripts/python.exe -m backend.migrations.sqlite_to_postgres --pg-url "$DATABASE_URL"
   ```

---

## 3. Running Production Processes Behind Nginx TLS

- **Backend Gateway (FastAPI + Uvicorn):**
  ```bash
  uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --workers 2
  ```
- **Frontend Studio (Next.js 15 Production Server):**
  ```bash
  cd apps/web
  npm ci
  NEXT_PUBLIC_API_URL="https://cineflow.bmsit.ac.in/api/v1" npm run build
  npm run start -- -p 3000
  ```
- **Nginx Reverse Proxy:** Route `/api/` and `/static/` to `127.0.0.1:8000` (with `client_max_body_size 512M;` matching `MAX_UPLOAD_FILE_MB`) and `/` to `127.0.0.1:3000`.

---

## 4. Storage Quotas & Automated Cleanup Policies

- Each registered student receives `USER_STORAGE_QUOTA_GB` (adjustable per student in `/admin`).
- Uploads pushing a user over quota fail fast with HTTP `413` before filling campus disks.
- Startup lifecycle in `backend/api/main.py` automatically purges orphaned temp artifacts in `data/cache` older than `CACHE_TTL_HOURS`; Club Admins can trigger full cache & expired render cleanup anytime from `/admin` (`POST /api/v1/admin/cleanup`).

---

## 5. Seeded Onboarding Accounts (Change Passwords Immediately!)

When the database starts fresh, idempotent institutional onboarding seeds two demo logins (visible on `/auth/login` for quick lab evaluation — rotate or disable in production):
- **Demo Student:** `student.innovator@bmsit.in` / `bmsit2026cineflow`
- **Club Admin:** `media.club@bmsit.in` / `bmsit2026admin`

