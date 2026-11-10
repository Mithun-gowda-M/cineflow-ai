import type {
  AspectRatio,
  CinematicEffects,
  ColorGradePreset,
  SpeedRampPreset,
  SubtitleCue,
  TimelineClip,
} from "@/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const BACKEND_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, "");

export function resolveBackendUrl(path?: string | null): string {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${BACKEND_ORIGIN}${path.startsWith("/") ? "" : "/"}${path}`;
}

export interface BackendMediaMetadata {
  width: number;
  height: number;
  fps: number;
  duration_seconds: number;
  codec: string;
  audio_codec?: string | null;
  has_audio: boolean;
  audio_channels: number;
  sample_rate: number;
  bitrate_kbps: number;
  aspect_ratio: string;
  rotation: number;
}

export interface BackendQualityBreakdown {
  sharpness_score: number;
  exposure_score: number;
  stability_score: number;
  composition_score: number;
  laplacian_variance: number;
  mean_luminance: number;
  motion_intensity: "static" | "smooth" | "action" | "shaky";
  lighting_mood: "bright" | "warm_golden" | "balanced" | "low_light";
  face_count: number;
  subject_position: string;
  dominant_colors: string[];
  overall_score: number;
  explanation: string;
}

export interface BackendDetectedScene {
  scene_id: string;
  media_id: string;
  scene_index: number;
  start_seconds: number;
  end_seconds: number;
  duration_seconds: number;
  thumbnail_url?: string | null;
  quality_score: number;
  sharpness_score: number;
  motion_level: "static" | "smooth" | "action" | "shaky";
  tags: string[];
}

export interface BackendMediaAnalysis {
  quality: BackendQualityBreakdown;
  semantic_tags: string[];
  perceptual_hash: string;
  duplicate_of_id?: string | null;
  similarity_percent?: number | null;
  analyzed_at: string;
}

export interface BackendAudioAnalysis {
  tempo_bpm: number;
  duration_seconds: number;
  beat_timestamps: number[];
  downbeat_timestamps: number[];
  energy_peaks: number[];
  waveform_peaks: number[];
  silence_ratio: number;
  analyzed_at: string;
}

export interface BackendMediaAsset {
  id: string;
  original_filename: string;
  stored_filename: string;
  media_kind: "video" | "image" | "audio";
  mime_type: string;
  file_size_bytes: number;
  source_url: string;
  thumbnail_url?: string | null;
  proxy_url?: string | null;
  metadata: BackendMediaMetadata;
  tags: string[];
  analysis?: BackendMediaAnalysis | null;
  audio_analysis?: BackendAudioAnalysis | null;
  scenes?: BackendDetectedScene[];
  created_at: string;
}

export interface BackendHealth {
  status: "ok" | "degraded";
  app_name: string;
  ffmpeg_available: boolean;
  ffprobe_available: boolean;
  ffmpeg_version?: string | null;
  hardware: {
    profile: "low" | "medium" | "high";
    cpu_cores: number;
    free_disk_gb: number;
    video_encoder: string;
    hw_accel_available: boolean;
  };
}

export interface BackendRenderJob {
  job_id: string;
  project_id: string;
  status: "queued" | "processing" | "completed" | "failed" | "cancelled";
  progress_percent: number;
  current_step: string;
  resolution: string;
  output_video_url?: string | null;
  output_file_size_bytes?: number | null;
  segment_cache_hits?: number;
  segment_cache_misses?: number;
  partial_rerender_used?: boolean;
  error_message?: string | null;
}

export async function checkBackendHealth(): Promise<BackendHealth | null> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${API_BASE_URL}/health`, { signal: controller.signal });
    clearTimeout(timer);
    if (!res.ok) return null;
    return (await res.json()) as BackendHealth;
  } catch {
    return null;
  }
}

export async function listMediaAssets(): Promise<BackendMediaAsset[]> {
  const res = await fetch(`${API_BASE_URL}/media`);
  if (!res.ok) throw new Error(`Failed to fetch media library (${res.status})`);
  return (await res.json()) as BackendMediaAsset[];
}

