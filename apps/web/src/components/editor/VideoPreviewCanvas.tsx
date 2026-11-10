"use client";

import React, { useRef, useEffect } from "react";
import { Play, Pause, SkipBack, SkipForward, Maximize2 } from "lucide-react";
import { AspectRatio, CinematicEffects, ColorGradePreset, TimelineClip, SubtitleCue } from "@/types";
import { formatTimecode } from "@/lib/utils";

interface VideoPreviewCanvasProps {
  aspectRatio: AspectRatio;
  colorGrade: ColorGradePreset;
  cinematicEffects?: CinematicEffects;
  currentTime: number;
  totalDuration: number;
  isPlaying: boolean;
  onTogglePlay: () => void;
  onSeek: (time: number) => void;
  clips: TimelineClip[];
  subtitles: SubtitleCue[];
}

export const VideoPreviewCanvas: React.FC<VideoPreviewCanvasProps> = ({
  aspectRatio,
  colorGrade,
  cinematicEffects,
  currentTime,
  totalDuration,
  isPlaying,
  onTogglePlay,
  onSeek,
  clips,
  subtitles,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const activeClip = clips.find(
    (c) =>
      (c.trackId === "v1" || c.trackId === "v2") &&
      currentTime >= c.startTime &&
      currentTime < c.startTime + c.duration
  );

  const activeSubtitle = subtitles.find(
    (s) => currentTime >= s.startTime && currentTime <= s.startTime + s.duration
  );

  const videoSrc = activeClip?.proxyUrl || activeClip?.sourceUrl || "";
  const isRealVideo =
    activeClip?.mediaKind === "video" ||
    /\.(mp4|mov|webm|m4v)(\?|$)/i.test(videoSrc);

  // Sync HTML5 video playhead & playback speed with timeline
  useEffect(() => {
    const vid = videoRef.current;
    if (!vid || !isRealVideo || !activeClip) return;

    const clipLocalOffset =
      Math.max(0, currentTime - activeClip.startTime) * (activeClip.speed || 1.0) +
      (activeClip.trimStart || 0);

    if (Math.abs(vid.currentTime - clipLocalOffset) > 0.35) {
      vid.currentTime = clipLocalOffset;
    }
    vid.playbackRate = Math.min(4.0, Math.max(0.25, activeClip.speed || 1.0));

    if (isPlaying && vid.paused) {
      vid.play().catch(() => {});
    } else if (!isPlaying && !vid.paused) {
      vid.pause();
    }
  }, [currentTime, isPlaying, activeClip, isRealVideo]);

  const aspectClasses: Record<AspectRatio, string> = {
    "16:9": "aspect-video max-w-4xl",
    "9:16": "aspect-[9/16] max-h-[480px]",
    "1:1": "aspect-square max-h-[480px]",
    "21:9": "aspect-[21/9] max-w-5xl",
  };

  const lutFilters: Record<ColorGradePreset, string> = {
    natural: "none",
    golden_hour: "sepia(25%) saturate(145%) contrast(115%) brightness(105%) hue-rotate(-8deg)",
    cinematic_teal_orange: "contrast(130%) saturate(125%) hue-rotate(15deg)",
    moody_dark: "contrast(125%) saturate(75%) brightness(85%)",
    vintage_film: "sepia(40%) contrast(110%) brightness(95%) grayscale(20%)",
    bleach_bypass: "saturate(45%) contrast(155%) brightness(98%)",
    high_contrast_bw: "grayscale(100%) contrast(135%)",
  };

  return (
    <div className="flex-1 bg-cine-black flex flex-col items-center justify-center p-4 relative overflow-hidden select-none">
      {/* Aspect Ratio Viewport Frame */}
      <div
        ref={containerRef}
        className={`w-full relative rounded-xl overflow-hidden bg-black border border-cine-border shadow-2xl flex items-center justify-center transition-all duration-300 ${aspectClasses[aspectRatio]}`}
      >
        {isRealVideo && videoSrc ? (
          <video
            ref={videoRef}
            src={videoSrc}
            playsInline
            muted={false}
            className="w-full h-full object-contain transition-all duration-300"
            style={{ filter: lutFilters[colorGrade] }}
          />
        ) : (
          <div
            className="w-full h-full bg-cover bg-center transition-all duration-300"
            style={{
              backgroundImage: `url('${
                activeClip?.sourceUrl ||
                "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=1200&q=80"
              }')`,
              filter: lutFilters[colorGrade],
            }}
          />
        )}

        {/* Cinema Letterbox Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/30 pointer-events-none" />

        {/* Optional Optical Vignette Overlay */}
        {cinematicEffects?.vignette && (
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              background:
                "radial-gradient(circle, rgba(0,0,0,0) 48%, rgba(0,0,0,0.72) 100%)",
            }}
          />
        )}

        {/* Optional 35mm Film Grain Preview Overlay */}
        {cinematicEffects?.filmGrain && (
          <div
            className="absolute inset-0 pointer-events-none opacity-20 mix-blend-overlay"
            style={{
              backgroundImage:
                "radial-gradient(rgba(255,255,255,0.45) 0.5px, transparent 0.5px)",
              backgroundSize: "3px 3px",
            }}
          />
        )}

        {/* Active Subtitle Cue */}
        {activeSubtitle && (
          <div
            className={`absolute inset-x-4 text-center animate-in fade-in zoom-in-95 duration-200 pointer-events-none ${
              activeSubtitle.style === "bold_center_reel"
                ? "top-1/2 -translate-y-1/2"
                : "bottom-12"
            }`}
          >
            <span
              className={`inline-block px-4 py-1.5 rounded-lg backdrop-blur-md shadow-lg tracking-wide ${
                activeSubtitle.style === "bold_center_reel"
                  ? "bg-cine-black/85 text-white font-extrabold text-base sm:text-xl border-2 border-cine-gold-400 uppercase"
                  : activeSubtitle.style === "subtle_white"
                  ? "bg-black/70 text-gray-100 font-medium text-sm border border-white/15"
                  : "bg-black/80 text-cine-gold-300 font-semibold text-sm sm:text-base border border-cine-gold-500/30"
              }`}
            >
              {activeSubtitle.text}
            </span>
          </div>
        )}

        {/* Top Info Overlays */}
        <div className="absolute top-3 left-3 flex items-center gap-2 pointer-events-none">
          <span className="px-2 py-0.5 rounded bg-black/80 backdrop-blur-md text-[11px] font-mono text-cine-gold-400 border border-white/10">
            {formatTimecode(currentTime)}
          </span>
          <span className="px-2 py-0.5 rounded bg-black/80 backdrop-blur-md text-[10px] text-gray-300 border border-white/10">
            {aspectRatio} • {colorGrade.replace("_", " ").toUpperCase()}
          </span>
        </div>

        {activeClip && (
          <div className="absolute top-3 right-3 px-2 py-0.5 rounded bg-black/80 backdrop-blur-md text-[11px] text-white border border-cine-gold-500/30 flex items-center gap-1 pointer-events-none">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="truncate max-w-[140px]">{activeClip.title}</span>
          </div>
        )}
      </div>

      {/* Video Control Bar */}
      <div className="w-full max-w-2xl mt-4 px-4 py-2 rounded-xl bg-cine-surface/90 backdrop-blur-md border border-cine-border flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => onSeek(Math.max(0, currentTime - 1))}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
            title="Step Back 1s"
          >
            <SkipBack className="w-4 h-4" />
          </button>
          <button
            onClick={onTogglePlay}
            className="w-9 h-9 rounded-full bg-gold-gradient text-cine-black flex items-center justify-center font-bold shadow-gold-sm hover:scale-105 active:scale-95 transition-all"
            title={isPlaying ? "Pause (Space)" : "Play (Space)"}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
          </button>
          <button
            onClick={() => onSeek(Math.min(totalDuration, currentTime + 1))}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
            title="Step Forward 1s"
          >
            <SkipForward className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 flex items-center gap-2">
          <span className="text-xs font-mono text-gray-400">{formatTimecode(currentTime)}</span>
          <input
            type="range"
            min="0"
            max={totalDuration}
            step="0.1"
            value={currentTime}
            onChange={(e) => onSeek(Number(e.target.value))}
            className="flex-1 accent-cine-gold-500 cursor-pointer h-1.5 bg-cine-black rounded-lg"
          />
          <span className="text-xs font-mono text-gray-500">{formatTimecode(totalDuration)}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (containerRef.current) {
                if (document.fullscreenElement) {
                  document.exitFullscreen();
                } else {
                  containerRef.current.requestFullscreen();
                }
              }
            }}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
            title="Toggle Fullscreen"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
