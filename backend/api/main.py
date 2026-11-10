"""FastAPI application entrypoint for CINEFLOW AI."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.config import get_settings
from backend.api.database import get_database
from backend.api.routes_audio import router as audio_router
from backend.api.routes_director import router as director_router
from backend.api.routes_media import router as media_router
from backend.api.routes_projects import router as projects_router
from backend.api.routes_render import router as render_router
from backend.api.schemas import HardwareProfileInfo, HealthResponse
from backend.video_engine.ffmpeg_runner import get_binary_info
from backend.video_engine.hardware import detect_hardware_profile


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.ensure_directories()
    db = get_database()
    db.mark_interrupted_jobs()
    detect_hardware_profile()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    settings.ensure_directories()

    app = FastAPI(
        title=settings.APP_NAME,
        version="2.0.0",
        description="Local-first AI video analysis and FFmpeg rendering platform.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static media mounts for uploaded sources, 720p proxies/thumbnails, and completed renders
    app.mount("/static/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")
    app.mount("/static/proxies", StaticFiles(directory=str(settings.PROXY_DIR)), name="proxies")
    app.mount("/static/renders", StaticFiles(directory=str(settings.RENDER_DIR)), name="renders")

    api_prefix = f"/api/{settings.API_VERSION}"
    app.include_router(media_router, prefix=api_prefix)
    app.include_router(audio_router, prefix=api_prefix)
    app.include_router(projects_router, prefix=api_prefix)
    app.include_router(render_router, prefix=api_prefix)
    app.include_router(director_router, prefix=api_prefix)

    @app.get(f"{api_prefix}/health", response_model=HealthResponse, tags=["System"])
    def health_check() -> HealthResponse:
        bins = get_binary_info()
        hw = detect_hardware_profile()
        ffmpeg_ok = bool(bins["ffmpeg_path"])
        ffprobe_ok = bool(bins["ffprobe_path"])

        return HealthResponse(
            status="ok" if (ffmpeg_ok and ffprobe_ok) else "degraded",
            app_name=settings.APP_NAME,
            ffmpeg_available=ffmpeg_ok,
            ffprobe_available=ffprobe_ok,
            ffmpeg_version=bins["ffmpeg_version"],
            ffprobe_version=bins["ffprobe_version"],
            hardware=HardwareProfileInfo(
                profile=hw.profile,
                cpu_cores=hw.cpu_cores,
                free_disk_gb=hw.free_disk_gb,
                video_encoder=hw.video_encoder,
                hw_accel_available=hw.hw_accel_available,
                detected_encoders=list(hw.detected_encoders),
                max_concurrent_renders=hw.max_concurrent_renders,
            ),
        )

    return app


app = create_app()

