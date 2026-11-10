"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Mic,
  MicOff,
  Send,
  Sliders,
  Scissors,
  Trash2,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  AlertCircle,
  Film,
  Music,
  Type,
  Plus,
} from "lucide-react";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";
import {
  CinematicEffects,
  ColorGradePreset,
  SpeedRampPreset,
  SubtitleCue,
  TimelineClip,
  TransitionType,
} from "@/types";
import { BackendStoryboardBeat } from "@/lib/api";

interface AiDirectorDrawerProps {
  selectedClip: TimelineClip | null;
  onUpdateClip: (clipId: string, updates: Partial<TimelineClip>) => void;
  onDeleteClip: (clipId: string) => void;
  onApplyAiPlan: (instruction: string) => Promise<void> | void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  globalColorGrade: ColorGradePreset;
  onUpdateGlobalColorGrade: (grade: ColorGradePreset) => void;
  cinematicEffects?: CinematicEffects;
  onUpdateCinematicEffects?: (updates: Partial<CinematicEffects>) => void;
  onSnapToBeats?: () => Promise<void> | void;
  hasAudioTrack?: boolean;
  isBeatSyncing?: boolean;
  beatSyncMessage?: string;
  subtitles?: SubtitleCue[];
  onAddSubtitle?: (text: string, style: SubtitleCue["style"]) => void;
  onDeleteSubtitle?: (id: string) => void;
  storyboard?: BackendStoryboardBeat[];
  directorEngine?: "ollama" | "rule_fallback" | "demo" | null;
  directorWarnings?: string[];
  directorError?: string;
}

