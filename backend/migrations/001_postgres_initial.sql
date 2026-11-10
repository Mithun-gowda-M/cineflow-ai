-- ============================================================================
-- CINEFLOW AI — Institutional Campus PostgreSQL 15+ Production Schema
-- Migration ID: 001_campus_v1
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL DEFAULT 'Computer Science & Engineering',
    role TEXT NOT NULL DEFAULT 'student',
    password_hash TEXT NOT NULL,
    storage_quota_bytes BIGINT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

CREATE TABLE IF NOT EXISTS media_assets (
    id TEXT PRIMARY KEY,
    owner_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    media_kind TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_path TEXT NOT NULL,
    source_url TEXT NOT NULL,
    thumbnail_url TEXT,
    proxy_url TEXT,
    proxy_path TEXT,
    metadata_json JSONB NOT NULL,
    tags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    analysis_json JSONB,
    audio_analysis_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_media_owner ON media_assets (owner_id, created_at DESC);

CREATE TABLE IF NOT EXISTS detected_scenes (
    scene_id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL REFERENCES media_assets(id) ON DELETE CASCADE,
    scene_index INTEGER NOT NULL,
    start_seconds DOUBLE PRECISION NOT NULL,
    end_seconds DOUBLE PRECISION NOT NULL,
    duration_seconds DOUBLE PRECISION NOT NULL,
    thumbnail_url TEXT,
    quality_score DOUBLE PRECISION NOT NULL DEFAULT 75.0,
    sharpness_score DOUBLE PRECISION NOT NULL DEFAULT 75.0,
    motion_level TEXT NOT NULL DEFAULT 'static',
    tags_json JSONB NOT NULL DEFAULT '[]'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_scenes_media ON detected_scenes (media_id, scene_index);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    owner_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    aspect_ratio TEXT NOT NULL DEFAULT '16:9',
    target_duration_seconds DOUBLE PRECISION NOT NULL DEFAULT 120.0,
    color_grade TEXT NOT NULL DEFAULT 'golden_hour',
    timeline_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects (owner_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS render_jobs (
    job_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL,
    progress_percent DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    current_step TEXT NOT NULL,
    resolution TEXT NOT NULL DEFAULT '1080p',
    output_path TEXT,
    output_video_url TEXT,
    output_file_size_bytes BIGINT,
    segment_cache_hits INTEGER NOT NULL DEFAULT 0,
    segment_cache_misses INTEGER NOT NULL DEFAULT 0,
    partial_rerender_used BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_render_jobs_project ON render_jobs (project_id, created_at DESC);

CREATE TABLE IF NOT EXISTS timeline_revisions (
    revision_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    revision_index INTEGER NOT NULL,
    command_text TEXT NOT NULL,
    diff_summary_json JSONB NOT NULL,
    timeline_json JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_revisions_project_idx ON timeline_revisions (project_id, revision_index);

CREATE TABLE IF NOT EXISTS style_recipes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    source_type TEXT NOT NULL,
    is_builtin BOOLEAN NOT NULL DEFAULT FALSE,
    recipe_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO schema_migrations (version)
VALUES ('001_campus_v1')
ON CONFLICT (version) DO NOTHING;