export async function searchMediaAssets(params: {
  q?: string;
  tag?: string;
  minQuality?: number;
  excludeDuplicates?: boolean;
}): Promise<{ query: string; total_matches: number; results: BackendMediaAsset[] }> {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.tag && params.tag !== "all") qs.set("tag", params.tag);
  if (params.minQuality !== undefined) qs.set("min_quality", String(params.minQuality));
  if (params.excludeDuplicates) qs.set("exclude_duplicates", "true");
  const res = await fetch(`${API_BASE_URL}/media/search?${qs.toString()}`);
  if (!res.ok) throw new Error(`Search failed (${res.status})`);
  return await res.json();
}

export async function analyzeAllMedia(): Promise<BackendMediaAsset[]> {
  const res = await fetch(`${API_BASE_URL}/media/analyze-all`, { method: "POST" });
  if (!res.ok) throw new Error(`Analysis failed (${res.status})`);
  return (await res.json()) as BackendMediaAsset[];
}

export async function uploadMediaBatch(
  files: File[]
): Promise<{ uploaded: BackendMediaAsset[]; errors: { filename: string; error: string }[] }> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const res = await fetch(`${API_BASE_URL}/media/upload`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Upload failed (${res.status})`);
  }
  return await res.json();
}

export async function deleteMediaAsset(mediaId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/media/${encodeURIComponent(mediaId)}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(`Delete failed (${res.status})`);
}

function serializeTimelinePayload(params: {
  projectId: string;
  title: string;
  aspectRatio: AspectRatio;
  colorGrade: ColorGradePreset;
  clips: TimelineClip[];
  subtitles?: SubtitleCue[];
  cinematicEffects?: CinematicEffects;
}) {
  const videoClips = params.clips
    .filter((c) => (c.trackId === "v1" || c.trackId === "v2") && Boolean(c.sourceId))
    .map((c) => ({
      clip_id: c.id,
      source_id: c.sourceId!,
      source_filename: c.title,
      source_url: c.sourceUrl,
      thumbnail_url: c.thumbnailUrl,
      start_time_seconds: Math.max(0, c.trimStart),
      end_time_seconds: Math.max(c.trimStart + 0.2, c.trimEnd || c.trimStart + c.duration),
      timeline_start_seconds: Math.max(0, c.startTime),
      duration_seconds: Math.max(0.2, c.duration),
      playback_speed: c.speed || 1.0,
      speed_ramp: c.speedRamp || "none",
      transition_in: c.transition && c.transition !== "none" ? { type: c.transition, duration_seconds: 0.5 } : null,
      color_grade: c.colorGrade || null,
      tags: c.tags || [],
    }));

  const audioTracks = params.clips
    .filter((c) => c.trackId === "a2" && Boolean(c.sourceId))
    .map((c) => ({
      id: c.id,
      name: c.title,
      source_id: c.sourceId!,
      source_url: c.sourceUrl,
      volume: 0.85,
      start_time_seconds: Math.max(0, c.trimStart),
      timeline_start_seconds: Math.max(0, c.startTime),
      duration_seconds: Math.max(0.5, c.duration),
      ducking_enabled: params.cinematicEffects ? params.cinematicEffects.audioDucking : true,
      duck_volume: 0.35,
    }));

  const subtitles = (params.subtitles || []).map((s) => ({
    id: s.id,
    start_seconds: Math.max(0, s.startTime),
    end_seconds: Math.max(s.startTime + 0.5, s.startTime + s.duration),
    text: s.text,
    style: s.style,
  }));

  const totalDuration = videoClips.reduce((acc, c) => acc + c.duration_seconds / c.playback_speed, 0);

  return {
    version: "1.0",
    project_id: params.projectId,
    title: params.title,
    aspect_ratio: params.aspectRatio,
    target_duration_seconds: Math.max(1, totalDuration),
    fps: 30,
    color_grade: params.colorGrade,
    cinematic_effects: params.cinematicEffects
      ? {
          vignette: params.cinematicEffects.vignette,
          film_grain: params.cinematicEffects.filmGrain,
          ken_burns_on_images: params.cinematicEffects.kenBurnsOnImages,
          audio_ducking: params.cinematicEffects.audioDucking,
          loudness_normalize: params.cinematicEffects.loudnessNormalize,
        }
      : undefined,
    video_clips: videoClips,
    audio_tracks: audioTracks,
    subtitles,
  };
}

export async function submitRenderJob(params: {
  projectId: string;
  title: string;
  aspectRatio: AspectRatio;
  colorGrade: ColorGradePreset;
  clips: TimelineClip[];
  subtitles?: SubtitleCue[];
  cinematicEffects?: CinematicEffects;
  resolution: "720p" | "1080p" | "4k";
  encoderPreference: "auto" | "cpu" | "nvenc" | "qsv" | "amf";
  partialCache?: boolean;
}): Promise<BackendRenderJob> {
  const res = await fetch(`${API_BASE_URL}/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resolution: params.resolution,
      encoder_preference: params.encoderPreference,
      partial_cache: params.partialCache ?? true,
      timeline: serializeTimelinePayload(params),
    }),
  });

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Render submission failed (${res.status})`);
  }
  return (await res.json()) as BackendRenderJob;
}

export async function pollRenderStatus(jobId: string): Promise<BackendRenderJob> {
  const res = await fetch(`${API_BASE_URL}/render/${encodeURIComponent(jobId)}`);
  if (!res.ok) throw new Error(`Failed to poll render job (${res.status})`);
  return (await res.json()) as BackendRenderJob;
}

export async function cancelRenderJob(jobId: string): Promise<BackendRenderJob> {
  const res = await fetch(`${API_BASE_URL}/render/${encodeURIComponent(jobId)}/cancel`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Failed to cancel render job (${res.status})`);
  return (await res.json()) as BackendRenderJob;
}

