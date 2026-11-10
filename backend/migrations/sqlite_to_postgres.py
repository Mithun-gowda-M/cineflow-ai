"""CLI and helper utility for SQLite -> PostgreSQL schema verification and data migration."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Optional

from backend.api.config import get_settings
from backend.api.database import Database

REQUIRED_TABLES = (
    "users",
    "media_assets",
    "detected_scenes",
    "projects",
    "render_jobs",
    "timeline_revisions",
    "style_recipes",
)


def extract_postgres_ddl_tables(ddl_path: Path) -> set[str]:
    text = ddl_path.read_text(encoding="utf-8")
    return set(re.findall(r"CREATE TABLE IF NOT EXISTS\s+([a-zA-Z_][a-zA-Z0-9_]*)", text))


def inspect_sqlite_for_migration(sqlite_path: Path, ddl_path: Path) -> dict:
    db = Database(sqlite_path)
    counts = db.get_schema_table_counts()
    ddl_tables = extract_postgres_ddl_tables(ddl_path)
    missing_in_ddl = [t for t in REQUIRED_TABLES if t not in ddl_tables]
    return {
        "sqlite_path": str(sqlite_path),
        "ddl_path": str(ddl_path),
        "ddl_tables_verified": len(missing_in_ddl) == 0,
        "missing_ddl_tables": missing_in_ddl,
        "sqlite_table_counts": counts,
    }


def migrate_sqlite_to_postgres(
    sqlite_path: Path,
    *,
    pg_url: Optional[str] = None,
    ddl_path: Optional[Path] = None,
    dry_run: bool = True,
) -> dict:
    """Verify SQLite parity against Postgres DDL, or copy rows cleanly into PostgreSQL."""
    resolved_ddl = ddl_path or (Path(__file__).resolve().parent / "001_postgres_initial.sql")
    report = inspect_sqlite_for_migration(sqlite_path, resolved_ddl)
    if not report["ddl_tables_verified"]:
        raise RuntimeError(f"PostgreSQL DDL is missing required tables: {report['missing_ddl_tables']}")

    if dry_run:
        report["mode"] = "dry_run"
        report["copied_rows"] = {}
        return report

    if not pg_url or not pg_url.lower().startswith("postgres"):
        raise ValueError("A valid PostgreSQL DSN (`postgresql://...`) is required unless --dry-run is set.")

    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Install `psycopg[binary]` (`pip install psycopg[binary]`) to execute live SQLite -> PostgreSQL copy."
        ) from exc

    ddl_sql = resolved_ddl.read_text(encoding="utf-8")
    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_conn.row_factory = sqlite3.Row
    copied: dict[str, int] = {}

    try:
        with psycopg.connect(pg_url) as pg_conn:
            with pg_conn.cursor() as cur:
                cur.execute(ddl_sql)
                for table in REQUIRED_TABLES:
                    rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
                    if not rows:
                        copied[table] = 0
                        continue
                    cols = list(rows[0].keys())
                    placeholders = ", ".join(["%s"] * len(cols))
                    col_list = ", ".join(cols)
                    insert_sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                    for r in rows:
                        cur.execute(insert_sql, tuple(r[c] for c in cols))
                    copied[table] = len(rows)
            pg_conn.commit()
    finally:
        sqlite_conn.close()

    report["mode"] = "executed"
    report["copied_rows"] = copied
    return report


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate CINEFLOW SQLite database to PostgreSQL 15+.")
    parser.add_argument("--sqlite-path", type=Path, default=get_settings().DATABASE_PATH)
    parser.add_argument("--pg-url", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Inspect schema parity without copying.")
    args = parser.parse_args(argv)

    result = migrate_sqlite_to_postgres(
        args.sqlite_path,
        pg_url=args.pg_url,
        dry_run=args.dry_run or (args.pg_url is None),
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

