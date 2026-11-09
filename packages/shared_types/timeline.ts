export type AspectRatio = "16:9" | "9:16" | "1:1" | "4:5" | "21:9";

export type TransitionType = 
  | "none"
  | "crossfade"
  | "fade_from_black"
  | "fade_to_black"
  | "slide_left"
  | "slide_right"
  | "wipe_left"
  | "wipe_right"
  | "zoom_in"
  | "zoom_out";

export type ColorGradePreset = 
  | "natural"
  | "cinematic_teal_orange"
  | "golden_hour"
  | "moody_dark"
  | "vintage_film"
  | "high_contrast_bw";

export interface TransitionSpec {
  type: TransitionType;
  duration_seconds: number;
}

export interface MediaClip {
  clip_id: string;
  source_id: string;
  source_filename: string;
  source_url: string;
  thumbnail_url?: string;
  start_time_seconds: number;
  end_time_seconds: number;
  timeline_start_seconds: number;
  duration_seconds: number;
  playback_speed: number;
  transition_in?: TransitionSpec;
  transition_out?: TransitionSpec;
  color_grade?: ColorGradePreset;
  quality_score?: number;
  tags: string[];
}

export interface AudioTrackCue {
  id: string;
  name: string;
  source_id: string;
  source_url: string;
  volume: number;
  start_time_seconds: number;
  timeline_start_seconds: number;
  duration_seconds: number;
  ducking_enabled: boolean;
  duck_volume?: number;
}

export interface SubtitleCue {
  id: string;
  start_seconds: number;
  end_seconds: number;
  text: string;
  style?: "cinematic_gold_bottom" | "bold_center_reel" | "subtle_white";
}

export interface TimelinePlan {
  version: string;
  project_id: string;
  title: string;
  aspect_ratio: AspectRatio;
  target_duration_seconds: number;
  fps: number;
  color_grade: ColorGradePreset;
  video_clips: MediaClip[];
  audio_tracks: AudioTrackCue[];
  subtitles: SubtitleCue[];
}

export interface RenderJobStatus {
  job_id: string;
  project_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress_percent: number;
  current_step: string;
  output_video_url?: string;
  output_file_size_bytes?: number;
  error_message?: string;
}