export function getRenderDownloadUrl(jobId: string): string {
  return `${API_BASE_URL}/render/${encodeURIComponent(jobId)}/download`;
}

export interface BackendStoryboardBeat {
  beat_index: number;
  act: "Opening Hook" | "Rising Action" | "Climax" | "Emotional Resolution";
  clip_id: string;
  source_id: string;
  title: string;
  start_time_seconds: number;
  end_time_seconds: number;
  duration_seconds: number;
  playback_speed: number;
  transition_in: string;
  rationale: string;
}

export interface BackendDirectorPlanResponse {
  engine_used: "ollama" | "rule_fallback";
  intent: {
    mood: string;
    theme_keywords: string[];
    target_duration_seconds: number;
    aspect_ratio: AspectRatio;
    color_grade: ColorGradePreset;
    pacing: string;
    title_suggestion: string;
  };
  storyboard: BackendStoryboardBeat[];
  timeline: {
    project_id: string;
    title: string;
    aspect_ratio: AspectRatio;
    target_duration_seconds: number;
    fps: number;
    color_grade: ColorGradePreset;
    cinematic_effects?: {
      vignette: boolean;
      film_grain: boolean;
      ken_burns_on_images: boolean;
      audio_ducking: boolean;
      loudness_normalize: boolean;
    };
    video_clips: {
      clip_id: string;
      source_id: string;
      source_filename: string;
      source_url: string;
      thumbnail_url?: string | null;
      start_time_seconds: number;
      end_time_seconds: number;
      timeline_start_seconds: number;
      duration_seconds: number;
      playback_speed: number;
      speed_ramp?: SpeedRampPreset;
      transition_in?: { type: string; duration_seconds: number } | null;
      quality_score?: number | null;
      tags: string[];
    }[];
    audio_tracks: {
      id: string;
      name: string;
      source_id: string;
      source_url: string;
      start_time_seconds: number;
      timeline_start_seconds: number;
      duration_seconds: number;
    }[];
    subtitles: {
      id: string;
      start_seconds: number;
      end_seconds: number;
      text: string;
      style: "cinematic_gold_bottom" | "bold_center_reel" | "subtle_white";
    }[];
  };
  warnings: string[];
}