export const AiDirectorDrawer: React.FC<AiDirectorDrawerProps> = ({
  selectedClip,
  onUpdateClip,
  onDeleteClip,
  onApplyAiPlan,
  isCollapsed,
  onToggleCollapse,
  globalColorGrade,
  onUpdateGlobalColorGrade,
  cinematicEffects,
  onUpdateCinematicEffects,
  onSnapToBeats,
  hasAudioTrack = false,
  isBeatSyncing = false,
  beatSyncMessage = "",
  subtitles = [],
  onAddSubtitle,
  onDeleteSubtitle,
  storyboard = [],
  directorEngine = null,
  directorWarnings = [],
  directorError = "",
}) => {
  const [prompt, setPrompt] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [subText, setSubText] = useState("");
  const [subStyle, setSubStyle] = useState<SubtitleCue["style"]>("cinematic_gold_bottom");

  const handleSendPrompt = async (textToSend?: string) => {
    const text = textToSend || prompt;
    if (!text.trim()) return;

    setIsProcessing(true);
    try {
      await onApplyAiPlan(text);
      setPrompt("");
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleVoiceListen = () => {
    if (isListening) {
      setIsListening(false);
    } else {
      setIsListening(true);
      setTimeout(() => {
        setPrompt("Create a two-minute cinematic Deepavali video with slow dramatic intro and fast transitions during fireworks");
        setIsListening(false);
      }, 2200);
    }
  };

  if (isCollapsed) {
    return (
      <div className="w-10 bg-cine-surface border-l border-cine-border flex flex-col items-center py-3 select-none">
        <button
          onClick={onToggleCollapse}
          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
          title="Expand AI Director"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <aside className="w-80 bg-cine-surface border-l border-cine-border flex flex-col shrink-0 select-none overflow-y-auto">
      {/* Header */}
      <div className="p-3 border-b border-cine-border flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-cine-gold-400" /> AI Director Copilot
        </span>
        <button
          onClick={onToggleCollapse}
          className="p-1 rounded text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
          title="Collapse Panel"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* AI Conversational Input Box */}
      <div className="p-3 border-b border-cine-border space-y-3 bg-cine-black/40">
        <div className="flex items-center justify-between text-[11px] text-gray-400">
          <span>Creative Instructions</span>
          <span className="text-purple-400 font-mono">
            {directorEngine === "ollama"
              ? "Ollama LLM"
              : directorEngine === "rule_fallback"
              ? "4-Act Rule Engine"
              : "Ollama + Heuristic"}
          </span>
        </div>

        <div className="relative">
          <textarea
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Create a two-minute Deepavali film with slow dramatic intro and fast fireworks cuts..."
            className="w-full p-2.5 rounded-lg bg-cine-black border border-cine-border text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cine-gold-500 resize-none font-sans"
          />
          {isListening && (
            <div className="absolute top-2 right-2 flex items-center gap-1 text-[10px] text-red-400 bg-red-500/10 px-2 py-0.5 rounded animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400" /> Listening...
            </div>
          )}
        </div>

        <div className="flex items-center justify-between gap-2">
          <button
            onClick={toggleVoiceListen}
            className={`p-2 rounded-lg border text-xs flex items-center gap-1.5 transition-all ${
              isListening
                ? "bg-red-500/20 text-red-400 border-red-500 animate-pulse"
                : "bg-cine-card text-gray-300 border-cine-border hover:text-cine-gold-400"
            }`}
            title="Speech Voice Command"
          >
            {isListening ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
            <span className="text-[11px]">{isListening ? "Listening" : "Voice"}</span>
          </button>

          <GoldButton
            size="sm"
            onClick={() => handleSendPrompt()}
            disabled={isProcessing || !prompt.trim()}
            icon={
              isProcessing ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5" />
              )
            }
          >
            {isProcessing ? "Directing..." : "Direct Cut"}
          </GoldButton>
        </div>

        {directorError && (
          <div className="p-2 rounded bg-red-500/10 border border-red-500/30 text-[11px] text-red-300 flex items-start gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>{directorError}</span>
          </div>
        )}

        {directorWarnings.length > 0 && (
          <div className="p-2 rounded bg-amber-500/10 border border-amber-500/30 text-[10px] text-amber-300 space-y-1">
            {directorWarnings.map((w, i) => (
              <p key={i}>• {w}</p>
            ))}
          </div>
        )}

        {/* Quick Recipe Chips */}
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] text-gray-500 uppercase font-semibold">Quick Directing Recipes:</span>
          <div className="flex flex-col gap-1.5">
            {[
              "Create a 2-minute Deepavali film with slow dramatic intro and fast fireworks",
              "Fast 9:16 vertical Reel with energetic cuts",
              "Professional travel film with emotional ending",
            ].map((recipe, idx) => (
              <button
                key={idx}
                onClick={() => handleSendPrompt(recipe)}
                className="text-left p-1.5 rounded bg-cine-surface border border-cine-border hover:border-cine-gold-500/40 text-[11px] text-gray-300 hover:text-cine-gold-300 transition-colors"
              >
                &ldquo;{recipe}&rdquo;
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Generated Storyboard Readout */}
      {storyboard.length > 0 && (
        <div className="p-3 border-b border-cine-border space-y-2 bg-cine-surface/60">
          <div className="flex items-center justify-between text-xs font-semibold text-white">
            <span className="flex items-center gap-1.5">
              <Film className="w-3.5 h-3.5 text-cine-cyan-400" /> AI Storyboard ({storyboard.length})
            </span>
            <Badge variant="gold" size="sm">
              {directorEngine === "ollama" ? "LLM" : "Rule Engine"}
            </Badge>
          </div>
          <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
            {storyboard.map((beat) => (
              <div
                key={beat.beat_index}
                className="p-2 rounded bg-cine-black/60 border border-cine-border/60 text-[10px] space-y-0.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-cine-gold-400">{beat.act}</span>
                  <span className="font-mono text-gray-400">
                    {beat.duration_seconds.toFixed(1)}s @ {beat.playback_speed}x
                  </span>
                </div>
                <p className="text-white font-medium truncate">{beat.title}</p>
                <p className="text-gray-400 leading-tight">{beat.rationale}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Global Color Grade Selector */}
      <div className="p-3 border-b border-cine-border space-y-2">
        <div className="flex items-center justify-between text-xs text-gray-300 font-semibold">
          <span className="flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-cine-gold-400" /> Color Science LUT
          </span>
          <span className="text-[10px] text-gray-500 font-mono">Rec.709 Conformed</span>
        </div>

        <div className="grid grid-cols-2 gap-1.5">
          {(
            [
              { id: "natural", label: "Natural" },
              { id: "golden_hour", label: "Golden Hour" },
              { id: "cinematic_teal_orange", label: "Teal & Orange" },
              { id: "moody_dark", label: "Moody Dark" },
              { id: "vintage_film", label: "Vintage Film" },
              { id: "bleach_bypass", label: "Bleach Bypass" },
              { id: "high_contrast_bw", label: "High Contrast B&W" },
            ] as { id: ColorGradePreset; label: string }[]
          ).map((g) => (
            <button
              key={g.id}
              onClick={() => onUpdateGlobalColorGrade(g.id)}
              className={`p-1.5 rounded text-xs text-left transition-colors border ${
                globalColorGrade === g.id
                  ? "bg-cine-gold-500 text-cine-black font-semibold border-cine-gold-500 shadow-gold-sm"
                  : "bg-cine-card text-gray-300 border-cine-border hover:text-white"
              }`}
            >
              {g.label}
            </button>
          ))}
        </div>

        {/* Cinematic Post-Processing & Beat-Sync Controls */}
        {cinematicEffects && onUpdateCinematicEffects && (
          <div className="pt-2 border-t border-cine-border/50 space-y-2">
            <div className="grid grid-cols-2 gap-1.5 text-[11px]">
              {[
                { key: "vignette" as const, label: "Vignette" },
                { key: "filmGrain" as const, label: "35mm Grain" },
                { key: "kenBurnsOnImages" as const, label: "Ken Burns" },
                { key: "audioDucking" as const, label: "Audio Ducking" },
              ].map((opt) => (
                <button
                  key={opt.key}
                  onClick={() => onUpdateCinematicEffects({ [opt.key]: !cinematicEffects[opt.key] })}
                  className={`px-2 py-1 rounded border text-left transition-colors ${
                    cinematicEffects[opt.key]
                      ? "bg-cine-cyan-500/20 border-cine-cyan-500/50 text-cine-cyan-300 font-semibold"
                      : "bg-cine-black/50 border-cine-border text-gray-400 hover:text-white"
                  }`}
                >
                  {cinematicEffects[opt.key] ? "✓ " : ""}
                  {opt.label}
                </button>
              ))}
            </div>

            {onSnapToBeats && (
              <div className="space-y-1">
                <button
                  onClick={() => onSnapToBeats()}
                  disabled={!hasAudioTrack || isBeatSyncing}
                  className="w-full py-1.5 px-2.5 rounded bg-cine-cyan-500/15 border border-cine-cyan-500/40 text-cine-cyan-300 hover:bg-cine-cyan-500/25 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Music className="w-3.5 h-3.5" />
                  {isBeatSyncing ? "Snapping Cuts to Beats..." : "Snap Cuts to Music Beats"}
                </button>
                {beatSyncMessage && (
                  <p className="text-[10px] text-cine-cyan-300 font-mono text-center">{beatSyncMessage}</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Clip Properties Inspector */}
      <div className="p-3 space-y-3 flex-1">
        <div className="flex items-center justify-between text-xs text-gray-300 font-semibold pb-1 border-b border-cine-border">
          <span className="flex items-center gap-1.5">
            <Scissors className="w-3.5 h-3.5 text-cine-cyan-400" /> Clip Inspector
          </span>
          {selectedClip ? (
            <Badge variant="cyan" size="sm">Selected</Badge>
          ) : (
            <span className="text-[10px] text-gray-500">None selected</span>
          )}
        </div>

        {selectedClip ? (
          <div className="space-y-3">
            <div>
              <span className="text-[10px] text-gray-500 block">Clip Title</span>
              <p className="text-xs font-bold text-white truncate">{selectedClip.title}</p>
            </div>

            <div>
              <div className="flex items-center justify-between text-xs text-gray-300 mb-1">
                <span>Playback Speed:</span>
                <span className="font-mono text-cine-gold-400 font-bold">{selectedClip.speed}x</span>
              </div>
              <input
                type="range"
                min="0.25"
                max="3.0"
                step="0.25"
                value={selectedClip.speed}
                onChange={(e) => onUpdateClip(selectedClip.id, { speed: Number(e.target.value) })}
                className="w-full accent-cine-gold-500 cursor-pointer h-1 bg-cine-black rounded"
              />
            </div>

            <div>
              <label className="text-xs text-gray-300 block mb-1">Speed Ramp Curve</label>
              <select
                value={selectedClip.speedRamp || "none"}
                onChange={(e) =>
                  onUpdateClip(selectedClip.id, { speedRamp: e.target.value as SpeedRampPreset })
                }
                className="w-full p-1.5 rounded bg-cine-black border border-cine-border text-xs text-white focus:outline-none focus:border-cine-gold-500"
              >
                <option value="none">Linear Speed</option>
                <option value="fast_to_slow">Action Hero (Fast → Slow)</option>
                <option value="slow_to_fast">Momentum Build (Slow → Fast)</option>
                <option value="ease_in_out">Smooth Ease In / Out</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-gray-300 block mb-1">Transition</label>
              <select
                value={selectedClip.transition}
                onChange={(e) => onUpdateClip(selectedClip.id, { transition: e.target.value as TransitionType })}
                className="w-full p-1.5 rounded bg-cine-black border border-cine-border text-xs text-white focus:outline-none focus:border-cine-gold-500"
              >
                <option value="none">Cut (No Transition)</option>
                <option value="crossfade">Dissolve / Crossfade (0.5s)</option>
                <option value="fade_from_black">Fade From Black (0.8s)</option>
                <option value="fade_to_black">Fade To Black (0.8s)</option>
                <option value="zoom_in">Dynamic Zoom In</option>
                <option value="wipe_left">Wipe Left</option>
              </select>
            </div>

            <div className="pt-2">
              <button
                onClick={() => onDeleteClip(selectedClip.id)}
                className="w-full py-1.5 rounded bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 text-xs flex items-center justify-center gap-1.5 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" /> Remove Clip from Track
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 text-xs">
            <p>Click any clip on the timeline below to inspect and trim its properties.</p>
          </div>
        )}

        {/* Burned-In Animated Titles (ASS Typography) */}
        {onAddSubtitle && (
          <div className="pt-3 mt-3 border-t border-cine-border space-y-2">
            <div className="flex items-center justify-between text-xs text-gray-300 font-semibold">
              <span className="flex items-center gap-1.5">
                <Type className="w-3.5 h-3.5 text-purple-400" /> Burned-In Titles (T1)
              </span>
              <span className="text-[10px] text-gray-500 font-mono">{subtitles.length} cues</span>
            </div>

            <div className="space-y-1.5">
              <input
                type="text"
                value={subText}
                onChange={(e) => setSubText(e.target.value)}
                placeholder="Type animated title or caption..."
                className="w-full px-2 py-1.5 rounded bg-cine-black border border-cine-border text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-400"
              />
              <div className="flex items-center gap-1.5">
                <select
                  value={subStyle}
                  onChange={(e) => setSubStyle(e.target.value as SubtitleCue["style"])}
                  className="flex-1 p-1.5 rounded bg-cine-black border border-cine-border text-[11px] text-white"
                >
                  <option value="cinematic_gold_bottom">Cinematic Gold</option>
                  <option value="bold_center_reel">Bold Center Reel</option>
                  <option value="subtle_white">Subtle White</option>
                </select>
                <button
                  onClick={() => {
                    if (!subText.trim()) return;
                    onAddSubtitle(subText.trim(), subStyle);
                    setSubText("");
                  }}
                  disabled={!subText.trim()}
                  className="px-2.5 py-1.5 rounded bg-purple-500/20 border border-purple-500/40 text-purple-300 hover:bg-purple-500/30 disabled:opacity-40 text-xs font-semibold flex items-center gap-1"
                >
                  <Plus className="w-3 h-3" /> Add
                </button>
              </div>
            </div>

            {subtitles.length > 0 && (
              <div className="space-y-1 max-h-28 overflow-y-auto pr-1">
                {subtitles.map((sub) => (
                  <div
                    key={sub.id}
                    className="flex items-center justify-between gap-2 px-2 py-1 rounded bg-cine-black/60 border border-cine-border/50 text-[10px]"
                  >
                    <span className="text-gray-200 truncate">{sub.text}</span>
                    {onDeleteSubtitle && (
                      <button
                        onClick={() => onDeleteSubtitle(sub.id)}
                        className="text-gray-500 hover:text-red-400 shrink-0"
                        title="Delete subtitle"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};
