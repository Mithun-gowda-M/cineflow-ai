import type { AspectRatio, ColorGradePreset, TimelineClip } from "@/types";

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

export async function submitRenderJob(params: {
  projectId: string;
  title: string;
  aspectRatio: AspectRatio;
  colorGrade: ColorGradePreset;
  clips: TimelineClip[];
  resolution: "720p" | "1080p" | "4k";
  encoderPreference: "auto" | "cpu" | "nvenc" | "qsv" | "amf";
}): Promise<BackendRenderJob> {
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
      ducking_enabled: true,
      duck_volume: 0.35,
    }));

  const totalDuration = videoClips.reduce((acc, c) => acc + c.duration_seconds / c.playback_speed, 0);

  const res = await fetch(`${API_BASE_URL}/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resolution: params.resolution,
      encoder_preference: params.encoderPreference,
      timeline: {
        version: "1.0",
        project_id: params.projectId,
        title: params.title,
        aspect_ratio: params.aspectRatio,
        target_duration_seconds: Math.max(1, totalDuration),
        fps: 30,
        color_grade: params.colorGrade,
        video_clips: videoClips,
        audio_tracks: audioTracks,
        subtitles: [],
      },
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

