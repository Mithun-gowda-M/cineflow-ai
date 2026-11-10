"use client";

import React, { useState } from "react";
import { 
  Sparkles, Mic, MicOff, Send, Sliders, Scissors, 
  Trash2, ChevronLeft, ChevronRight, Wand2, RefreshCw 
} from "lucide-react";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";
import { TimelineClip, TransitionType, ColorGradePreset } from "@/types";

interface AiDirectorDrawerProps {
  selectedClip: TimelineClip | null;
  onUpdateClip: (clipId: string, updates: Partial<TimelineClip>) => void;
  onDeleteClip: (clipId: string) => void;
  onApplyAiPlan: (instruction: string) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  globalColorGrade: ColorGradePreset;
  onUpdateGlobalColorGrade: (grade: ColorGradePreset) => void;
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
}) => {
  const [prompt, setPrompt] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSendPrompt = (textToSend?: string) => {
    const text = textToSend || prompt;
    if (!text.trim()) return;

    setIsProcessing(true);
    setTimeout(() => {
      onApplyAiPlan(text);
      setIsProcessing(false);
      setPrompt("");
    }, 600);
  };

  const toggleVoiceListen = () => {
    if (isListening) {
      setIsListening(false);
    } else {
      setIsListening(true);
      // Simulate speech-to-text transcription
      setTimeout(() => {
        setPrompt("Make cuts faster and apply Golden Hour grading");
        setIsListening(false);
      }, 2500);
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
          <span className="text-purple-400 font-mono">Llama 3.2 + Heuristic</span>
        </div>

        <div className="relative">
          <textarea
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Snap cuts to the drum drops and slow down the fireworks..."
            className="w-full p-2.5 rounded-lg bg-cine-black border border-cine-border text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cine-gold-500 resize-none font-sans"
          />
          {isListening && (
            <div className="absolute top-2 right-2 flex items-center gap-1 text-[10px] text-red-400 bg-red-500/10 px-2 py-0.5 rounded animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400" /> Listening...
            </div>
          )}
        </div>

        <div className="flex items-center justify-between gap-2">
          {/* Voice Microphone Button */}
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

          {/* Send / Apply Prompt */}
          <GoldButton
            size="sm"
            onClick={() => handleSendPrompt()}
            disabled={isProcessing || !prompt.trim()}
            icon={isProcessing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
          >
            {isProcessing ? "Re-Planning..." : "Direct Cut"}
          </GoldButton>
        </div>

        {/* Quick Recipe Chips */}
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] text-gray-500 uppercase font-semibold">Quick Directing Recipes:</span>
          <div className="flex flex-col gap-1.5">
            {[
              "Golden hour grading + slow dramatic intro",
              "Fast cuts on drum drops + 9:16 vertical conforming",
              "Subtle crossfades + emotional ending deceleration",
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

            {/* Playback Speed Ramp */}
            <div>
              <div className="flex items-center justify-between text-xs text-gray-300 mb-1">
                <span>Speed Ramp:</span>
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

            {/* Transition Selector */}
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

            {/* Delete Clip */}
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
      </div>
    </aside>
  );
};

