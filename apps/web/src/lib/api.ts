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
}): Promise<BackendRenderJob> {
  const res = await fetch(`${API_BASE_URL}/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resolution: params.resolution,
      encoder_preference: params.encoderPreference,
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