export async function generateDirectorPlan(params: {
  projectId: string;
  instruction: string;
  targetDurationSeconds?: number;
  aspectRatio?: AspectRatio;
  beatSync?: boolean;
  styleRecipeId?: string;
}): Promise<BackendDirectorPlanResponse> {
  const res = await fetch(`${API_BASE_URL}/director/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: params.projectId,
      instruction: params.instruction,
      target_duration_seconds: params.targetDurationSeconds,
      aspect_ratio: params.aspectRatio,
      use_llm: true,
      beat_sync: params.beatSync ?? true,
      style_recipe_id: params.styleRecipeId || undefined,
    }),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `AI Director failed (${res.status})`);
  }
  return (await res.json()) as BackendDirectorPlanResponse;
}

export async function analyzeAudioAsset(mediaId: string): Promise<BackendMediaAsset> {
  const res = await fetch(`${API_BASE_URL}/audio/${encodeURIComponent(mediaId)}/analyze`, {
    method: "POST",
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Audio analysis failed (${res.status})`);
  }
  return (await res.json()) as BackendMediaAsset;
}

export async function getAudioAnalysis(mediaId: string): Promise<BackendAudioAnalysis> {
  const res = await fetch(`${API_BASE_URL}/audio/${encodeURIComponent(mediaId)}/analysis`);
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Failed to load audio analysis (${res.status})`);
  }
  return (await res.json()) as BackendAudioAnalysis;
}

export interface BackendBeatSyncResponse {
  tempo_bpm: number;
  snapped_cuts: number;
  beat_timestamps_used: number[];
  timeline: {
    target_duration_seconds: number;
    video_clips: {
      clip_id: string;
      source_id: string;
      start_time_seconds: number;
      end_time_seconds: number;
      timeline_start_seconds: number;
      duration_seconds: number;
      playback_speed: number;
      speed_ramp?: SpeedRampPreset;
    }[];
  };
}

export async function beatSyncTimeline(params: {
  projectId: string;
  title: string;
  aspectRatio: AspectRatio;
  colorGrade: ColorGradePreset;
  clips: TimelineClip[];
  audioSourceId: string;
  subtitles?: SubtitleCue[];
  cinematicEffects?: CinematicEffects;
  toleranceSeconds?: number;
}): Promise<BackendBeatSyncResponse> {
  const res = await fetch(`${API_BASE_URL}/audio/beat-sync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      timeline: serializeTimelinePayload(params),
      audio_source_id: params.audioSourceId,
      tolerance_seconds: params.toleranceSeconds ?? 0.35,
    }),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Beat-sync failed (${res.status})`);
  }
  return (await res.json()) as BackendBeatSyncResponse;
}

// ---- Phase 6: Whisper Voice Transcription, Conversational Editing & History ----

export interface BackendWhisperStatus {
  package_installed: boolean;
  model_name: string;
  device: string;
  compute_type: string;
  model_cached: boolean;
  ready: boolean;
  ffmpeg_ready: boolean;
  detail: string;
}

export interface BackendTranscriptionResponse {
  text: string;
  language: string;
  duration_seconds: number;
  engine: "faster_whisper" | "custom";
  segments: {
    id: string;
    start_seconds: number;
    end_seconds: number;
    text: string;
  }[];
  suggested_subtitles: {
    id: string;
    start_seconds: number;
    end_seconds: number;
    text: string;
    style: "cinematic_gold_bottom" | "bold_center_reel" | "subtle_white";
  }[];
}

export interface BackendTimelineDiffSummary {
  added_clip_ids: string[];
  removed_clip_ids: string[];
  modified_clip_ids: string[];
  shifted_clip_ids: string[];
  unchanged_clip_ids: string[];
  global_visual_changed: boolean;
  subtitles_changed: boolean;
  audio_changed: boolean;
  affected_segment_indices: number[];
  changes: string[];
}

export interface BackendConversationalEditResponse {
  engine_used: "ollama" | "rule_fallback";
  instruction: string;
  timeline: BackendDirectorPlanResponse["timeline"];
  diff: BackendTimelineDiffSummary;
  operations_applied: string[];
  warnings: string[];
  revision_index: number;
  history_count: number;
  can_undo: boolean;
  can_redo: boolean;
}

export interface BackendProjectHistoryResponse {
  project_id: string;
  active_revision_index: number;
  total_revisions: number;
  can_undo: boolean;
  can_redo: boolean;
  timeline?: BackendDirectorPlanResponse["timeline"] | null;
}

export async function getVoiceStatus(): Promise<BackendWhisperStatus> {
  const res = await fetch(`${API_BASE_URL}/voice/status`);
  if (!res.ok) throw new Error(`Voice status error (${res.status})`);
  return (await res.json()) as BackendWhisperStatus;
}

export async function transcribeVoiceBlob(blob: Blob): Promise<BackendTranscriptionResponse> {
  const form = new FormData();
  form.append("file", blob, "voice_command.webm");
  const res = await fetch(`${API_BASE_URL}/voice/transcribe`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Voice transcription failed (${res.status})`);
  }
  return (await res.json()) as BackendTranscriptionResponse;
}

