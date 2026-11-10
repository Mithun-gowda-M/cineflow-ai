export type AspectRatio = "16:9" | "9:16" | "1:1" | "21:9";

export type TransitionType = 
  | "none"
  | "crossfade"
  | "fade_from_black"
  | "fade_to_black"
  | "slide_left"
  | "wipe_left"
  | "zoom_in";

export type ColorGradePreset = 
  | "natural"
  | "cinematic_teal_orange"
  | "golden_hour"
  | "moody_dark"
  | "vintage_film";

export interface TimelineClip {
  id: string;
  sourceId?: string;
  mediaKind?: "video" | "image" | "audio";
  title: string;
  sourceUrl: string;
  proxyUrl?: string;
  thumbnailUrl: string;
  trackId: "v1" | "v2" | "a1" | "a2" | "t1";
  startTime: number; // in timeline
  duration: number;
  trimStart: number;
  trimEnd: number;
  speed: number;
  transition: TransitionType;
  colorGrade?: ColorGradePreset;
  qualityScore: number;
  tags: string[];
}

export interface SubtitleCue {
  id: string;
  startTime: number;
  duration: number;
  text: string;
  style: "cinematic_gold_bottom" | "bold_center_reel";
}

export interface ProjectData {
  id: string;
  title: string;
  description?: string;
  aspectRatio: AspectRatio;
  targetDuration: number;
  colorGrade: ColorGradePreset;
  updatedAt: string;
  thumbnailUrl: string;
  clipsCount: number;
  clips: TimelineClip[];
  subtitles: SubtitleCue[];
}

export interface UploadedMediaItem {
  id: string;
  filename: string;
  url: string;
  thumbnailUrl: string;
  fileSizeMB: number;
  durationSeconds: number;
  resolution: string;
  fps: number;
  qualityScore: number;
  tags: string[];
  blurScore: number; // 0-100 (higher = sharper)
  exposureScore: number; // 0-100 (optimal = 80-100)
  stabilityScore?: number;
  compositionScore?: number;
  explanation?: string;
  dominantColors?: string[];
  scenesCount?: number;
  duplicateOfId?: string | null;
  similarityPercent?: number | null;
  motionIntensity?: string;
  lightingMood?: string;
}

