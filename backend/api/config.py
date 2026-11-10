"""Centralized configuration for CINEFLOW AI backend services."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp without deprecated `utcnow()`."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds") + "Z"


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "CINEFLOW AI Backend"
    API_VERSION: str = "v1"
    ENVIRONMENT: str = "development"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    SECRET_KEY: str = "dev-local-cineflow-secret-key-change-in-production"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    HARDWARE_PROFILE: Literal["auto", "low", "medium", "high"] = "auto"
    MAX_CONCURRENT_RENDERS: int = 2
    PROXY_RESOLUTION: str = "720p"

    # Storage paths (resolved relative to repository root when relative)
    BASE_DIR: Path = Field(default_factory=_default_repo_root)
    DATA_DIR: Path = Field(default_factory=lambda: _default_repo_root() / "data")
    UPLOAD_DIR: Path = Field(default_factory=lambda: _default_repo_root() / "data" / "uploads")
    PROXY_DIR: Path = Field(default_factory=lambda: _default_repo_root() / "data" / "proxies")
    RENDER_DIR: Path = Field(default_factory=lambda: _default_repo_root() / "data" / "renders")
    CACHE_DIR: Path = Field(default_factory=lambda: _default_repo_root() / "data" / "cache")
    PROJECTS_DIR: Path = Field(default_factory=lambda: _default_repo_root() / "data" / "projects")
    DATABASE_PATH: Path = Field(default_factory=lambda: _default_repo_root() / "data" / "cineflow.db")

    # Security & upload limits
    MAX_UPLOAD_FILE_MB: int = 512
    MAX_BATCH_FILES: int = 50
    USER_STORAGE_QUOTA_GB: float = 25.0

    # External binaries (optional overrides)
    FFMPEG_PATH: str = ""
    FFPROBE_PATH: str = ""

    # Local AI Director (Ollama - free & open-source)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    OLLAMA_TIMEOUT_SECONDS: float = 12.0

    # Local Speech-to-Text (faster-whisper - CPU INT8 offline)
    WHISPER_MODEL: str = "tiny"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_LOCAL_FILES_ONLY: bool = False

    # Partial Segment Render Caching
    MAX_SEGMENT_CACHE_MB: int = 1024

    # Phase 8: Institutional Campus Deployment, Auth & Quotas
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720
    RESTRICT_COLLEGE_EMAIL_DOMAIN: bool = False
    ALLOWED_AUTH_DOMAINS: str = "bmsit.in,bmsit.ac.in"
    REQUIRE_AUTH_FOR_MEDIA: bool = False
    CACHE_TTL_HOURS: int = 24
    DATABASE_URL: str = "sqlite:///./data/cineflow.db"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    def ensure_directories(self) -> None:
        """Create required local storage folders if they do not exist."""
        for folder in (
            self.DATA_DIR,
            self.UPLOAD_DIR,
            self.PROXY_DIR,
            self.RENDER_DIR,
            self.CACHE_DIR,
            self.CACHE_DIR / "segments",
            self.PROJECTS_DIR,
            self.DATABASE_PATH.parent,
        ):
            folder.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings

