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
    "bleach_bypass",
]

SpeedRampPreset = Literal["none", "fast_to_slow", "slow_to_fast", "ease_in_out"]

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


class AudioAnalysisResult(BaseModel):
    tempo_bpm: float = 0.0
    duration_seconds: float = 0.0
    beat_timestamps: list[float] = Field(default_factory=list)
    downbeat_timestamps: list[float] = Field(default_factory=list)
    energy_peaks: list[float] = Field(default_factory=list)
    waveform_peaks: list[float] = Field(default_factory=list)
    silence_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    analyzed_at: str = Field(default_factory=utc_now_iso)


class MediaAsset(BaseModel):
    id: str
    owner_id: Optional[str] = None
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
    audio_analysis: Optional[AudioAnalysisResult] = None
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
    speed_ramp: SpeedRampPreset = "none"
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


SubtitleStyle = Literal["cinematic_gold_bottom", "bold_center_reel", "subtle_white"]


class SubtitleCue(BaseModel):
    id: str
    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(gt=0.0)
    text: str = Field(min_length=1, max_length=400)
    style: SubtitleStyle = "cinematic_gold_bottom"

    @model_validator(mode="after")
    def validate_cue_times(self) -> "SubtitleCue":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("Subtitle end_seconds must exceed start_seconds")
        return self


class CinematicEffects(BaseModel):
    vignette: bool = False
    film_grain: bool = False
    ken_burns_on_images: bool = True
    audio_ducking: bool = True
    loudness_normalize: bool = True


class TimelinePlan(BaseModel):
    version: str = "1.0"
    project_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=200)
    aspect_ratio: AspectRatio = "16:9"
    target_duration_seconds: float = Field(default=30.0, gt=0.0, le=3600.0)
    fps: int = Field(default=30, ge=15, le=120)
    color_grade: ColorGradePreset = "natural"
    cinematic_effects: CinematicEffects = Field(default_factory=CinematicEffects)
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
    owner_id: Optional[str] = None
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
    partial_cache: bool = True


class RenderJobStatus(BaseModel):
    job_id: str
    project_id: str
    status: JobState
    progress_percent: float = Field(ge=0.0, le=100.0)
    current_step: str
    resolution: ResolutionPreset = "1080p"
    output_video_url: Optional[str] = None
    output_file_size_bytes: Optional[int] = None
    segment_cache_hits: int = 0
    segment_cache_misses: int = 0
    partial_rerender_used: bool = False
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


# ---- Phase 4: AI Director & Storyboard Schemas ----

StoryAct = Literal["Opening Hook", "Rising Action", "Climax", "Emotional Resolution"]
PacingStyle = Literal["dynamic_arc", "fast", "slow"]


class DirectorIntent(BaseModel):
    mood: str = "cinematic"
    theme_keywords: list[str] = Field(default_factory=list)
    target_duration_seconds: float = Field(default=60.0, gt=0.0, le=3600.0)
    aspect_ratio: AspectRatio = "16:9"
    color_grade: ColorGradePreset = "golden_hour"
    pacing: PacingStyle = "dynamic_arc"
    intro_style: Literal["slow_dramatic", "punchy_hook", "standard"] = "standard"
    climax_keywords: list[str] = Field(default_factory=list)
    outro_style: Literal["emotional", "upbeat", "standard"] = "standard"
    title_suggestion: str = "Cinematic Story"


class StoryboardBeat(BaseModel):
    beat_index: int
    act: StoryAct
    clip_id: str
    source_id: str
    title: str
    start_time_seconds: float = Field(ge=0.0)
    end_time_seconds: float = Field(gt=0.0)
    duration_seconds: float = Field(gt=0.0)
    playback_speed: float = Field(default=1.0, ge=0.25, le=4.0)
    transition_in: TransitionType = "crossfade"
    rationale: str


