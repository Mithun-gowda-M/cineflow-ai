"""Pydantic v2 contracts shared across CINEFLOW AI backend services."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.api.config import utc_now_iso

AspectRatio = Literal["16:9", "9:16", "1:1", "4:5", "21:9"]

TransitionType = Literal[
    "none",
    "crossfade",
    "fade_from_black",
    "fade_to_black",
    "slide_left",
    "slide_right",
    "wipe_left",
    "wipe_right",
    "zoom_in",
    "zoom_out",
]

ColorGradePreset = Literal[
    "natural",
    "cinematic_teal_orange",
    "golden_hour",
    "moody_dark",
    "vintage_film",
    "high_contrast_bw",
]

MediaKind = Literal["video", "image", "audio"]
ResolutionPreset = Literal["540p", "720p", "1080p", "4k"]
JobState = Literal["queued", "processing", "completed", "failed", "cancelled"]


class TransitionSpec(BaseModel):
    type: TransitionType = "none"
    duration_seconds: float = Field(default=0.5, ge=0.0, le=5.0)


class MediaMetadata(BaseModel):
    width: int = 0
    height: int = 0
    fps: float = 0.0
    duration_seconds: float = 0.0
    codec: str = ""
    audio_codec: Optional[str] = None
    has_audio: bool = False
    audio_channels: int = 0
    sample_rate: int = 0
    bitrate_kbps: int = 0
    aspect_ratio: str = "16:9"
    rotation: int = 0


class QualityBreakdown(BaseModel):
    sharpness_score: float = Field(ge=0.0, le=100.0)
    exposure_score: float = Field(ge=0.0, le=100.0)
    stability_score: float = Field(ge=0.0, le=100.0)
    composition_score: float = Field(ge=0.0, le=100.0)
    laplacian_variance: float = 0.0
    mean_luminance: float = 0.0
    motion_intensity: Literal["static", "smooth", "action", "shaky"] = "static"
    lighting_mood: Literal["bright", "warm_golden", "balanced", "low_light"] = "balanced"
    face_count: int = 0
    subject_position: Literal["center", "rule_of_thirds", "wide", "none"] = "none"
    dominant_colors: list[str] = Field(default_factory=list)
    overall_score: float = Field(ge=0.0, le=100.0)
    explanation: str = ""


class DetectedScene(BaseModel):
    scene_id: str
    media_id: str
    scene_index: int
    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(gt=0.0)
    duration_seconds: float = Field(gt=0.0)
    thumbnail_url: Optional[str] = None
    quality_score: float = Field(default=75.0, ge=0.0, le=100.0)
    sharpness_score: float = Field(default=75.0, ge=0.0, le=100.0)
    motion_level: Literal["static", "smooth", "action", "shaky"] = "static"
    tags: list[str] = Field(default_factory=list)


class MediaAnalysisResult(BaseModel):
    quality: QualityBreakdown
    semantic_tags: list[str] = Field(default_factory=list)
    perceptual_hash: str = ""
    duplicate_of_id: Optional[str] = None
    similarity_percent: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    analyzed_at: str = Field(default_factory=utc_now_iso)


class MediaAsset(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    media_kind: MediaKind
    mime_type: str
    file_size_bytes: int
    file_path: str
    source_url: str
    thumbnail_url: Optional[str] = None
    proxy_url: Optional[str] = None
    proxy_path: Optional[str] = None
    metadata: MediaMetadata
    tags: list[str] = Field(default_factory=list)
    analysis: Optional[MediaAnalysisResult] = None
    scenes: list[DetectedScene] = Field(default_factory=list)
    created_at: str


class MediaSearchResponse(BaseModel):
    query: str
    total_matches: int
    results: list[MediaAsset]


class MediaUploadResponse(BaseModel):
    uploaded: list[MediaAsset]
    errors: list[dict[str, str]] = Field(default_factory=list)


class MediaClip(BaseModel):
    clip_id: str = Field(min_length=1, max_length=128)
    source_id: str = Field(min_length=1, max_length=128)
    source_filename: str = ""
    source_url: str = ""
    thumbnail_url: Optional[str] = None
    start_time_seconds: float = Field(default=0.0, ge=0.0)
    end_time_seconds: float = Field(default=4.0, gt=0.0)
    timeline_start_seconds: float = Field(default=0.0, ge=0.0)
    duration_seconds: float = Field(default=4.0, gt=0.0, le=1800.0)
    playback_speed: float = Field(default=1.0, ge=0.25, le=4.0)
    transition_in: Optional[TransitionSpec] = None
    transition_out: Optional[TransitionSpec] = None
    color_grade: Optional[ColorGradePreset] = None
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_trim_bounds(self) -> "MediaClip":
        if self.end_time_seconds <= self.start_time_seconds:
            raise ValueError("end_time_seconds must be strictly greater than start_time_seconds")
        return self


class AudioTrackCue(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = "Soundtrack"
    source_id: str = Field(min_length=1, max_length=128)
    source_url: str = ""
    volume: float = Field(default=0.8, ge=0.0, le=2.0)
    start_time_seconds: float = Field(default=0.0, ge=0.0)
    timeline_start_seconds: float = Field(default=0.0, ge=0.0)
    duration_seconds: float = Field(default=10.0, gt=0.0)
    ducking_enabled: bool = True
    duck_volume: float = Field(default=0.25, ge=0.0, le=1.0)


class SubtitleCue(BaseModel):
    id: str
    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(gt=0.0)
    text: str = Field(min_length=1, max_length=400)
    style: Literal["cinematic_gold_bottom", "bold_center_reel", "subtle_white"] = "cinematic_gold_bottom"

    @model_validator(mode="after")
    def validate_cue_times(self) -> "SubtitleCue":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("Subtitle end_seconds must exceed start_seconds")
        return self


class TimelinePlan(BaseModel):
    version: str = "1.0"
    project_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=200)
    aspect_ratio: AspectRatio = "16:9"
    target_duration_seconds: float = Field(default=30.0, gt=0.0, le=3600.0)
    fps: int = Field(default=30, ge=15, le=120)
    color_grade: ColorGradePreset = "natural"
    video_clips: list[MediaClip] = Field(min_length=1)
    audio_tracks: list[AudioTrackCue] = Field(default_factory=list)
    subtitles: list[SubtitleCue] = Field(default_factory=list)


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    aspect_ratio: AspectRatio = "16:9"
    target_duration_seconds: float = Field(default=120.0, gt=0.0, le=3600.0)
    color_grade: ColorGradePreset = "golden_hour"


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    aspect_ratio: Optional[AspectRatio] = None
    target_duration_seconds: Optional[float] = Field(default=None, gt=0.0, le=3600.0)
    color_grade: Optional[ColorGradePreset] = None
    timeline: Optional[TimelinePlan] = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    description: str = ""
    aspect_ratio: AspectRatio
    target_duration_seconds: float
    color_grade: ColorGradePreset
    timeline: Optional[TimelinePlan] = None
    created_at: str
    updated_at: str


class RenderRequest(BaseModel):
    timeline: TimelinePlan
    resolution: ResolutionPreset = "1080p"
    encoder_preference: Literal["auto", "cpu", "nvenc", "qsv", "amf"] = "auto"


class RenderJobStatus(BaseModel):
    job_id: str
    project_id: str
    status: JobState
    progress_percent: float = Field(ge=0.0, le=100.0)
    current_step: str
    resolution: ResolutionPreset = "1080p"
    output_video_url: Optional[str] = None
    output_file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class HardwareProfileInfo(BaseModel):
    profile: Literal["low", "medium", "high"]
    cpu_cores: int
    free_disk_gb: float
    video_encoder: str
    hw_accel_available: bool
    detected_encoders: list[str]
    max_concurrent_renders: int


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    app_name: str
    ffmpeg_available: bool
    ffprobe_available: bool
    ffmpeg_version: Optional[str] = None
    ffprobe_version: Optional[str] = None
    hardware: HardwareProfileInfo
    timestamp: str = Field(default_factory=utc_now_iso)