export async function transcribeMediaSubtitles(
  mediaId: string,
  style: SubtitleCue["style"] = "cinematic_gold_bottom"
): Promise<BackendTranscriptionResponse> {
  const res = await fetch(
    `${API_BASE_URL}/voice/subtitles/${encodeURIComponent(mediaId)}?style=${encodeURIComponent(style)}`,
    { method: "POST" }
  );
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Subtitle extraction failed (${res.status})`);
  }
  return (await res.json()) as BackendTranscriptionResponse;
}

export async function editTimelineConversationally(params: {
  projectId: string;
  instruction: string;
  title: string;
  aspectRatio: AspectRatio;
  colorGrade: ColorGradePreset;
  clips: TimelineClip[];
  subtitles?: SubtitleCue[];
  cinematicEffects?: CinematicEffects;
}): Promise<BackendConversationalEditResponse> {
  const res = await fetch(`${API_BASE_URL}/director/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: params.projectId,
      instruction: params.instruction,
      timeline: serializeTimelinePayload(params),
      use_llm: true,
      record_history: true,
    }),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Conversational edit failed (${res.status})`);
  }
  return (await res.json()) as BackendConversationalEditResponse;
}

export async function undoProjectHistory(projectId: string): Promise<BackendProjectHistoryResponse> {
  const res = await fetch(`${API_BASE_URL}/projects/${encodeURIComponent(projectId)}/undo`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Undo failed (${res.status})`);
  return (await res.json()) as BackendProjectHistoryResponse;
}