class DirectorPlanRequest(BaseModel):
    project_id: str = Field(default="proj_ai_01", min_length=1, max_length=128)
    instruction: str = Field(min_length=3, max_length=2000)
    media_ids: Optional[list[str]] = None
    target_duration_seconds: Optional[float] = Field(default=None, gt=0.0, le=3600.0)
    aspect_ratio: Optional[AspectRatio] = None
    use_llm: bool = True
    beat_sync: bool = True
    style_recipe_id: Optional[str] = None


class DirectorPlanResponse(BaseModel):
    engine_used: Literal["ollama", "rule_fallback"]
    intent: DirectorIntent
    storyboard: list[StoryboardBeat]
    timeline: TimelinePlan
    warnings: list[str] = Field(default_factory=list)


class DirectorStatusResponse(BaseModel):
    ollama_available: bool
    ollama_url: str
    configured_model: str
    available_models: list[str] = Field(default_factory=list)
    fallback_ready: bool = True


# ---- Phase 5: Audio Beat-Sync Schemas ----


class BeatSyncRequest(BaseModel):
    timeline: TimelinePlan
    audio_source_id: str = Field(min_length=1, max_length=128)
    tolerance_seconds: float = Field(default=0.35, ge=0.05, le=1.5)


class BeatSyncResponse(BaseModel):
    timeline: TimelinePlan
    tempo_bpm: float
    snapped_cuts: int
    beat_timestamps_used: list[float] = Field(default_factory=list)


# ---- Phase 6: Voice, Speech-to-Text & Conversational Editing Schemas ----


class TranscriptWord(BaseModel):
    word: str
    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(ge=0.0)
    probability: float = Field(default=1.0, ge=0.0, le=1.0)


class TranscriptSegment(BaseModel):
    id: str
    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(gt=0.0)
    text: str
    words: list[TranscriptWord] = Field(default_factory=list)


class WhisperStatusResponse(BaseModel):
    package_installed: bool
    model_name: str
    device: str
    compute_type: str
    model_cached: bool
    ready: bool
    ffmpeg_ready: bool
    detail: str = ""


class TranscriptionResponse(BaseModel):
    text: str
    language: str = "en"
    duration_seconds: float = 0.0
    engine: Literal["faster_whisper", "custom"] = "faster_whisper"
    segments: list[TranscriptSegment] = Field(default_factory=list)
    suggested_subtitles: list[SubtitleCue] = Field(default_factory=list)


class TimelineDiffSummary(BaseModel):
    added_clip_ids: list[str] = Field(default_factory=list)
    removed_clip_ids: list[str] = Field(default_factory=list)
    modified_clip_ids: list[str] = Field(default_factory=list)
    shifted_clip_ids: list[str] = Field(default_factory=list)
    unchanged_clip_ids: list[str] = Field(default_factory=list)
    global_visual_changed: bool = False
    subtitles_changed: bool = False
    audio_changed: bool = False
    affected_segment_indices: list[int] = Field(default_factory=list)
    changes: list[str] = Field(default_factory=list)


class ConversationalEditRequest(BaseModel):
    project_id: str = Field(default="proj_studio_01", min_length=1, max_length=128)
    instruction: str = Field(min_length=2, max_length=2000)
    timeline: TimelinePlan
    use_llm: bool = True
    record_history: bool = True


class ConversationalEditResponse(BaseModel):
    engine_used: Literal["ollama", "rule_fallback"]
    instruction: str
    timeline: TimelinePlan
    diff: TimelineDiffSummary
    operations_applied: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    revision_index: int = 0
    history_count: int = 0
    can_undo: bool = False
    can_redo: bool = False


class TimelineRevisionRecord(BaseModel):
    revision_id: str
    project_id: str
    revision_index: int
    command_text: str
    diff_summary: TimelineDiffSummary
    timeline: TimelinePlan
    created_at: str


