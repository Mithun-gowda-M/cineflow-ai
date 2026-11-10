"use client";

import React, { Suspense, useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { EditorHeader } from "@/components/editor/EditorHeader";
import { MediaLibraryDrawer } from "@/components/editor/MediaLibraryDrawer";
import { VideoPreviewCanvas } from "@/components/editor/VideoPreviewCanvas";
import { AiDirectorDrawer } from "@/components/editor/AiDirectorDrawer";
import { MultiTrackTimeline } from "@/components/editor/MultiTrackTimeline";
import { ExportModal } from "@/components/editor/ExportModal";
import { StyleRecipeModal } from "@/components/editor/StyleRecipeModal";
import {
  AspectRatio,
  CinematicEffects,
  ColorGradePreset,
  TimelineClip,
  SubtitleCue,
  TransitionType,
} from "@/types";
import {
  applyStyleRecipe,
  BackendAudioAnalysis,
  BackendDirectorPlanResponse,
  BackendMediaAsset,
  BackendStoryboardBeat,
  BackendStyleRecipe,
  beatSyncTimeline,
  checkBackendHealth,
  editTimelineConversationally,
  fetchBackendProject,
  generateDirectorPlan,
  getAudioAnalysis,
  listMediaAssets,
  resolveBackendUrl,
  transcribeMediaSubtitles,
} from "@/lib/api";

interface TimelineSnapshot {
  clips: TimelineClip[];
  subtitles: SubtitleCue[];
  colorGrade: ColorGradePreset;
  aspectRatio: AspectRatio;
  cinematicEffects: CinematicEffects;
  totalDuration: number;
}

function EditorStudioContent() {
  const searchParams = useSearchParams();
  const projectIdParam = searchParams.get("projectId");
  const [activeProjectId, setActiveProjectId] = useState<string>(projectIdParam || "proj_studio_01");
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

  const [storyboard, setStoryboard] = useState<BackendStoryboardBeat[]>([]);
  const [directorEngine, setDirectorEngine] = useState<"ollama" | "rule_fallback" | "demo" | null>(null);
  const [directorWarnings, setDirectorWarnings] = useState<string[]>([]);
  const [directorError, setDirectorError] = useState<string>("");
  const [cinematicEffects, setCinematicEffects] = useState<CinematicEffects>({
    vignette: false,
    filmGrain: false,
    kenBurnsOnImages: true,
    audioDucking: true,
    loudnessNormalize: true,
  });
  const [audioAnalysis, setAudioAnalysis] = useState<{
    sourceId: string;
    data: BackendAudioAnalysis;
  } | null>(null);
  const [isBeatSyncing, setIsBeatSyncing] = useState<boolean>(false);
  const [beatSyncMessage, setBeatSyncMessage] = useState<string>("");
  const [editDiffChanges, setEditDiffChanges] = useState<string[]>([]);
  const [isCaptioning, setIsCaptioning] = useState<boolean>(false);
  const [isStyleModalOpen, setIsStyleModalOpen] = useState<boolean>(false);
  const [activeStyleRecipe, setActiveStyleRecipe] = useState<BackendStyleRecipe | null>(null);

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

  // Full Multi-Property History Stack for functional Undo / Redo
  const [history, setHistory] = useState<TimelineSnapshot[]>([]);
  const [redoStack, setRedoStack] = useState<TimelineSnapshot[]>([]);

  const currentSnapshot = (): TimelineSnapshot => ({
    clips,
    subtitles,
    colorGrade,
    aspectRatio,
    cinematicEffects,
    totalDuration,
  });

  const applySnapshot = (snap: TimelineSnapshot) => {
    setClips(snap.clips);
    setSubtitles(snap.subtitles);
    setColorGrade(snap.colorGrade);
    setAspectRatio(snap.aspectRatio);
    setCinematicEffects(snap.cinematicEffects);
    setTotalDuration(snap.totalDuration);
  };

  const pushHistorySnapshot = (
    nextClipsOrPatch: TimelineClip[] | Partial<TimelineSnapshot>
  ) => {
    const patch: Partial<TimelineSnapshot> = Array.isArray(nextClipsOrPatch)
      ? { clips: nextClipsOrPatch }
      : nextClipsOrPatch;
    const prevSnap = currentSnapshot();
    setHistory((prev) => [...prev, prevSnap]);
    setRedoStack([]);
    applySnapshot({
      ...prevSnap,
      ...patch,
    });
  };

  const handleUndo = () => {
    if (history.length === 0) return;
    const previous = history[history.length - 1];
    setRedoStack((prev) => [...prev, currentSnapshot()]);
    setHistory((prev) => prev.slice(0, prev.length - 1));
    applySnapshot(previous);
  };

  const handleRedo = () => {
    if (redoStack.length === 0) return;
    const next = redoStack[redoStack.length - 1];
    setHistory((prev) => [...prev, currentSnapshot()]);
    setRedoStack((prev) => prev.slice(0, prev.length - 1));
    applySnapshot(next);
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
  });

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
      sourceId: newClipPartial.sourceId,
      mediaKind: newClipPartial.mediaKind,
      title: newClipPartial.title || "New Media Clip",
      sourceUrl: newClipPartial.sourceUrl || "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=800&q=80",
      proxyUrl: newClipPartial.proxyUrl,
      thumbnailUrl: newClipPartial.thumbnailUrl || "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=400&q=80",
      trackId: targetTrack,
      startTime: newStartTime,
      duration: clipDur,
      trimStart: newClipPartial.trimStart ?? 0.0,
      trimEnd: newClipPartial.trimEnd ?? clipDur,
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

  const hydrateTimelineSnapshot = (
    backendTimeline: BackendDirectorPlanResponse["timeline"],
    assetById: Map<string, BackendMediaAsset>
  ): TimelineSnapshot => {
    const nextClips: TimelineClip[] = backendTimeline.video_clips.map((vc) => {
      const asset = assetById.get(vc.source_id);
      return {
        id: vc.clip_id,
        sourceId: vc.source_id,
        mediaKind: asset?.media_kind || "video",
        title: vc.source_filename || asset?.original_filename || vc.source_id,
        sourceUrl: resolveBackendUrl(vc.source_url || asset?.source_url),
        proxyUrl: resolveBackendUrl(asset?.proxy_url),
        thumbnailUrl:
          resolveBackendUrl(vc.thumbnail_url || asset?.thumbnail_url) ||
          "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=400&q=80",
        trackId: "v1",
        startTime: vc.timeline_start_seconds,
        duration: vc.duration_seconds,
        trimStart: vc.start_time_seconds,
        trimEnd: vc.end_time_seconds,
        speed: vc.playback_speed,
        speedRamp: vc.speed_ramp || "none",
        transition: (vc.transition_in?.type as TransitionType) || "crossfade",
        qualityScore: vc.quality_score ?? 85,
        tags: vc.tags,
      };
    });

    for (const ac of backendTimeline.audio_tracks) {
      const asset = assetById.get(ac.source_id);
      if (asset?.audio_analysis) {
        setAudioAnalysis({ sourceId: ac.source_id, data: asset.audio_analysis });
      }
      nextClips.push({
        id: ac.id,
        sourceId: ac.source_id,
        mediaKind: "audio",
        title: ac.name,
        sourceUrl: resolveBackendUrl(ac.source_url || asset?.source_url),
        thumbnailUrl: "",
        trackId: "a2",
        startTime: ac.timeline_start_seconds,
        duration: ac.duration_seconds,
        trimStart: ac.start_time_seconds,
        trimEnd: ac.start_time_seconds + ac.duration_seconds,
        speed: 1.0,
        transition: "none",
        qualityScore: 95,
        tags: ["Audio"],
      });
    }

    const nextSubs: SubtitleCue[] = backendTimeline.subtitles.map((s) => ({
      id: s.id,
      startTime: s.start_seconds,
      duration: Math.max(0.5, s.end_seconds - s.start_seconds),
      text: s.text,
      style: s.style,
    }));

    return {
      clips: nextClips,
      subtitles: nextSubs,
      colorGrade: backendTimeline.color_grade,
      aspectRatio: backendTimeline.aspect_ratio,
      cinematicEffects: backendTimeline.cinematic_effects
        ? {
            vignette: backendTimeline.cinematic_effects.vignette,
            filmGrain: backendTimeline.cinematic_effects.film_grain,
            kenBurnsOnImages: backendTimeline.cinematic_effects.ken_burns_on_images,
            audioDucking: backendTimeline.cinematic_effects.audio_ducking,
            loudnessNormalize: backendTimeline.cinematic_effects.loudness_normalize,
          }
        : cinematicEffects,
      totalDuration: Math.max(5.0, backendTimeline.target_duration_seconds),
    };
  };

  // AI Directing Engine callback (real FastAPI planner when media & backend are ready, else local demo adjustment)
  const handleApplyAiPlan = async (instruction: string) => {
    setDirectorError("");
    setEditDiffChanges([]);
    const health = await checkBackendHealth();
    if (health) {
      try {
        const backendAssets = await listMediaAssets();
        const hasVisual = backendAssets.some((a) => a.media_kind === "video" || a.media_kind === "image");
        if (hasVisual) {
          const assetById = new Map(backendAssets.map((a) => [a.id, a]));
          const plan = await generateDirectorPlan({
            projectId: activeProjectId,
            instruction,
            styleRecipeId: activeStyleRecipe?.id,
          });
          const snap = hydrateTimelineSnapshot(plan.timeline, assetById);
          pushHistorySnapshot(snap);
          setProjectTitle(plan.timeline.title);
          setStoryboard(plan.storyboard);
          setDirectorEngine(plan.engine_used);
          setDirectorWarnings(plan.warnings);
          if (snap.clips.length > 0) setSelectedClipId(snap.clips[0].id);
          return;
        }
      } catch (err) {
        setDirectorError(err instanceof Error ? err.message : "AI Director request failed.");
        return;
      }
    }

    // Demo fallback when working with placeholder demo clips or offline backend
    const lower = instruction.toLowerCase();
    if (lower.includes("golden") || lower.includes("warm")) {
      setColorGrade("golden_hour");
    } else if (lower.includes("teal") || lower.includes("contrast") || lower.includes("cinema")) {
      setColorGrade("cinematic_teal_orange");
    } else if (lower.includes("dark") || lower.includes("moody")) {
      setColorGrade("moody_dark");
    }

    if (lower.includes("9:16") || lower.includes("reel") || lower.includes("shorts") || lower.includes("vertical")) {
      setAspectRatio("9:16");
    } else if (lower.includes("16:9") || lower.includes("landscape") || lower.includes("youtube")) {
      setAspectRatio("16:9");
    }

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
    setDirectorEngine("demo");
    setDirectorWarnings(["Demo mode active: upload footage in Media Hub to run full AI storyboarding."]);
  };

  // Phase 6 Conversational Editing handler (diff calculator + Undo/Redo snapshot)
  const handleApplyConversationalEdit = async (instruction: string) => {
    setDirectorError("");
    const hasRealVisual = clips.some(
      (c) => (c.trackId === "v1" || c.trackId === "v2") && Boolean(c.sourceId)
    );
    const health = hasRealVisual ? await checkBackendHealth() : null;

    if (health && hasRealVisual) {
      try {
        const backendAssets = await listMediaAssets();
        const assetById = new Map(backendAssets.map((a) => [a.id, a]));
        const editRes = await editTimelineConversationally({
          projectId: activeProjectId,
          instruction,
          title: projectTitle,
          aspectRatio,
          colorGrade,
          clips,
          subtitles,
          cinematicEffects,
        });
        const snap = hydrateTimelineSnapshot(editRes.timeline, assetById);
        pushHistorySnapshot(snap);
        setEditDiffChanges(
          editRes.diff.changes.length > 0 ? editRes.diff.changes : editRes.operations_applied
        );
        setDirectorEngine(editRes.engine_used);
        setDirectorWarnings(editRes.warnings);
        return;
      } catch (err) {
        setDirectorError(err instanceof Error ? err.message : "Conversational edit failed.");
        return;
      }
    }

    // Demo placeholder fallback for iterative edits
    const lower = instruction.toLowerCase();
    const nextPatch: Partial<TimelineSnapshot> = {};
    const localDiffs: string[] = [];
    if (lower.includes("bleach")) {
      nextPatch.colorGrade = "bleach_bypass";
      localDiffs.push("Changed color grade to 'bleach_bypass'");
    } else if (lower.includes("golden") || lower.includes("warm")) {
      nextPatch.colorGrade = "golden_hour";
      localDiffs.push("Changed color grade to 'golden_hour'");
    } else if (lower.includes("teal")) {
      nextPatch.colorGrade = "cinematic_teal_orange";
      localDiffs.push("Changed color grade to 'cinematic_teal_orange'");
    }
    if (lower.includes("vignette")) {
      const enable = !lower.includes("remove") && !lower.includes("disable");
      nextPatch.cinematicEffects = { ...cinematicEffects, vignette: enable };
      localDiffs.push(`${enable ? "Enabled" : "Disabled"} optical vignette`);
    }
    if (lower.includes("grain")) {
      const enable = !lower.includes("remove") && !lower.includes("disable");
      nextPatch.cinematicEffects = {
        ...(nextPatch.cinematicEffects || cinematicEffects),
        filmGrain: enable,
      };
      localDiffs.push(`${enable ? "Enabled" : "Disabled"} 35mm film grain`);
    }
    if (lower.includes("9:16") || lower.includes("vertical") || lower.includes("reel")) {
      nextPatch.aspectRatio = "9:16";
      localDiffs.push("Switched aspect ratio to 9:16");
    } else if (lower.includes("16:9") || lower.includes("landscape")) {
      nextPatch.aspectRatio = "16:9";
      localDiffs.push("Switched aspect ratio to 16:9");
    }
    if (lower.includes("faster") || lower.includes("speed up")) {
      const sped = clips.map((c) =>
        c.trackId === "v1"
          ? { ...c, speed: Math.min(2.5, Number((c.speed * 1.25).toFixed(2))), duration: Number((c.duration * 0.8).toFixed(1)) }
          : c
      );
      nextPatch.clips = sped;
      localDiffs.push("Accelerated timeline pacing");
    }
    if (localDiffs.length > 0) {
      pushHistorySnapshot(nextPatch);
      setEditDiffChanges(localDiffs);
      setDirectorEngine("demo");
    } else {
      setDirectorWarnings(["Demo mode: try 'Change to bleach bypass', 'Add vignette', 'Make it faster', or upload clips for full asset replacement."]);
    }
  };

  const captionCandidateClip =
    (selectedClip && selectedClip.sourceId && selectedClip.mediaKind !== "image"
      ? selectedClip
      : clips.find((c) => Boolean(c.sourceId) && c.mediaKind !== "image")) || null;

  const handleAutoCaption = async () => {
    if (!captionCandidateClip?.sourceId) return;
    setIsCaptioning(true);
    setDirectorError("");
    try {
      const res = await transcribeMediaSubtitles(captionCandidateClip.sourceId);
      const offset = captionCandidateClip.trackId === "v1" ? captionCandidateClip.startTime : 0.0;
      const newCues: SubtitleCue[] = res.suggested_subtitles.map((s) => ({
        id: s.id,
        startTime: Number((s.start_seconds + offset).toFixed(2)),
        duration: Math.max(0.5, Number((s.end_seconds - s.start_seconds).toFixed(2))),
        text: s.text,
        style: s.style,
      }));
      if (newCues.length > 0) {
        pushHistorySnapshot({ subtitles: [...subtitles, ...newCues] });
        setEditDiffChanges([`Added ${newCues.length} Whisper subtitle cue(s) from '${captionCandidateClip.title}'`]);
      } else {
        setDirectorWarnings(["Whisper found no spoken words in selected clip."]);
      }
    } catch (err) {
      setDirectorError(err instanceof Error ? err.message : "Auto-captioning failed.");
    } finally {
      setIsCaptioning(false);
    }
  };

  useEffect(() => {
    const audioClip = clips.find((c) => c.trackId === "a2" && Boolean(c.sourceId));
    if (!audioClip?.sourceId) return;
    if (audioAnalysis && audioAnalysis.sourceId === audioClip.sourceId) return;

    let cancelled = false;
    checkBackendHealth().then((health) => {
      if (!health || cancelled) return;
      getAudioAnalysis(audioClip.sourceId!)
        .then((res) => {
          if (!cancelled) setAudioAnalysis({ sourceId: audioClip.sourceId!, data: res });
        })
        .catch(() => {});
    });
    return () => {
      cancelled = true;
    };
  }, [clips, audioAnalysis]);

  // Hydrate persisted backend project (e.g. ?projectId=proj_bmsit_showcase_2026 from Showcase or Dashboard)
  useEffect(() => {
    if (!projectIdParam) return;
    let cancelled = false;
    setActiveProjectId(projectIdParam);

    Promise.all([fetchBackendProject(projectIdParam), listMediaAssets()])
      .then(([proj, backendAssets]) => {
        if (cancelled) return;
        const assetById = new Map(backendAssets.map((a) => [a.id, a]));
        setProjectTitle(proj.title);
        setAspectRatio(proj.aspect_ratio);
        setColorGrade(proj.color_grade);
        setTotalDuration(Math.max(5.0, proj.target_duration_seconds));

        if (proj.timeline) {
          const snap = hydrateTimelineSnapshot(proj.timeline, assetById);
          setClips(snap.clips);
          setSubtitles(snap.subtitles);
          setColorGrade(snap.colorGrade);
          setAspectRatio(snap.aspectRatio);
          setCinematicEffects(snap.cinematicEffects);
          setTotalDuration(snap.totalDuration);
          setHistory([]);
          setRedoStack([]);
          if (snap.clips.length > 0) setSelectedClipId(snap.clips[0].id);
          setEditDiffChanges([`Hydrated live project '${proj.title}' (${snap.clips.length} tracks/clips)`]);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setDirectorError(err instanceof Error ? err.message : "Failed to load project from backend.");
        }
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectIdParam]);

  const primaryAudioSourceId = clips.find((c) => c.trackId === "a2" && Boolean(c.sourceId))?.sourceId;

  const handleSnapToBeats = async () => {
    if (!primaryAudioSourceId) return;
    setIsBeatSyncing(true);
    setBeatSyncMessage("");
    try {
      const synced = await beatSyncTimeline({
        projectId: activeProjectId,
        title: projectTitle,
        aspectRatio,
        colorGrade,
        clips,
        audioSourceId: primaryAudioSourceId,
        subtitles,
        cinematicEffects,
      });
      const syncedById = new Map(synced.timeline.video_clips.map((vc) => [vc.clip_id, vc]));
      const nextClips = clips.map((clip) => {
        const match = syncedById.get(clip.id);
        if (!match) return clip;
        return {
          ...clip,
          startTime: match.timeline_start_seconds,
          duration: match.duration_seconds,
          trimStart: match.start_time_seconds,
          trimEnd: match.end_time_seconds,
        };
      });
      pushHistorySnapshot({
        clips: nextClips,
        totalDuration: Math.max(5.0, synced.timeline.target_duration_seconds),
      });
      setBeatSyncMessage(
        `Aligned ${synced.snapped_cuts} cut(s) to ${Math.round(synced.tempo_bpm)} BPM`
      );
    } catch (err) {
      setBeatSyncMessage(err instanceof Error ? err.message : "Beat-sync failed.");
    } finally {
      setIsBeatSyncing(false);
    }
  };

  const handleAddSubtitle = (text: string, style: SubtitleCue["style"]) => {
    const startTime = Math.max(0, Number(currentTime.toFixed(2)));
    const newSub: SubtitleCue = {
      id: `sub_${Date.now()}`,
      startTime,
      duration: 3.5,
      text,
      style,
    };
    pushHistorySnapshot({ subtitles: [...subtitles, newSub] });
  };

  const handleDeleteSubtitle = (id: string) => {
    pushHistorySnapshot({ subtitles: subtitles.filter((s) => s.id !== id) });
  };

  const handleApplyStyleRecipe = async (recipe: BackendStyleRecipe) => {
    setActiveStyleRecipe(recipe);
    setDirectorError("");
    const hasRealVisual = clips.some(
      (c) => (c.trackId === "v1" || c.trackId === "v2") && Boolean(c.sourceId)
    );
    const health = hasRealVisual ? await checkBackendHealth() : null;

    if (health && hasRealVisual) {
      try {
        const backendAssets = await listMediaAssets();
        const assetById = new Map(backendAssets.map((a) => [a.id, a]));
        const applied = await applyStyleRecipe({
          recipeId: recipe.id,
          projectId: activeProjectId,
          title: projectTitle,
          aspectRatio,
          colorGrade,
          clips,
          subtitles,
          cinematicEffects,
        });
        const snap = hydrateTimelineSnapshot(applied.timeline, assetById);
        pushHistorySnapshot(snap);
        setEditDiffChanges(applied.changes_applied);
        return;
      } catch (err) {
        setDirectorError(err instanceof Error ? err.message : "Failed to apply style recipe.");
        return;
      }
    }

    // Demo fallback / offline application of abstract style parameters
    const styledClips = clips.map((c, idx) =>
      c.trackId === "v1"
        ? {
            ...c,
            speedRamp: idx > 0 ? recipe.recommended_speed_ramp : c.speedRamp,
            transition: (idx > 0 ? (recipe.recommended_transition as TransitionType) : c.transition),
          }
        : c
    );
    pushHistorySnapshot({
      clips: styledClips,
      colorGrade: recipe.recommended_color_grade,
      aspectRatio: recipe.recommended_aspect_ratio,
      cinematicEffects: {
        vignette: recipe.cinematic_effects.vignette,
        filmGrain: recipe.cinematic_effects.film_grain,
        kenBurnsOnImages: recipe.cinematic_effects.ken_burns_on_images,
        audioDucking: recipe.cinematic_effects.audio_ducking,
        loudnessNormalize: recipe.cinematic_effects.loudness_normalize,
      },
    });
    setEditDiffChanges([`Applied Style Recipe '${recipe.name}' (${recipe.cuts_per_minute.toFixed(0)} cuts/min)`]);
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
          cinematicEffects={cinematicEffects}
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
          onApplyConversationalEdit={handleApplyConversationalEdit}
          editDiffChanges={editDiffChanges}
          isCollapsed={isAiDrawerCollapsed}
          onToggleCollapse={() => setIsAiDrawerCollapsed(!isAiDrawerCollapsed)}
          globalColorGrade={colorGrade}
          onUpdateGlobalColorGrade={(g) => pushHistorySnapshot({ colorGrade: g })}
          cinematicEffects={cinematicEffects}
          onUpdateCinematicEffects={(updates) =>
            pushHistorySnapshot({ cinematicEffects: { ...cinematicEffects, ...updates } })
          }
          onSnapToBeats={handleSnapToBeats}
          hasAudioTrack={Boolean(primaryAudioSourceId)}
          isBeatSyncing={isBeatSyncing}
          beatSyncMessage={beatSyncMessage}
          subtitles={subtitles}
          onAddSubtitle={handleAddSubtitle}
          onDeleteSubtitle={handleDeleteSubtitle}
          onAutoCaption={handleAutoCaption}
          canAutoCaption={Boolean(captionCandidateClip)}
          isCaptioning={isCaptioning}
          onOpenStyleRecipes={() => setIsStyleModalOpen(true)}
          activeStyleRecipeName={activeStyleRecipe?.name || null}
          storyboard={storyboard}
          directorEngine={directorEngine}
          directorWarnings={directorWarnings}
          directorError={directorError}
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
        waveformPeaks={audioAnalysis?.data.waveform_peaks}
        beatTimestamps={audioAnalysis?.data.beat_timestamps}
        tempoBpm={audioAnalysis?.data.tempo_bpm}
      />

      {/* Export Render Modal */}
      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        projectTitle={projectTitle}
        aspectRatio={aspectRatio}
        colorGrade={colorGrade}
        durationSeconds={totalDuration}
        clips={clips}
        subtitles={subtitles}
        cinematicEffects={cinematicEffects}
      />

      {/* Phase 7 Trend Intelligence & Style Recipes Modal */}
      <StyleRecipeModal
        isOpen={isStyleModalOpen}
        onClose={() => setIsStyleModalOpen(false)}
        activeRecipeId={activeStyleRecipe?.id || null}
        onApplyRecipe={handleApplyStyleRecipe}
        onSelectForDirector={(recipe) => setActiveStyleRecipe(recipe)}
      />
    </div>
  );
}

export default function EditorStudioPage() {
  return (
    <Suspense
      fallback={
        <div className="h-screen w-screen flex items-center justify-center bg-cine-black text-cine-gold-400 text-sm">
          Loading CINEFLOW Studio Workspace...
        </div>
      }
    >
      <EditorStudioContent />
    </Suspense>
  );
}