export async function redoProjectHistory(projectId: string): Promise<BackendProjectHistoryResponse> {
  const res = await fetch(`${API_BASE_URL}/projects/${encodeURIComponent(projectId)}/redo`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Redo failed (${res.status})`);
  return (await res.json()) as BackendProjectHistoryResponse;
}

// ---- Phase 7: Trend Intelligence & Original Style Recipes ----

export interface BackendStyleRecipe {
  id: string;
  name: string;
  description: string;
  source_type: "builtin" | "uploaded_reference" | "url_pattern";
  is_builtin: boolean;
  reference_label?: string | null;
  cuts_per_minute: number;
  avg_shot_duration_seconds: number;
  cut_cadence: "rapid" | "moderate" | "deliberate";
  motion_velocity_score: number;
  motion_profile: "static" | "smooth_glide" | "dynamic_burst" | "high_velocity";
  color_mood: string;
  recommended_color_grade: ColorGradePreset;
  recommended_aspect_ratio: AspectRatio;
  recommended_pacing: string;
  recommended_speed_ramp: SpeedRampPreset;
  recommended_transition: string;
  cinematic_effects: {
    vignette: boolean;
    film_grain: boolean;
    ken_burns_on_images: boolean;
    audio_ducking: boolean;
    loudness_normalize: boolean;
  };
  dominant_palette: string[];
  prompt_hint: string;
  safety_audit: {
    copyright_safe: boolean;
    media_downloaded: boolean;
    private_scraping_blocked: boolean;
    raw_frames_retained: boolean;
    compliance_note: string;
  };
  created_at: string;
}

export interface BackendStyleApplyResponse {
  recipe: BackendStyleRecipe;
  timeline: BackendDirectorPlanResponse["timeline"];
  diff: BackendTimelineDiffSummary;
  changes_applied: string[];
  revision_index: number;
  history_count: number;
  can_undo: boolean;
  can_redo: boolean;
}

export async function listStyleRecipes(): Promise<BackendStyleRecipe[]> {
  const res = await fetch(`${API_BASE_URL}/trends/recipes`);
  if (!res.ok) throw new Error(`Failed to load style recipes (${res.status})`);
  return (await res.json()) as BackendStyleRecipe[];
}

export async function analyzeReferenceVideoUpload(
  file: File,
  recipeName?: string
): Promise<BackendStyleRecipe> {
  const form = new FormData();
  form.append("file", file);
  if (recipeName) form.append("recipe_name", recipeName);
  const res = await fetch(`${API_BASE_URL}/trends/analyze-upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Reference video analysis failed (${res.status})`);
  }
  return (await res.json()) as BackendStyleRecipe;
}

export async function analyzeSafeReferenceUrl(params: {
  referenceUrl: string;
  recipeName?: string;
  styleNotes?: string;
}): Promise<BackendStyleRecipe> {
  const res = await fetch(`${API_BASE_URL}/trends/analyze-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      reference_url: params.referenceUrl,
      recipe_name: params.recipeName || undefined,
      style_notes: params.styleNotes || "",
    }),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Reference URL analysis failed (${res.status})`);
  }
  return (await res.json()) as BackendStyleRecipe;
}

export async function applyStyleRecipe(params: {
  recipeId: string;
  projectId: string;
  title: string;
  aspectRatio: AspectRatio;
  colorGrade: ColorGradePreset;
  clips: TimelineClip[];
  subtitles?: SubtitleCue[];
  cinematicEffects?: CinematicEffects;
}): Promise<BackendStyleApplyResponse> {
  const res = await fetch(
    `${API_BASE_URL}/trends/recipes/${encodeURIComponent(params.recipeId)}/apply`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_id: params.projectId,
        timeline: serializeTimelinePayload(params),
        record_history: true,
      }),
    }
  );
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Failed to apply style recipe (${res.status})`);
  }
  return (await res.json()) as BackendStyleApplyResponse;
}

// ---- Phase 8: Campus Authentication, Quotas, Admin & Migrations ----

export type BackendUserRole = "student" | "club_lead" | "admin";

export interface BackendUserPublic {
  id: string;
  full_name: string;
  email: string;
  department: string;
  role: BackendUserRole;
  storage_quota_bytes: number;
  used_storage_bytes: number;
  is_active: boolean;
  created_at: string;
}

export interface BackendAuthTokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in_seconds: number;
  user: BackendUserPublic;
}

export interface BackendQuotaStatus {
  user_id: string;
  email: string;
  used_bytes: number;
  quota_bytes: number;
  remaining_bytes: number;
  percent_used: number;
}

export interface BackendAdminUserRecord {
  id: string;
  full_name: string;
  email: string;
  department: string;
  role: BackendUserRole;
  storage_quota_bytes: number;
  used_storage_bytes: number;
  projects_count: number;
  is_active: boolean;
  created_at: string;
}

export interface BackendDirectoryStorage {
  uploads_bytes: number;
  proxies_bytes: number;
  renders_bytes: number;
  cache_bytes: number;
  segment_cache_bytes: number;
  total_managed_bytes: number;
}

export interface BackendAdminOverview {
  system: {
    cpu_percent: number;
    cpu_cores: number;
    memory_used_gb: number;
    memory_total_gb: number;
    memory_percent: number;
    disk_free_gb: number;
    disk_total_gb: number;
    hardware_encoder: string;
  };
  storage: BackendDirectoryStorage;
  active_users_count: number;
  total_users_count: number;
  total_projects_count: number;
  total_media_assets_count: number;
  render_queue: Record<string, number>;
  database_engine: string;
}

