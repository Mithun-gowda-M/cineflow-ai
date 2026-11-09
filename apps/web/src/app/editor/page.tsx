"use client";

import React, { useState, useEffect, useRef } from "react";
import { EditorHeader } from "@/components/editor/EditorHeader";
import { MediaLibraryDrawer } from "@/components/editor/MediaLibraryDrawer";
import { VideoPreviewCanvas } from "@/components/editor/VideoPreviewCanvas";
import { AiDirectorDrawer } from "@/components/editor/AiDirectorDrawer";
import { MultiTrackTimeline } from "@/components/editor/MultiTrackTimeline";
import { ExportModal } from "@/components/editor/ExportModal";
import { AspectRatio, ColorGradePreset, TimelineClip, SubtitleCue } from "@/types";

export default function EditorStudioPage() {
  const [projectTitle, setProjectTitle] = useState("Deepavali 2026 Festival Highlights");
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>("16:9");
  const [colorGrade, setColorGrade] = useState<ColorGradePreset>("golden_hour");
  const [totalDuration, setTotalDuration] = useState<number>(30.0); // 30s initial sequence
  const [currentTime, setCurrentTime] = useState<number>(0.0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [selectedClipId, setSelectedClipId] = useState<string | null>("clip_v1_01");

  const [isMediaDrawerCollapsed, setIsMediaDrawerCollapsed] = useState<boolean>(false);
  const [isAiDrawerCollapsed, setIsAiDrawerCollapsed] = useState<boolean>(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState<boolean>(false);

  // Initial timeline clips (realistic demo project data)
  const [clips, setClips] = useState<TimelineClip[]>([
    {
      id: "clip_v1_01",
      title: "Diya Lighting Macro (Intro Hook)",
      sourceUrl: "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1200&q=80",
      thumbnailUrl: "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=400&q=80",
      trackId: "v1",
      startTime: 0.0,
      duration: 6.0,
      trimStart: 0.0,
      trimEnd: 6.0,
      speed: 1.0,
      transition: "fade_from_black",
      qualityScore: 94,
      tags: ["Diya", "Macro", "Warm"],
    },
    {
      id: "clip_v1_02",
      title: "Auditorium Crowd Cheering",
      sourceUrl: "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=1200&q=80",
      thumbnailUrl: "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=400&q=80",
      trackId: "v1",
      startTime: 6.0,
      duration: 7.5,
      trimStart: 0.0,
      trimEnd: 7.5,
      speed: 1.0,
      transition: "crossfade",
      qualityScore: 86,
      tags: ["Crowd", "High-Energy"],
    },
    {
      id: "clip_v1_03",
      title: "Fireworks Sky Climax Burst",
      sourceUrl: "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?auto=format&fit=crop&w=1200&q=80",
      thumbnailUrl: "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?auto=format&fit=crop&w=400&q=80",
      trackId: "v1",
      startTime: 13.5,
      duration: 8.5,
      trimStart: 0.0,
      trimEnd: 8.5,
      speed: 1.25,
      transition: "zoom_in",
      qualityScore: 91,
      tags: ["Fireworks", "Action"],
    },
    {
      id: "clip_v1_04",
      title: "Campus Sunset Drone Finale",
      sourceUrl: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
      thumbnailUrl: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=400&q=80",
      trackId: "v1",
      startTime: 22.0,
      duration: 8.0,
      trimStart: 0.0,
      trimEnd: 8.0,
      speed: 0.8,
      transition: "fade_to_black",
      qualityScore: 98,
      tags: ["Sunset", "Drone"],
    },
    {
      id: "clip_v2_broll_01",
      title: "Rangoli Flower Cutaway",
      sourceUrl: "https://images.unsplash.com/photo-1605647540924-852290f6b0d5?auto=format&fit=crop&w=1200&q=80",
      thumbnailUrl: "https://images.unsplash.com/photo-1605647540924-852290f6b0d5?auto=format&fit=crop&w=400&q=80",
      trackId: "v2",
      startTime: 8.0,
      duration: 3.5,
      trimStart: 0.0,
      trimEnd: 3.5,
      speed: 1.0,
      transition: "crossfade",
      qualityScore: 95,
      tags: ["Rangoli", "Detail"],
    },
    {
      id: "clip_a1_voice_01",
      title: "Student Presidential Welcome",
      sourceUrl: "",
      thumbnailUrl: "",
      trackId: "a1",
      startTime: 1.5,
      duration: 5.0,
      trimStart: 0.0,
      trimEnd: 5.0,
      speed: 1.0,
      transition: "none",
      qualityScore: 92,
      tags: ["Voice", "Speech"],
    },
  ]);

  const [subtitles, setSubtitles] = useState<SubtitleCue[]>([
    {
      id: "sub_01",
      startTime: 1.5,
      duration: 4.5,
      text: "When tradition ignites the festival night",
      style: "cinematic_gold_bottom",
    },
    {
      id: "sub_02",
      startTime: 14.0,
      duration: 6.0,
      text: "Lighting the skies across BMSIT Campus",
      style: "cinematic_gold_bottom",
    },
  ]);

  // History Stack for functional Undo / Redo
  const [history, setHistory] = useState<TimelineClip[][]>([]);
  const [redoStack, setRedoStack] = useState<TimelineClip[][]>([]);

  const pushHistorySnapshot = (newClips: TimelineClip[]) => {
    setHistory((prev) => [...prev, clips]);
    setRedoStack([]);
    setClips(newClips);
  };

  const handleUndo = () => {
    if (history.length === 0) return;
    const previous = history[history.length - 1];
    setRedoStack((prev) => [...prev, clips]);
    setHistory((prev) => prev.slice(0, prev.length - 1));
    setClips(previous);
  };

  const handleRedo = () => {
    if (redoStack.length === 0) return;
    const next = redoStack[redoStack.length - 1];
    setHistory((prev) => [...prev, clips]);
    setRedoStack((prev) => prev.slice(0, prev.length - 1));
    setClips(next);
  };

  // Playback timer ticker
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentTime((prev) => {
          if (prev >= totalDuration) {
            setIsPlaying(false);
            return 0;
          }
          return Number((prev + 0.1).toFixed(2));
        });
      }, 100);
    }
    return () => clearInterval(interval);
  }, [isPlaying, totalDuration]);

  // Keyboard shortcut listener (Space to play/pause, Ctrl+Z / Ctrl+Y)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      if (e.code === "Space") {
        e.preventDefault();
        setIsPlaying((p) => !p);
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) {
          handleRedo();
        } else {
          handleUndo();
        }
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
        e.preventDefault();
        handleRedo();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [history, redoStack, clips]);

  // Selected Clip object
  const selectedClip = clips.find((c) => c.id === selectedClipId) || null;

  // Actions
  const handleUpdateClip = (clipId: string, updates: Partial<TimelineClip>) => {
    const updated = clips.map((c) => (c.id === clipId ? { ...c, ...updates } : c));
    pushHistorySnapshot(updated);
  };

  const handleDeleteClip = (clipId: string) => {
    const updated = clips.filter((c) => c.id !== clipId);
    pushHistorySnapshot(updated);
    if (selectedClipId === clipId) setSelectedClipId(null);
  };

  const handleAddClip = (newClipPartial: Partial<TimelineClip>) => {
    const targetTrack = newClipPartial.trackId || "v1";
    const trackClips = clips.filter((c) => c.trackId === targetTrack);
    const lastClip = trackClips[trackClips.length - 1];
    const newStartTime = lastClip ? lastClip.startTime + lastClip.duration : 0.0;
    const clipDur = newClipPartial.duration || 4.0;

    const newClip: TimelineClip = {
      id: `clip_${Date.now()}`,
      title: newClipPartial.title || "New Media Clip",
      sourceUrl: newClipPartial.sourceUrl || "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=800&q=80",
      thumbnailUrl: newClipPartial.thumbnailUrl || "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=400&q=80",
      trackId: targetTrack,
      startTime: newStartTime,
      duration: clipDur,
      trimStart: 0.0,
      trimEnd: clipDur,
      speed: 1.0,
      transition: "crossfade",
      qualityScore: newClipPartial.qualityScore || 90,
      tags: newClipPartial.tags || ["Imported"],
    };

    const updated = [...clips, newClip];
    pushHistorySnapshot(updated);
    if (newStartTime + clipDur > totalDuration) {
      setTotalDuration(newStartTime + clipDur);
    }
    setSelectedClipId(newClip.id);
  };

  // AI Directing Engine callback
  const handleApplyAiPlan = (instruction: string) => {
    const lower = instruction.toLowerCase();

    // 1. Color Grading Detection
    if (lower.includes("golden") || lower.includes("warm")) {
      setColorGrade("golden_hour");
    } else if (lower.includes("teal") || lower.includes("contrast") || lower.includes("cinema")) {
      setColorGrade("cinematic_teal_orange");
    } else if (lower.includes("dark") || lower.includes("moody")) {
      setColorGrade("moody_dark");
    }

    // 2. Aspect Ratio Detection
    if (lower.includes("9:16") || lower.includes("reel") || lower.includes("shorts") || lower.includes("vertical")) {
      setAspectRatio("9:16");
    } else if (lower.includes("16:9") || lower.includes("landscape") || lower.includes("youtube")) {
      setAspectRatio("16:9");
    }

    // 3. Pacing & Speed Alterations
    let updated = [...clips];
    if (lower.includes("fast") || lower.includes("speed up") || lower.includes("energy")) {
      updated = updated.map((c) => ({
        ...c,
        speed: c.tags.includes("Action") || c.tags.includes("Fireworks") ? 1.5 : 1.25,
        duration: Number((c.duration * 0.85).toFixed(1)),
      }));
    } else if (lower.includes("slow") || lower.includes("dramatic")) {
      updated = updated.map((c) => ({
        ...c,
        speed: c.tags.includes("Warm") || c.tags.includes("Sunset") ? 0.75 : 1.0,
      }));
    }

    // Recalculate start times sequentially for V1
    let v1Time = 0.0;
    updated = updated.map((c) => {
      if (c.trackId === "v1") {
        const item = { ...c, startTime: v1Time };
        v1Time = Number((v1Time + c.duration).toFixed(1));
        return item;
      }
      return c;
    });

    pushHistorySnapshot(updated);
    setTotalDuration(Math.max(30.0, v1Time));
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-cine-black overflow-hidden select-none">
      {/* Top Header */}
      <EditorHeader
        title={projectTitle}
        onTitleChange={setProjectTitle}
        aspectRatio={aspectRatio}
        onAspectRatioChange={setAspectRatio}
        currentTime={currentTime}
        totalDuration={totalDuration}
        canUndo={history.length > 0}
        canRedo={redoStack.length > 0}
        onUndo={handleUndo}
        onRedo={handleRedo}
        onOpenExport={() => setIsExportModalOpen(true)}
      />

      {/* Main Studio Middle Section: Left Media, Center Canvas, Right AI Director */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Drawer: Media Library */}
        <MediaLibraryDrawer
          onAddClip={handleAddClip}
          isCollapsed={isMediaDrawerCollapsed}
          onToggleCollapse={() => setIsMediaDrawerCollapsed(!isMediaDrawerCollapsed)}
        />

        {/* Center: Video Preview Canvas */}
        <VideoPreviewCanvas
          aspectRatio={aspectRatio}
          colorGrade={colorGrade}
          currentTime={currentTime}
          totalDuration={totalDuration}
          isPlaying={isPlaying}
          onTogglePlay={() => setIsPlaying(!isPlaying)}
          onSeek={setCurrentTime}
          clips={clips}
          subtitles={subtitles}
        />

        {/* Right Drawer: AI Director Copilot & Inspector */}
        <AiDirectorDrawer
          selectedClip={selectedClip}
          onUpdateClip={handleUpdateClip}
          onDeleteClip={handleDeleteClip}
          onApplyAiPlan={handleApplyAiPlan}
          isCollapsed={isAiDrawerCollapsed}
          onToggleCollapse={() => setIsAiDrawerCollapsed(!isAiDrawerCollapsed)}
          globalColorGrade={colorGrade}
          onUpdateGlobalColorGrade={setColorGrade}
        />
      </div>

      {/* Bottom: Multi-Track Timeline Canvas */}
      <MultiTrackTimeline
        clips={clips}
        subtitles={subtitles}
        currentTime={currentTime}
        totalDuration={totalDuration}
        onSeek={setCurrentTime}
        selectedClipId={selectedClipId}
        onSelectClip={(clip) => setSelectedClipId(clip.id)}
      />

      {/* Export Render Modal */}
      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        projectTitle={projectTitle}
        aspectRatio={aspectRatio}
        colorGrade={colorGrade}
        durationSeconds={totalDuration}
      />
    </div>
  );
}