class ProjectHistoryResponse(BaseModel):
    project_id: str
    active_revision_index: int
    total_revisions: int
    can_undo: bool
    can_redo: bool
    timeline: Optional[TimelinePlan] = None
    revisions: list[TimelineRevisionRecord] = Field(default_factory=list)


# ---- Phase 7: Trend Intelligence & Original Style Recipe Schemas ----

StyleRecipeSourceType = Literal["builtin", "uploaded_reference", "url_pattern"]
MotionProfile = Literal["static", "smooth_glide", "dynamic_burst", "high_velocity"]
CutCadence = Literal["rapid", "moderate", "deliberate"]


class TrendSafetyAudit(BaseModel):
    copyright_safe: bool = True
    media_downloaded: bool = False
    private_scraping_blocked: bool = True
    raw_frames_retained: bool = False
    compliance_note: str = (
        "Extracts abstract mathematical editing parameters only; zero source frames or copyrighted streams retained."
    )


class StyleRecipe(BaseModel):
    id: str
    name: str = Field(min_length=2, max_length=160)
    description: str = ""
    source_type: StyleRecipeSourceType = "builtin"
    is_builtin: bool = False
    reference_label: Optional[str] = None
    cuts_per_minute: float = Field(ge=0.0, default=18.0)
    avg_shot_duration_seconds: float = Field(gt=0.1, default=3.2)
    cut_cadence: CutCadence = "moderate"
    motion_velocity_score: float = Field(ge=0.0, le=100.0, default=55.0)
    motion_profile: MotionProfile = "smooth_glide"
    color_mood: str = "balanced"
    recommended_color_grade: ColorGradePreset = "golden_hour"
    recommended_aspect_ratio: AspectRatio = "16:9"
    recommended_pacing: PacingStyle = "dynamic_arc"
    recommended_speed_ramp: SpeedRampPreset = "none"
    recommended_transition: TransitionType = "crossfade"
    cinematic_effects: CinematicEffects = Field(default_factory=CinematicEffects)
    dominant_palette: list[str] = Field(default_factory=list)
    energy_arc: list[str] = Field(default_factory=lambda: ["Opening Hook", "Rising Action", "Climax", "Emotional Resolution"])
    prompt_hint: str = ""
    safety_audit: TrendSafetyAudit = Field(default_factory=TrendSafetyAudit)
    created_at: str = Field(default_factory=utc_now_iso)


class StyleAnalyzeUrlRequest(BaseModel):
    reference_url: str = Field(min_length=4, max_length=2000)
    recipe_name: Optional[str] = Field(default=None, max_length=160)
    style_notes: str = Field(default="", max_length=1000)


class StyleApplyRequest(BaseModel):
    project_id: str = Field(default="proj_studio_01", min_length=1, max_length=128)
    timeline: TimelinePlan
    record_history: bool = True


class StyleApplyResponse(BaseModel):
    recipe: StyleRecipe
    timeline: TimelinePlan
    diff: TimelineDiffSummary
    changes_applied: list[str] = Field(default_factory=list)
    revision_index: int = 0
    history_count: int = 0
    can_undo: bool = False
    can_redo: bool = False


# ---- Phase 8: Institutional Campus Auth, Quotas, Cleanup & Admin Schemas ----

UserRole = Literal["student", "club_lead", "admin"]


class UserPublic(BaseModel):
    id: str
    full_name: str
    email: str
    department: str = "Computer Science & Engineering"
    role: UserRole = "student"
    storage_quota_bytes: int
    used_storage_bytes: int = 0
    is_active: bool = True
    created_at: str


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=180)
    password: str = Field(min_length=6, max_length=128)
    department: str = Field(default="Computer Science & Engineering", max_length=120)
    role: UserRole = "student"


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=180)
    password: str = Field(min_length=1, max_length=128)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in_seconds: int
    user: UserPublic


class QuotaStatusResponse(BaseModel):
    user_id: str
    email: str
    used_bytes: int
    quota_bytes: int
    remaining_bytes: int
    percent_used: float