export interface BackendCleanupResponse {
  files_removed: number;
  freed_bytes: number;
  post_cleanup_storage: BackendDirectoryStorage;
  executed_at: string;
}

export interface BackendMigrationStatus {
  active_engine: string;
  configured_database_url: string;
  schema_version: string;
  postgres_ddl_ready: boolean;
  table_counts: Record<string, number>;
  postgres_migration_cli: string;
}

const TOKEN_STORAGE_KEY = "cineflow_jwt_token";
const USER_STORAGE_KEY = "cineflow_auth_user";

export function getStoredAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function getStoredAuthUser(): BackendUserPublic | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as BackendUserPublic;
  } catch {
    return null;
  }
}

export function saveAuthSession(token: string, user: BackendUserPublic): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  window.localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  window.dispatchEvent(new Event("cineflow-auth-changed"));
}

export function clearAuthSession(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  window.localStorage.removeItem(USER_STORAGE_KEY);
  window.dispatchEvent(new Event("cineflow-auth-changed"));
}

export function getAuthHeaders(): Record<string, string> {
  const token = getStoredAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function loginStudent(params: {
  email: string;
  password: string;
}): Promise<BackendAuthTokenResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Login failed (${res.status})`);
  }
  const data = (await res.json()) as BackendAuthTokenResponse;
  saveAuthSession(data.access_token, data.user);
  return data;
}

export async function registerStudent(params: {
  full_name: string;
  email: string;
  password: string;
  department: string;
}): Promise<BackendAuthTokenResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Registration failed (${res.status})`);
  }
  const data = (await res.json()) as BackendAuthTokenResponse;
  saveAuthSession(data.access_token, data.user);
  return data;
}

export async function fetchUserQuota(): Promise<BackendQuotaStatus> {
  const res = await fetch(`${API_BASE_URL}/auth/quota`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch user quota (${res.status})`);
  return (await res.json()) as BackendQuotaStatus;
}

export async function fetchBackendProjects(): Promise<
  { id: string; title: string; aspect_ratio: string; target_duration_seconds: number; color_grade: string; updated_at: string }[]
> {
  const res = await fetch(`${API_BASE_URL}/projects`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch projects (${res.status})`);
  return await res.json();
}

export async function createBackendProject(params: {
  title: string;
  aspect_ratio: string;
  target_duration_seconds: number;
  color_grade: string;
}): Promise<{ id: string; title: string; aspect_ratio: string; target_duration_seconds: number; color_grade: string; updated_at: string }> {
  const res = await fetch(`${API_BASE_URL}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Project creation failed (${res.status})`);
  return await res.json();
}

export async function getAdminOverview(): Promise<BackendAdminOverview> {
  const res = await fetch(`${API_BASE_URL}/admin/overview`, { headers: getAuthHeaders() });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Admin access denied (${res.status})`);
  }
  return (await res.json()) as BackendAdminOverview;
}

export async function getAdminUsers(): Promise<BackendAdminUserRecord[]> {
  const res = await fetch(`${API_BASE_URL}/admin/users`, { headers: getAuthHeaders() });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Failed to load campus users (${res.status})`);
  }
  return (await res.json()) as BackendAdminUserRecord[];
}

export async function updateAdminUser(
  userId: string,
  updates: { storage_quota_gb?: number; role?: BackendUserRole; is_active?: boolean }
): Promise<BackendAdminUserRecord> {
  const res = await fetch(`${API_BASE_URL}/admin/users/${encodeURIComponent(userId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(updates),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `User update failed (${res.status})`);
  }
  return (await res.json()) as BackendAdminUserRecord;
}

export async function triggerAdminCleanup(params: {
  purge_cache: boolean;
  purge_expired_renders: boolean;
  max_age_hours: number;
}): Promise<BackendCleanupResponse> {
  const res = await fetch(`${API_BASE_URL}/admin/cleanup`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Cleanup failed (${res.status})`);
  }
  return (await res.json()) as BackendCleanupResponse;
}

