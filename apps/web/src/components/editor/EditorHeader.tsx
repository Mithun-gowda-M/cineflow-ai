"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  Film, Undo2, Redo2, Download, ArrowLeft, 
  Sparkles, CheckCircle2, SlidersHorizontal 
} from "lucide-react";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";
import { AspectRatio, ColorGradePreset } from "@/types";
import { formatTimecode } from "@/lib/utils";

interface EditorHeaderProps {
  title: string;
  onTitleChange: (newTitle: string) => void;
  aspectRatio: AspectRatio;
  onAspectRatioChange: (ratio: AspectRatio) => void;
  currentTime: number;
  totalDuration: number;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  onOpenExport: () => void;
}

export const EditorHeader: React.FC<EditorHeaderProps> = ({
  title,
  onTitleChange,
  aspectRatio,
  onAspectRatioChange,
  currentTime,
  totalDuration,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  onOpenExport,
}) => {
  const [isEditingTitle, setIsEditingTitle] = useState(false);

  return (
    <header className="h-14 bg-cine-surface border-b border-cine-border px-4 flex items-center justify-between shrink-0 select-none">
      {/* Left: Back & Title */}
      <div className="flex items-center gap-3">
        <Link
          href="/dashboard"
          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
          title="Back to Dashboard"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>

        <div className="h-4 w-[1px] bg-cine-border" />

        {isEditingTitle ? (
          <input
            type="text"
            value={title}
            onChange={(e) => onTitleChange(e.target.value)}
            onBlur={() => setIsEditingTitle(false)}
            onKeyDown={(e) => e.key === "Enter" && setIsEditingTitle(false)}
            autoFocus
            className="bg-cine-black px-2 py-1 rounded border border-cine-gold-500 text-sm font-semibold text-white focus:outline-none"
          />
        ) : (
          <div
            onClick={() => setIsEditingTitle(true)}
            className="flex items-center gap-2 cursor-pointer group"
          >
            <h1 className="text-sm font-bold text-white group-hover:text-cine-gold-300 transition-colors">
              {title}
            </h1>
            <span className="text-[10px] text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">
              (click to edit)
            </span>
          </div>
        )}

        <Badge variant="emerald" className="hidden sm:inline-flex text-[10px]">
          <CheckCircle2 className="w-3 h-3" /> Auto-Saved
        </Badge>
      </div>

      {/* Center: Timecode & Undo/Redo & Aspect Ratio */}
      <div className="flex items-center gap-4">
        {/* Aspect Ratio Selector */}
        <div className="flex items-center gap-1 bg-cine-black/70 p-1 rounded-lg border border-cine-border text-xs">
          {(["16:9", "9:16", "1:1", "21:9"] as AspectRatio[]).map((r) => (
            <button
              key={r}
              onClick={() => onAspectRatioChange(r)}
              className={`px-2 py-0.5 rounded font-mono text-[11px] transition-colors ${
                aspectRatio === r
                  ? "bg-cine-gold-500 text-cine-black font-bold shadow-gold-sm"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        {/* Timecode Readout */}
        <div className="hidden md:flex items-center gap-1 px-3 py-1 rounded-lg bg-cine-black border border-cine-border font-mono text-xs">
          <span className="text-cine-cyan-400 font-bold">{formatTimecode(currentTime)}</span>
          <span className="text-gray-500">/</span>
          <span className="text-gray-400">{formatTimecode(totalDuration)}</span>
        </div>

        {/* Undo / Redo */}
        <div className="flex items-center gap-1">
          <button
            onClick={onUndo}
            disabled={!canUndo}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:pointer-events-none transition-colors"
            title="Undo (Ctrl+Z)"
          >
            <Undo2 className="w-4 h-4" />
          </button>
          <button
            onClick={onRedo}
            disabled={!canRedo}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:pointer-events-none transition-colors"
            title="Redo (Ctrl+Y)"
          >
            <Redo2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Right: Export Button */}
      <div className="flex items-center gap-3">
        <GoldButton
          size="sm"
          icon={<Download className="w-4 h-4" />}
          onClick={onOpenExport}
          className="shadow-gold-sm"
        >
          Export Video
        </GoldButton>
      </div>
    </header>
  );
};