class AdminUserRecord(BaseModel):
    id: str
    full_name: str
    email: str
    department: str
    role: UserRole
    storage_quota_bytes: int
    used_storage_bytes: int
    projects_count: int
    is_active: bool
    created_at: str


class AdminUserUpdateRequest(BaseModel):
    storage_quota_gb: Optional[float] = Field(default=None, ge=0.001, le=2000.0)
    storage_quota_bytes: Optional[int] = Field(default=None, ge=1024)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class DirectoryStorageBreakdown(BaseModel):
    uploads_bytes: int
    proxies_bytes: int
    renders_bytes: int
    cache_bytes: int
    segment_cache_bytes: int
    total_managed_bytes: int


class SystemResourceTelemetry(BaseModel):
    cpu_percent: float
    cpu_cores: int
    memory_used_gb: float
    memory_total_gb: float
    memory_percent: float
    disk_free_gb: float
    disk_total_gb: float
    hardware_encoder: str


class AdminOverviewResponse(BaseModel):
    system: SystemResourceTelemetry
    storage: DirectoryStorageBreakdown
    active_users_count: int
    total_users_count: int
    total_projects_count: int
    total_media_assets_count: int
    render_queue: dict[str, int]
    database_engine: str


class CleanupRequest(BaseModel):
    purge_cache: bool = True
    purge_expired_renders: bool = True
    max_age_hours: int = Field(default=24, ge=0, le=8760)


class CleanupResponse(BaseModel):
    files_removed: int
    freed_bytes: int
    post_cleanup_storage: DirectoryStorageBreakdown
    executed_at: str = Field(default_factory=utc_now_iso)


class MigrationStatusResponse(BaseModel):
    active_engine: str
    configured_database_url: str
    schema_version: str
    postgres_ddl_ready: bool
    table_counts: dict[str, int]
    postgres_migration_cli: str = "backend\\.venv\\Scripts\\python.exe -m backend.migrations.sqlite_to_postgres --dry-run"


# ---- Phase 9: Benchmarking & Hackathon Showcase Schemas ----


class BenchmarkStageResult(BaseModel):
    stage_id: str
    stage_name: str
    duration_seconds: float
    throughput_label: str
    cpu_percent_avg: float = 0.0
    memory_rss_mb: float = 0.0
    notes: str = ""


class ShowcaseBenchmarkReport(BaseModel):
    generated_at: str = Field(default_factory=utc_now_iso)
    host_os: str
    python_version: str
    cpu_cores: int
    ram_total_gb: float
    ffmpeg_version: str
    hardware_profile: HardwareProfileInfo
    stages: list[BenchmarkStageResult]
    cold_render_seconds: float
    warm_cached_render_seconds: float
    cache_speedup_percent: float
    segment_cache_hits: int
    segment_cache_misses: int
    output_duration_seconds: float
    realtime_speedup_x: float
    portrait_render_seconds: float
    output_file_bytes: int


class ShowcaseSampleFileInfo(BaseModel):
    filename: str
    media_kind: Literal["video", "image", "audio"]
    size_bytes: int
    resolution_label: str
    duration_seconds: float
    role: str


class ShowcaseStatusResponse(BaseModel):
    showcase_project_id: str
    project_loaded: bool
    sample_pack_ready: bool
    sample_files: list[ShowcaseSampleFileInfo]
    total_sample_bytes: int
    benchmark_report_ready: bool
    last_benchmark_at: Optional[str] = None
    hardware: HardwareProfileInfo


class ShowcaseLoadRequest(BaseModel):
    force_reset: bool = False


class ShowcaseLoadResponse(BaseModel):
    project: ProjectResponse
    assets: list[MediaAsset]
    audio_asset_id: Optional[str] = None
    newly_ingested: bool
    total_sample_bytes: int
    message: str