export async function getAdminMigrationStatus(): Promise<BackendMigrationStatus> {
  const res = await fetch(`${API_BASE_URL}/admin/migration-status`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch migration status (${res.status})`);
  return (await res.json()) as BackendMigrationStatus;
}

// ---- Phase 9: Showcase & Live Benchmarks ----

export interface BackendProjectDetail {
  id: string;
  owner_id?: string | null;
  title: string;
  description: string;
  aspect_ratio: AspectRatio;
  target_duration_seconds: number;
  color_grade: ColorGradePreset;
  timeline: BackendDirectorPlanResponse["timeline"] | null;
  created_at: string;
  updated_at: string;
}

export interface BackendBenchmarkStageResult {
  stage_id: string;
  stage_name: string;
  duration_seconds: number;
  throughput_label: string;
  cpu_percent_avg: number;
  memory_rss_mb: number;
  notes: string;
}

export interface BackendBenchmarkReport {
  generated_at: string;
  host_os: string;
  python_version: string;
  cpu_cores: number;
  ram_total_gb: number;
  ffmpeg_version: string;
  hardware_profile: {
    profile: "low" | "medium" | "high";
    cpu_cores: number;
    free_disk_gb: number;
    video_encoder: string;
    hw_accel_available: boolean;
    detected_encoders: string[];
    max_concurrent_renders: number;
  };
  stages: BackendBenchmarkStageResult[];
  cold_render_seconds: number;
  warm_cached_render_seconds: number;
  cache_speedup_percent: number;
  segment_cache_hits: number;
  segment_cache_misses: number;
  output_duration_seconds: number;
  realtime_speedup_x: number;
  portrait_render_seconds: number;
  output_file_bytes: number;
}

export interface BackendShowcaseSampleFileInfo {
  filename: string;
  media_kind: "video" | "image" | "audio";
  size_bytes: number;
  resolution_label: string;
  duration_seconds: number;
  role: string;
}

export interface BackendShowcaseStatus {
  showcase_project_id: string;
  project_loaded: boolean;
  sample_pack_ready: boolean;
  sample_files: BackendShowcaseSampleFileInfo[];
  total_sample_bytes: number;
  benchmark_report_ready: boolean;
  last_benchmark_at?: string | null;
  hardware: BackendBenchmarkReport["hardware_profile"];
}

export interface BackendShowcaseLoadResponse {
  project: BackendProjectDetail;
  assets: BackendMediaAsset[];
  audio_asset_id?: string | null;
  newly_ingested: boolean;
  total_sample_bytes: number;
  message: string;
}

export async function fetchBackendProject(projectId: string): Promise<BackendProjectDetail> {
  const res = await fetch(`${API_BASE_URL}/projects/${encodeURIComponent(projectId)}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to fetch project '${projectId}' (${res.status})`);
  return (await res.json()) as BackendProjectDetail;
}

export async function fetchShowcaseStatus(): Promise<BackendShowcaseStatus> {
  const res = await fetch(`${API_BASE_URL}/showcase/status`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch showcase status (${res.status})`);
  return (await res.json()) as BackendShowcaseStatus;
}

export async function loadShowcaseProject(forceReset = false): Promise<BackendShowcaseLoadResponse> {
  const res = await fetch(`${API_BASE_URL}/showcase/load`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ force_reset: forceReset }),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Failed to load HD showcase (${res.status})`);
  }
  return (await res.json()) as BackendShowcaseLoadResponse;
}

export async function fetchShowcaseBenchmarks(): Promise<BackendBenchmarkReport> {
  const res = await fetch(`${API_BASE_URL}/showcase/benchmarks`);
  if (!res.ok) throw new Error(`Failed to load benchmarks (${res.status})`);
  return (await res.json()) as BackendBenchmarkReport;
}

export async function runShowcaseBenchmarks(): Promise<BackendBenchmarkReport> {
  const res = await fetch(`${API_BASE_URL}/showcase/benchmarks/run`, { method: "POST" });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errBody.detail || `Benchmark run failed (${res.status})`);
  }
  return (await res.json()) as BackendBenchmarkReport;
}

