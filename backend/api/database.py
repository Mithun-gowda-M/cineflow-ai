"""Thread-safe SQLite repository for CINEFLOW AI media, projects, and render jobs."""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from backend.api.config import get_settings, utc_now_iso
from backend.api.schemas import (
    DetectedScene,
    MediaAnalysisResult,
    MediaAsset,
    MediaMetadata,
    ProjectResponse,
    RenderJobStatus,
    TimelinePlan,
)


class Database:
    """Lightweight SQLite store using WAL mode and explicit parameterized queries."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        settings = get_settings()
        self.db_path = db_path or settings.DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS media_assets (
                    id TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    stored_filename TEXT NOT NULL,
                    media_kind TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    thumbnail_url TEXT,
                    proxy_url TEXT,
                    proxy_path TEXT,
                    metadata_json TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    analysis_json TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS detected_scenes (
                    scene_id TEXT PRIMARY KEY,
                    media_id TEXT NOT NULL,
                    scene_index INTEGER NOT NULL,
                    start_seconds REAL NOT NULL,
                    end_seconds REAL NOT NULL,
                    duration_seconds REAL NOT NULL,
                    thumbnail_url TEXT,
                    quality_score REAL NOT NULL DEFAULT 75.0,
                    sharpness_score REAL NOT NULL DEFAULT 75.0,
                    motion_level TEXT NOT NULL DEFAULT 'static',
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    FOREIGN KEY (media_id) REFERENCES media_assets(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    aspect_ratio TEXT NOT NULL DEFAULT '16:9',
                    target_duration_seconds REAL NOT NULL DEFAULT 120.0,
                    color_grade TEXT NOT NULL DEFAULT 'golden_hour',
                    timeline_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS render_jobs (
                    job_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress_percent REAL NOT NULL DEFAULT 0.0,
                    current_step TEXT NOT NULL,
                    resolution TEXT NOT NULL DEFAULT '1080p',
                    output_path TEXT,
                    output_video_url TEXT,
                    output_file_size_bytes INTEGER,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            # Safe idempotent migration for pre-Phase 3 SQLite databases
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(media_assets)").fetchall()}
            if "analysis_json" not in cols:
                conn.execute("ALTER TABLE media_assets ADD COLUMN analysis_json TEXT")

    # ---- Media Assets ----

    def save_media_asset(self, asset: MediaAsset) -> MediaAsset:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO media_assets (
                    id, original_filename, stored_filename, media_kind, mime_type,
                    file_size_bytes, file_path, source_url, thumbnail_url,
                    proxy_url, proxy_path, metadata_json, tags_json, analysis_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    original_filename = excluded.original_filename,
                    stored_filename = excluded.stored_filename,
                    media_kind = excluded.media_kind,
                    mime_type = excluded.mime_type,
                    file_size_bytes = excluded.file_size_bytes,
                    file_path = excluded.file_path,
                    source_url = excluded.source_url,
                    thumbnail_url = excluded.thumbnail_url,
                    proxy_url = excluded.proxy_url,
                    proxy_path = excluded.proxy_path,
                    metadata_json = excluded.metadata_json,
                    tags_json = excluded.tags_json,
                    analysis_json = excluded.analysis_json
                """,
                (
                    asset.id,
                    asset.original_filename,
                    asset.stored_filename,
                    asset.media_kind,
                    asset.mime_type,
                    asset.file_size_bytes,
                    asset.file_path,
                    asset.source_url,
                    asset.thumbnail_url,
                    asset.proxy_url,
                    asset.proxy_path,
                    asset.metadata.model_dump_json(),
                    json.dumps(asset.tags),
                    asset.analysis.model_dump_json() if asset.analysis else None,
                    asset.created_at,
                ),
            )
            if asset.scenes:
                self._replace_scenes_in_conn(conn, asset.id, asset.scenes)
        return asset

    def _replace_scenes_in_conn(
        self, conn: sqlite3.Connection, media_id: str, scenes: list[DetectedScene]
    ) -> None:
        conn.execute("DELETE FROM detected_scenes WHERE media_id = ?", (media_id,))
        for sc in scenes:
            conn.execute(
                """
                INSERT INTO detected_scenes (
                    scene_id, media_id, scene_index, start_seconds, end_seconds,
                    duration_seconds, thumbnail_url, quality_score, sharpness_score,
                    motion_level, tags_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sc.scene_id,
                    media_id,
                    sc.scene_index,
                    sc.start_seconds,
                    sc.end_seconds,
                    sc.duration_seconds,
                    sc.thumbnail_url,
                    sc.quality_score,
                    sc.sharpness_score,
                    sc.motion_level,
                    json.dumps(sc.tags),
                ),
            )

    def save_detected_scenes(self, media_id: str, scenes: list[DetectedScene]) -> list[DetectedScene]:
        with self._connect() as conn:
            self._replace_scenes_in_conn(conn, media_id, scenes)
        return scenes

    def _row_to_scene(self, row: sqlite3.Row) -> DetectedScene:
        return DetectedScene(
            scene_id=row["scene_id"],
            media_id=row["media_id"],
            scene_index=row["scene_index"],
            start_seconds=row["start_seconds"],
            end_seconds=row["end_seconds"],
            duration_seconds=row["duration_seconds"],
            thumbnail_url=row["thumbnail_url"],
            quality_score=row["quality_score"],
            sharpness_score=row["sharpness_score"],
            motion_level=row["motion_level"],
            tags=json.loads(row["tags_json"]),
        )

    def get_detected_scenes(self, media_id: str) -> list[DetectedScene]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM detected_scenes WHERE media_id = ? ORDER BY scene_index ASC",
                (media_id,),
            ).fetchall()
            return [self._row_to_scene(r) for r in rows]

    def _row_to_media(self, row: sqlite3.Row, scenes: Optional[list[DetectedScene]] = None) -> MediaAsset:
        analysis_raw = row["analysis_json"] if "analysis_json" in row.keys() else None
        analysis = MediaAnalysisResult.model_validate_json(analysis_raw) if analysis_raw else None
        return MediaAsset(
            id=row["id"],
            original_filename=row["original_filename"],
            stored_filename=row["stored_filename"],
            media_kind=row["media_kind"],
            mime_type=row["mime_type"],
            file_size_bytes=row["file_size_bytes"],
            file_path=row["file_path"],
            source_url=row["source_url"],
            thumbnail_url=row["thumbnail_url"],
            proxy_url=row["proxy_url"],
            proxy_path=row["proxy_path"],
            metadata=MediaMetadata.model_validate_json(row["metadata_json"]),
            tags=json.loads(row["tags_json"]),
            analysis=analysis,
            scenes=scenes if scenes is not None else [],
            created_at=row["created_at"],
        )

    def get_media_asset(self, media_id: str) -> Optional[MediaAsset]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM media_assets WHERE id = ?", (media_id,)).fetchone()
            if not row:
                return None
            scene_rows = conn.execute(
                "SELECT * FROM detected_scenes WHERE media_id = ? ORDER BY scene_index ASC",
                (media_id,),
            ).fetchall()
            return self._row_to_media(row, [self._row_to_scene(s) for s in scene_rows])

    def list_media_assets(self, media_kind: Optional[str] = None) -> list[MediaAsset]:
        with self._connect() as conn:
            if media_kind:
                rows = conn.execute(
                    "SELECT * FROM media_assets WHERE media_kind = ? ORDER BY created_at DESC",
                    (media_kind,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM media_assets ORDER BY created_at DESC").fetchall()

            all_scenes = conn.execute(
                "SELECT * FROM detected_scenes ORDER BY scene_index ASC"
            ).fetchall()
            scenes_by_media: dict[str, list[DetectedScene]] = {}
            for sr in all_scenes:
                sc = self._row_to_scene(sr)
                scenes_by_media.setdefault(sc.media_id, []).append(sc)

            return [self._row_to_media(r, scenes_by_media.get(r["id"], [])) for r in rows]

    def delete_media_asset(self, media_id: str) -> Optional[MediaAsset]:
        asset = self.get_media_asset(media_id)
        if not asset:
            return None
        with self._connect() as conn:
            conn.execute("DELETE FROM media_assets WHERE id = ?", (media_id,))
        return asset

    # ---- Projects ----

    def _row_to_project(self, row: sqlite3.Row) -> ProjectResponse:
        timeline = TimelinePlan.model_validate_json(row["timeline_json"]) if row["timeline_json"] else None
        return ProjectResponse(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            aspect_ratio=row["aspect_ratio"],
            target_duration_seconds=row["target_duration_seconds"],
            color_grade=row["color_grade"],
            timeline=timeline,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save_project(self, project: ProjectResponse) -> ProjectResponse:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO projects (
                    id, title, description, aspect_ratio, target_duration_seconds,
                    color_grade, timeline_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project.id,
                    project.title,
                    project.description,
                    project.aspect_ratio,
                    project.target_duration_seconds,
                    project.color_grade,
                    project.timeline.model_dump_json() if project.timeline else None,
                    project.created_at,
                    project.updated_at,
                ),
            )
        return project

    def get_project(self, project_id: str) -> Optional[ProjectResponse]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            return self._row_to_project(row) if row else None

    def list_projects(self) -> list[ProjectResponse]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
            return [self._row_to_project(r) for r in rows]

    def delete_project(self, project_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cur.rowcount > 0

    # ---- Render Jobs ----

    def _row_to_job(self, row: sqlite3.Row) -> RenderJobStatus:
        return RenderJobStatus(
            job_id=row["job_id"],
            project_id=row["project_id"],
            status=row["status"],
            progress_percent=row["progress_percent"],
            current_step=row["current_step"],
            resolution=row["resolution"],
            output_video_url=row["output_video_url"],
            output_file_size_bytes=row["output_file_size_bytes"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create_render_job(self, job: RenderJobStatus, output_path: Optional[str] = None) -> RenderJobStatus:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO render_jobs (
                    job_id, project_id, status, progress_percent, current_step,
                    resolution, output_path, output_video_url, output_file_size_bytes,
                    error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.project_id,
                    job.status,
                    job.progress_percent,
                    job.current_step,
                    job.resolution,
                    output_path,
                    job.output_video_url,
                    job.output_file_size_bytes,
                    job.error_message,
                    job.created_at,
                    job.updated_at,
                ),
            )
        return job

    def update_render_job(
        self,
        job_id: str,
        *,
        status: Optional[str] = None,
        progress_percent: Optional[float] = None,
        current_step: Optional[str] = None,
        output_path: Optional[str] = None,
        output_video_url: Optional[str] = None,
        output_file_size_bytes: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[RenderJobStatus]:
        fields: list[str] = []
        values: list[object] = []
        mapping = {
            "status": status,
            "progress_percent": progress_percent,
            "current_step": current_step,
            "output_path": output_path,
            "output_video_url": output_video_url,
            "output_file_size_bytes": output_file_size_bytes,
            "error_message": error_message,
        }
        for col, val in mapping.items():
            if val is not None:
                fields.append(f"{col} = ?")
                values.append(val)
        fields.append("updated_at = ?")
        values.append(utc_now_iso())
        values.append(job_id)

        with self._connect() as conn:
            conn.execute(f"UPDATE render_jobs SET {', '.join(fields)} WHERE job_id = ?", values)
            row = conn.execute("SELECT * FROM render_jobs WHERE job_id = ?", (job_id,)).fetchone()
            return self._row_to_job(row) if row else None

    def get_render_job(self, job_id: str) -> Optional[RenderJobStatus]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM render_jobs WHERE job_id = ?", (job_id,)).fetchone()
            return self._row_to_job(row) if row else None

    def get_render_output_path(self, job_id: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute("SELECT output_path FROM render_jobs WHERE job_id = ?", (job_id,)).fetchone()
            return row["output_path"] if row else None

    def mark_interrupted_jobs(self) -> int:
        """Recover gracefully on backend restart by marking stale active jobs as failed."""
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE render_jobs
                SET status = 'failed',
                    current_step = 'Interrupted by server restart',
                    error_message = 'Render process was interrupted before completion. Please re-run.',
                    updated_at = ?
                WHERE status IN ('queued', 'processing')
                """,
                (utc_now_iso(),),
            )
            return cur.rowcount


_db_instance: Optional[Database] = None


def get_database() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance

