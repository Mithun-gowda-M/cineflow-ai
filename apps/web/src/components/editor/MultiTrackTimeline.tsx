"use client";

import React, { useRef, useState } from "react";
import { 
  Volume2, VolumeX, Eye, EyeOff, Lock, Unlock, 
  Sparkles, Scissors, Layers, Music, Type 
} from "lucide-react";
import { TimelineClip, SubtitleCue } from "@/types";
import { formatDuration } from "@/lib/utils";

interface MultiTrackTimelineProps {
  clips: TimelineClip[];
  subtitles: SubtitleCue[];
  currentTime: number;
  totalDuration: number;
  onSeek: (time: number) => void;
  selectedClipId: string | null;
  onSelectClip: (clip: TimelineClip) => void;
  waveformPeaks?: number[];
  beatTimestamps?: number[];
  tempoBpm?: number | null;
}

export const MultiTrackTimeline: React.FC<MultiTrackTimelineProps> = ({
  clips,
  subtitles,
  currentTime,
  totalDuration,
  onSeek,
  selectedClipId,
  onSelectClip,
  waveformPeaks,
  beatTimestamps,
  tempoBpm,
}) => {
  const rulerRef = useRef<HTMLDivElement>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(10); // pixels per second
  const [trackLocks, setTrackLocks] = useState<Record<string, boolean>>({});
  const [trackMutes, setTrackMutes] = useState<Record<string, boolean>>({});

  const toggleLock = (track: string) => {
    setTrackLocks((prev) => ({ ...prev, [track]: !prev[track] }));
  };

  const toggleMute = (track: string) => {
    setTrackMutes((prev) => ({ ...prev, [track]: !prev[track] }));
  };

  // Handle timeline scrubbing on click/drag
  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!rulerRef.current) return;
    const rect = rulerRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickedTime = Math.max(0, Math.min(totalDuration, clickX / zoomLevel));
    onSeek(clickedTime);
  };

  const totalWidthPx = Math.max(800, totalDuration * zoomLevel);
  const playheadLeftPx = currentTime * zoomLevel;

  return (
    <div className="h-64 bg-cine-surface border-t border-cine-border flex flex-col shrink-0 select-none">
      {/* Timeline Controls Bar (Zoom, Track names) */}
      <div className="h-9 px-4 bg-cine-black/80 border-b border-cine-border flex items-center justify-between text-xs">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-gray-300 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-cine-gold-400" /> Multi-Track Sequence
          </span>
          <span className="text-[10px] text-gray-500 font-mono">
            {clips.length} Clips • {subtitles.length} Subtitles
          </span>
        </div>

        {/* Zoom Slider */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-gray-400">Zoom:</span>
          <input
            type="range"
            min="5"
            max="25"
            step="1"
            value={zoomLevel}
            onChange={(e) => setZoomLevel(Number(e.target.value))}
            className="w-24 accent-cine-gold-500 cursor-pointer h-1 bg-cine-card rounded"
          />
        </div>
      </div>

      {/* Main Track Workspace: Headers on left, Scrollable Timeline on right */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Track Control Headers */}
        <div className="w-36 bg-cine-card border-r border-cine-border shrink-0 flex flex-col justify-between py-1 text-xs">
          {/* Ruler offset spacer */}
          <div className="h-6 border-b border-cine-border/50 px-2 flex items-center text-[10px] font-mono text-gray-500">
            TRACKS
          </div>

          {/* V2 Header */}
          <div className="h-10 px-2 border-b border-cine-border/30 flex items-center justify-between bg-cine-panel/40">
            <span className="font-bold text-gray-300 text-[11px] flex items-center gap-1">
              <span className="text-cine-gold-400">V2</span> Overlay
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => toggleLock("v2")}
                className="text-gray-400 hover:text-white"
                title="Lock Track"
              >
                {trackLocks.v2 ? <Lock className="w-3 h-3 text-amber-400" /> : <Unlock className="w-3 h-3" />}
              </button>
            </div>
          </div>

          {/* V1 Header */}
          <div className="h-12 px-2 border-b border-cine-border/30 flex items-center justify-between bg-cine-panel/70">
            <span className="font-bold text-gray-200 text-[11px] flex items-center gap-1">
              <span className="text-cine-gold-400">V1</span> Video
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => toggleLock("v1")}
                className="text-gray-400 hover:text-white"
                title="Lock Track"
              >
                {trackLocks.v1 ? <Lock className="w-3 h-3 text-amber-400" /> : <Unlock className="w-3 h-3" />}
              </button>
            </div>
          </div>

          {/* A1 Voice Header */}
          <div className="h-9 px-2 border-b border-cine-border/30 flex items-center justify-between bg-cine-panel/40">
            <span className="font-bold text-gray-300 text-[11px] flex items-center gap-1">
              <span className="text-cine-cyan-400">A1</span> Voice
            </span>
            <button onClick={() => toggleMute("a1")} className="text-gray-400 hover:text-white">
              {trackMutes.a1 ? <VolumeX className="w-3 h-3 text-red-400" /> : <Volume2 className="w-3 h-3" />}
            </button>
          </div>

          {/* A2 Music Header */}
          <div className="h-10 px-2 border-b border-cine-border/30 flex items-center justify-between bg-cine-panel/50">
            <span className="font-bold text-gray-300 text-[11px] flex items-center gap-1">
              <span className="text-cine-cyan-400">A2</span> Music
            </span>
            <button onClick={() => toggleMute("a2")} className="text-gray-400 hover:text-white">
              {trackMutes.a2 ? <VolumeX className="w-3 h-3 text-red-400" /> : <Volume2 className="w-3 h-3" />}
            </button>
          </div>

          {/* T1 Subtitles Header */}
          <div className="h-8 px-2 flex items-center justify-between bg-cine-panel/30">
            <span className="font-bold text-purple-400 text-[11px] flex items-center gap-1">
              <Type className="w-3 h-3" /> T1 Subs
            </span>
          </div>
        </div>

        {/* Right: Scrollable Timeline Canvas */}
        <div
          ref={rulerRef}
          onClick={handleTimelineClick}
          className="flex-1 overflow-x-auto overflow-y-hidden relative bg-cine-black cursor-crosshair"
        >
          <div style={{ width: `${totalWidthPx}px` }} className="relative h-full flex flex-col justify-between">
            {/* Top Timecode Ruler */}
            <div className="h-6 border-b border-cine-border/50 relative bg-cine-card/40 flex items-center">
              {Array.from({ length: Math.ceil(totalDuration / 5) + 1 }).map((_, i) => {
                const sec = i * 5;
                const leftPos = sec * zoomLevel;
                return (
                  <div
                    key={i}
                    className="absolute top-0 bottom-0 border-l border-cine-border/60 pl-1 text-[9px] font-mono text-gray-500 pointer-events-none"
                    style={{ left: `${leftPos}px` }}
                  >
                    {formatDuration(sec)}
                  </div>
                );
              })}
            </div>

            {/* Red Scrub Playhead Indicator */}
            <div
              className="absolute top-0 bottom-0 w-[2px] bg-red-500 z-30 pointer-events-none shadow-[0_0_8px_rgba(239,68,68,0.8)]"
              style={{ left: `${playheadLeftPx}px` }}
            >
              <div className="w-3 h-3 bg-red-500 rotate-45 -translate-x-[5px] -translate-y-1" />
            </div>

            {/* Track V2 Blocks */}
            <div className="h-10 border-b border-cine-border/20 relative timeline-track-grid bg-cine-surface/20">
              {clips
                .filter((c) => c.trackId === "v2")
                .map((clip) => {
                  const left = clip.startTime * zoomLevel;
                  const width = clip.duration * zoomLevel;
                  const isSelected = selectedClipId === clip.id;

                  return (
                    <div
                      key={clip.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectClip(clip);
                      }}
                      className={`absolute top-1 bottom-1 rounded px-2 flex items-center gap-1.5 overflow-hidden cursor-pointer transition-all border ${
                        isSelected
                          ? "bg-cine-gold-500/40 border-cine-gold-500 shadow-gold-sm"
                          : "bg-cine-gold-500/20 border-cine-gold-500/40 hover:border-cine-gold-500"
                      }`}
                      style={{ left: `${left}px`, width: `${width}px` }}
                    >
                      <span className="text-[10px] font-semibold text-white truncate">{clip.title}</span>
                    </div>
                  );
                })}
            </div>

            {/* Track V1 Blocks */}
            <div className="h-12 border-b border-cine-border/20 relative timeline-track-grid bg-cine-surface/30">
              {clips
                .filter((c) => c.trackId === "v1")
                .map((clip) => {
                  const left = clip.startTime * zoomLevel;
                  const width = clip.duration * zoomLevel;
                  const isSelected = selectedClipId === clip.id;

                  return (
                    <div
                      key={clip.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectClip(clip);
                      }}
                      className={`absolute top-1 bottom-1 rounded px-2 flex items-center justify-between gap-1.5 overflow-hidden cursor-pointer transition-all border ${
                        isSelected
                          ? "bg-cine-gold-500/45 border-cine-gold-400 shadow-gold-sm ring-1 ring-cine-gold-400"
                          : "bg-cine-gold-500/25 border-cine-gold-500/50 hover:border-cine-gold-400"
                      }`}
                      style={{ left: `${left}px`, width: `${width}px` }}
                    >
                      <div className="flex items-center gap-1.5 truncate">
                        <div
                          className="w-8 h-8 rounded bg-cover bg-center shrink-0 border border-black/40"
                          style={{ backgroundImage: `url('${clip.thumbnailUrl}')` }}
                        />
                        <span className="text-[11px] font-bold text-white truncate">{clip.title}</span>
                      </div>
                      <span className="text-[9px] font-mono text-cine-gold-300 shrink-0">
                        {clip.speedRamp && clip.speedRamp !== "none" ? `⚡ ` : ""}
                        {clip.duration.toFixed(1)}s
                      </span>
                    </div>
                  );
                })}
            </div>

            {/* Track A1 Dialogue */}
            <div className="h-9 border-b border-cine-border/20 relative timeline-track-grid bg-cine-black/40">
              {clips
                .filter((c) => c.trackId === "a1")
                .map((clip) => (
                  <div
                    key={clip.id}
                    className="absolute top-1 bottom-1 rounded px-2 bg-cine-cyan-500/20 border border-cine-cyan-500/40 flex items-center text-[10px] text-cine-cyan-300 font-medium"
                    style={{ left: `${clip.startTime * zoomLevel}px`, width: `${clip.duration * zoomLevel}px` }}
                  >
                    Voice Track ({clip.duration}s)
                  </div>
                ))}
            </div>

            {/* Track A2 Music with Real Librosa Waveform & Beat Markers */}
            <div className="h-10 border-b border-cine-border/20 relative timeline-track-grid bg-cine-black/60 flex items-center px-2 overflow-hidden">
              <div className="absolute inset-0 flex items-end gap-[2px] px-1 py-1.5 opacity-55 pointer-events-none">
                {(waveformPeaks && waveformPeaks.length > 0
                  ? waveformPeaks
                  : Array.from({ length: 48 }).map((_, i) => (i % 4 === 0 ? 0.85 : 0.4))
                ).map((amp, i) => (
                  <div
                    key={i}
                    className={`flex-1 rounded-full ${
                      i % 4 === 0 ? "bg-cine-gold-400" : "bg-cine-cyan-400"
                    }`}
                    style={{ height: `${Math.max(14, Math.min(100, Math.round(amp * 100)))}%` }}
                  />
                ))}
              </div>
              {beatTimestamps &&
                beatTimestamps
                  .filter((b) => b >= 0 && b <= totalDuration)
                  .slice(0, 120)
                  .map((beatSec, idx) => (
                    <div
                      key={`${beatSec}-${idx}`}
                      className={`absolute top-0 bottom-0 pointer-events-none ${
                        idx % 4 === 0
                          ? "w-[1.5px] bg-cine-gold-400/75"
                          : "w-px bg-cine-cyan-400/35"
                      }`}
                      style={{ left: `${beatSec * zoomLevel}px` }}
                    />
                  ))}
              <span className="text-[10px] font-mono text-cine-cyan-300 font-semibold relative z-10 bg-cine-black/70 px-1.5 py-0.5 rounded">
                A2 • {clips.find((c) => c.trackId === "a2")?.title || "Librosa Beat-Synced Soundtrack"}{" "}
                ({tempoBpm && tempoBpm > 0 ? `${Math.round(tempoBpm)} BPM` : "124 BPM"})
              </span>
            </div>

            {/* Track T1 Subtitles */}
            <div className="h-8 relative timeline-track-grid bg-cine-surface/10 flex items-center">
              {subtitles.map((sub) => {
                const left = sub.startTime * zoomLevel;
                const width = sub.duration * zoomLevel;

                return (
                  <div
                    key={sub.id}
                    className="absolute top-1 bottom-1 rounded px-1.5 bg-purple-500/20 border border-purple-500/40 text-[9px] font-mono text-purple-300 truncate flex items-center"
                    style={{ left: `${left}px`, width: `${width}px` }}
                    title={sub.text}
                  >
                    &ldquo;{sub.text}&rdquo;
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

