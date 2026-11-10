"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  UploadCloud,
  Trash2,
  Filter,
  ArrowRight,
  Scan,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Search,
  Copy,
  Layers,
} from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";
import { UploadedMediaItem } from "@/types";
import {
  analyzeAllMedia,
  BackendMediaAsset,
  checkBackendHealth,
  deleteMediaAsset,
  listMediaAssets,
  resolveBackendUrl,
  searchMediaAssets,
  uploadMediaBatch,
} from "@/lib/api";

const DEMO_MEDIA: (UploadedMediaItem & { isDemo?: boolean; codec?: string })[] = [
  {
    id: "m_diya_01",
    filename: "diya_lighting_macro_4k.mp4",
    url: "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=600&q=80",
    thumbnailUrl: "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=600&q=80",
    fileSizeMB: 48.2,
    durationSeconds: 12.4,
    resolution: "3840x2160 (4K)",
    fps: 60,
    qualityScore: 94,
    blurScore: 96,
    exposureScore: 92,
    stabilityScore: 93,
    compositionScore: 91,
    explanation: "Crisp focus (96/100); balanced exposure (92/100); steady framing.",
    dominantColors: ["#E5B869", "#24160A", "#F59E0B"],
    scenesCount: 2,
    tags: ["Diya", "Celebration", "Macro", "Warm"],
    isDemo: true,
    codec: "h264",
  },
  {
    id: "m_fireworks_02",
    filename: "sky_fireworks_burst_slowmo.mp4",
    url: "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?auto=format&fit=crop&w=600&q=80",
    thumbnailUrl: "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?auto=format&fit=crop&w=600&q=80",
    fileSizeMB: 62.1,
    durationSeconds: 15.0,
    resolution: "1920x1080",
    fps: 120,
    qualityScore: 89,
    blurScore: 91,
    exposureScore: 86,
    stabilityScore: 84,
    compositionScore: 90,
    explanation: "Crisp focus (91/100); balanced exposure (86/100); dynamic action motion.",
    dominantColors: ["#0B0D13", "#F5D485", "#38BDF8"],
    scenesCount: 3,
    tags: ["Fireworks", "Action", "Night", "Slow-Mo"],
    isDemo: true,
    codec: "h264",
  },
  {
    id: "m_rangoli_04",
    filename: "rangoli_art_wide_shot.jpg",
    url: "https://images.unsplash.com/photo-1605647540924-852290f6b0d5?auto=format&fit=crop&w=600&q=80",
    thumbnailUrl: "https://images.unsplash.com/photo-1605647540924-852290f6b0d5?auto=format&fit=crop&w=600&q=80",
    fileSizeMB: 4.8,
    durationSeconds: 0,
    resolution: "4000x3000",
    fps: 0,
    qualityScore: 96,
    blurScore: 98,
    exposureScore: 94,
    stabilityScore: 100,
    compositionScore: 95,
    explanation: "Crisp focus (98/100); balanced exposure (94/100).",
    dominantColors: ["#EC4899", "#E5B869", "#10B981"],
    scenesCount: 0,
    tags: ["Rangoli", "Color", "Photo"],
    isDemo: true,
    codec: "mjpeg",
  },
];

function mapBackendAsset(
  asset: BackendMediaAsset
): UploadedMediaItem & { isDemo?: boolean; codec?: string } {
  const res =
    asset.metadata.width > 0 && asset.metadata.height > 0
      ? `${asset.metadata.width}x${asset.metadata.height}`
      : asset.media_kind.toUpperCase();
  const q = asset.analysis?.quality;
  return {
    id: asset.id,
    filename: asset.original_filename,
    url: resolveBackendUrl(asset.proxy_url || asset.source_url),
    thumbnailUrl:
      resolveBackendUrl(asset.thumbnail_url) ||
      "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&q=80",
    fileSizeMB: Number((asset.file_size_bytes / (1024 * 1024)).toFixed(2)),
    durationSeconds: Number(asset.metadata.duration_seconds.toFixed(1)),
    resolution: res,
    fps: Math.round(asset.metadata.fps || 0),
    qualityScore: q ? Math.round(q.overall_score) : 75,
    blurScore: q ? Math.round(q.sharpness_score) : 75,
    exposureScore: q ? Math.round(q.exposure_score) : 75,
    stabilityScore: q ? Math.round(q.stability_score) : 90,
    compositionScore: q ? Math.round(q.composition_score) : 75,
    explanation: q?.explanation || "FFprobe metadata verified; click Re-Analyze for CV metrics.",
    dominantColors: q?.dominant_colors || [],
    scenesCount: asset.scenes?.length || 0,
    duplicateOfId: asset.analysis?.duplicate_of_id || null,
    similarityPercent: asset.analysis?.similarity_percent || null,
    motionIntensity: q?.motion_intensity,
    lightingMood: q?.lighting_mood,
    tags: asset.tags.length ? asset.tags : [asset.media_kind],
    isDemo: false,
    codec: asset.metadata.codec || asset.metadata.audio_codec || "",
  };
}

export default function UploadWorkspacePage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedTag, setSelectedTag] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [minQuality, setMinQuality] = useState<number>(0);
  const [excludeDuplicates, setExcludeDuplicates] = useState<boolean>(false);

  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [statusNotice, setStatusNotice] = useState<string>("");
  const [errorNotice, setErrorNotice] = useState<string>("");

  const [mediaList, setMediaList] = useState<
    (UploadedMediaItem & { isDemo?: boolean; codec?: string })[]
  >(DEMO_MEDIA);

  const refreshMediaFromBackend = async () => {
    const health = await checkBackendHealth();
    if (!health) {
      setBackendOnline(false);
      return;
    }
    setBackendOnline(true);
    try {
      const assets = await listMediaAssets();
      if (assets.length > 0) {
        setMediaList(assets.map(mapBackendAsset));
      } else {
        setMediaList(DEMO_MEDIA);
      }
    } catch {
      // Keep current list on transient fetch issue
    }
  };

  useEffect(() => {
    refreshMediaFromBackend();
  }, []);

  const handleSearch = async (queryText: string) => {
    setSearchQuery(queryText);
    if (!backendOnline) return;
    try {
      const hasReal = mediaList.some((m) => !m.isDemo);
      if (!hasReal) return;
      const resp = await searchMediaAssets({
        q: queryText,
        tag: selectedTag,
        minQuality,
        excludeDuplicates,
      });
      setMediaList(resp.results.map(mapBackendAsset));
    } catch {
      // keep existing local list
    }
  };

  const handleAnalyzeAll = async () => {
    if (!backendOnline) return;
    setIsAnalyzing(true);
    setErrorNotice("");
    try {
      const updated = await analyzeAllMedia();
      if (updated.length > 0) {
        setMediaList(updated.map(mapBackendAsset));
        setStatusNotice(
          `Completed PySceneDetect & OpenCV intelligence across ${updated.length} asset(s).`
        );
      }
    } catch (err) {
      setErrorNotice(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleFilesSelected = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    const files = Array.from(fileList);
    setErrorNotice("");
    setStatusNotice("");

    if (!backendOnline) {
      setErrorNotice(
        "FastAPI backend is offline. Start it (`uvicorn backend.api.main:app --port 8000`) to analyze and ingest real media files."
      );
      return;
    }

    setIsUploading(true);
    try {
      const result = await uploadMediaBatch(files);
      const uploadedMapped = result.uploaded.map(mapBackendAsset);
      setMediaList((prev) => {
        const realOnly = prev.filter((item) => !item.isDemo);
        return [...uploadedMapped, ...realOnly];
      });
      if (result.uploaded.length > 0) {
        setStatusNotice(
          `Ingested & analyzed ${result.uploaded.length} file(s) with FFprobe, PySceneDetect, OpenCV scoring, and perceptual deduplication.`
        );
      }
      if (result.errors.length > 0) {
        setErrorNotice(
          `Rejected ${result.errors.length} file(s): ${result.errors
            .map((e) => `${e.filename} (${e.error})`)
            .join(", ")}`
        );
      }
    } catch (err) {
      setErrorNotice(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDelete = async (id: string, isDemo?: boolean) => {
    if (isDemo) {
      setMediaList((prev) => prev.filter((item) => item.id !== id));
      return;
    }
    try {
      await deleteMediaAsset(id);
      setMediaList((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      setErrorNotice(err instanceof Error ? err.message : "Failed to delete asset.");
    }
  };

  const allTags = Array.from(new Set(mediaList.flatMap((m) => m.tags))).slice(0, 8);

  const filteredMedia = mediaList.filter((m) => {
    const matchesTag = selectedTag === "all" || m.tags.includes(selectedTag);
    const matchesScore = m.qualityScore >= minQuality;
    const matchesDup = !excludeDuplicates || !m.duplicateOfId;
    const matchesQuery =
      !searchQuery.trim() ||
      backendOnline ||
      m.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesTag && matchesScore && matchesDup && matchesQuery;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-cine-border">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Media Ingestion &amp; AI Intelligence
            </h1>
            <Badge variant={backendOnline ? "emerald" : "amber"}>
              {backendOnline ? "OpenCV + PySceneDetect Online" : "Demo Mode (Backend Offline)"}
            </Badge>
          </div>
          <p className="text-sm text-gray-400">
            Automated scene splitting, Laplacian sharpness scoring, exposure evaluation, semantic auto-tagging, and dHash duplicate detection.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {backendOnline && (
            <GoldButton
              variant="secondary"
              size="md"
              onClick={handleAnalyzeAll}
              disabled={isAnalyzing}
              icon={<RefreshCw className={`w-4 h-4 ${isAnalyzing ? "animate-spin" : ""}`} />}
            >
              {isAnalyzing ? "Analyzing..." : "Re-Analyze All"}
            </GoldButton>
          )}
          <Link href="/editor">
            <GoldButton size="md" icon={<ArrowRight className="w-4 h-4" />}>
              Open {filteredMedia.length} Clips in Editor
            </GoldButton>
          </Link>
        </div>
      </div>

      {/* Notices */}
      {statusNotice && (
        <div className="p-3 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{statusNotice}</span>
        </div>
      )}
      {errorNotice && (
        <div className="p-3 rounded-lg bg-red-500/15 border border-red-500/30 text-red-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorNotice}</span>
        </div>
      )}

      {/* Batch Drag-and-Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFilesSelected(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".mp4,.mov,.mkv,.webm,.avi,.m4v,.jpg,.jpeg,.png,.webp,.mp3,.wav,.aac,.m4a,.flac"
          className="hidden"
          onChange={(e) => handleFilesSelected(e.target.files)}
        />
        <GlassPanel
          variant="active"
          className={`p-8 text-center border-dashed border-2 transition-colors cursor-pointer group ${
            isDragging ? "border-cine-cyan-400 bg-cine-cyan-500/10" : "border-cine-gold-500/40 hover:border-cine-gold-500"
          }`}
        >
          <div className="w-16 h-16 rounded-2xl bg-cine-black border border-cine-border mx-auto flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-gold-sm">
            {isUploading ? (
              <RefreshCw className="w-8 h-8 text-cine-gold-400 animate-spin" />
            ) : (
              <UploadCloud className="w-8 h-8 text-cine-gold-400" />
            )}
          </div>
          <h3 className="text-lg font-bold text-white mb-1">
            {isUploading ? "Running PySceneDetect & OpenCV Analysis..." : "Drag & Drop Videos, Images, or Audio Here"}
          </h3>
          <p className="text-xs text-gray-400 max-w-md mx-auto mb-4">
            Accepts MP4, MOV, MKV, WebM, JPG, PNG, MP3, WAV. Automatically probes streams, splits scenes, scores focus, and flags near-duplicates.
          </p>
          <div className="flex items-center justify-center gap-3">
            <GoldButton variant="secondary" size="sm" type="button" disabled={isUploading}>
              Select Files From Device
            </GoldButton>
            <span className="text-xs text-gray-500">Zero Cloud Upload • 100% Local CV Pipeline</span>
          </div>
        </GlassPanel>
      </div>

      {/* Search, Filter and Metrics Toolbar */}
      <div className="p-4 rounded-xl bg-cine-surface border border-cine-border space-y-3">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Natural Query Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder='Search: "best fireworks", "brightest diya", "sharpest sunset"...'
              className="w-full pl-9 pr-3 py-2 rounded-lg bg-cine-black border border-cine-border text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cine-gold-500"
            />
          </div>

          <div className="flex items-center flex-wrap gap-4">
            <label className="flex items-center gap-2 text-xs text-gray-300 cursor-pointer">
              <input
                type="checkbox"
                checked={excludeDuplicates}
                onChange={(e) => setExcludeDuplicates(e.target.checked)}
                className="accent-cine-gold-500 rounded"
              />
              Hide Near-Duplicates
            </label>

            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">
                Min Quality: <strong className="text-cine-gold-400">{minQuality}%</strong>
              </span>
              <input
                type="range"
                min="0"
                max="90"
                step="5"
                value={minQuality}
                onChange={(e) => setMinQuality(Number(e.target.value))}
                className="w-28 accent-cine-gold-500 cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Tag Pills */}
        <div className="flex items-center gap-2 flex-wrap pt-2 border-t border-cine-border/50">
          <span className="text-xs text-gray-400 font-semibold flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-cine-gold-400" /> Tags:
          </span>
          {["all", ...allTags].map((tag) => (
            <button
              key={tag}
              onClick={() => setSelectedTag(tag)}
              className={`px-2.5 py-1 rounded text-xs transition-colors ${
                selectedTag === tag
                  ? "bg-cine-gold-500 text-cine-black font-semibold shadow-gold-sm"
                  : "bg-cine-card text-gray-300 hover:text-white border border-cine-border"
              }`}
            >
              {tag === "all" ? "All Tags" : tag}
            </button>
          ))}
        </div>
      </div>

      {/* Media Inspection Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>Showing {filteredMedia.length} of {mediaList.length} ranked assets</span>
          <span>Transparent Scoring: Sharpness + Exposure + Stability + Composition</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMedia.map((m) => (
            <GlassPanel
              key={m.id}
              variant="surface"
              className="overflow-hidden border-cine-border hover:border-cine-gold-500/50 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="relative aspect-video bg-black overflow-hidden">
                  <div
                    className="w-full h-full bg-cover bg-center"
                    style={{ backgroundImage: `url('${m.thumbnailUrl}')` }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-cine-black/90 via-transparent to-black/40" />

                  <div className="absolute top-2 left-2 flex items-center gap-1.5">
                    <span className="px-2 py-0.5 rounded bg-black/80 backdrop-blur-md text-[10px] font-mono text-gray-200 border border-white/10">
                      {m.resolution}
                    </span>
                    {m.fps > 0 && (
                      <span className="px-2 py-0.5 rounded bg-black/80 backdrop-blur-md text-[10px] font-mono text-cine-cyan-300 border border-white/10">
                        {m.fps} fps
                      </span>
                    )}
                  </div>

                  <div className="absolute top-2 right-2 flex items-center gap-1.5">
                    {m.isDemo && (
                      <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[9px] uppercase font-semibold">
                        Demo Data
                      </span>
                    )}
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-bold border backdrop-blur-md flex items-center gap-1 ${
                        m.qualityScore >= 80
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                          : m.qualityScore >= 55
                          ? "bg-cine-gold-500/20 text-cine-gold-400 border-cine-gold-500/40"
                          : "bg-red-500/20 text-red-400 border-red-500/40"
                      }`}
                    >
                      <Scan className="w-3 h-3" />
                      {m.qualityScore}/100
                    </span>
                  </div>

                  {/* Bottom Overlays: Duration, Scenes & Color Swatches */}
                  <div className="absolute bottom-2 inset-x-2 flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      {m.durationSeconds > 0 && (
                        <span className="text-[10px] font-mono text-gray-300 bg-black/80 px-1.5 py-0.5 rounded">
                          {m.durationSeconds}s
                        </span>
                      )}
                      {Boolean(m.scenesCount && m.scenesCount > 0) && (
                        <span className="text-[10px] font-mono text-cine-cyan-300 bg-black/80 px-1.5 py-0.5 rounded border border-cine-cyan-500/30 flex items-center gap-1">
                          <Layers className="w-2.5 h-2.5" /> {m.scenesCount} Scenes
                        </span>
                      )}
                    </div>

                    {m.dominantColors && m.dominantColors.length > 0 && (
                      <div className="flex items-center gap-1 bg-black/75 px-1.5 py-1 rounded">
                        {m.dominantColors.slice(0, 3).map((hex, idx) => (
                          <span
                            key={idx}
                            title={`Dominant palette: ${hex}`}
                            className="w-2.5 h-2.5 rounded-full border border-white/25"
                            style={{ backgroundColor: hex }}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="p-4 space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="text-sm font-semibold text-white truncate">{m.filename}</h4>
                    {m.duplicateOfId && (
                      <span
                        title={`Duplicate of ${m.duplicateOfId}`}
                        className="px-1.5 py-0.5 rounded bg-amber-500/15 border border-amber-500/30 text-amber-300 text-[10px] flex items-center gap-1 shrink-0"
                      >
                        <Copy className="w-2.5 h-2.5" /> {m.similarityPercent || 95}% Dup
                      </span>
                    )}
                  </div>

                  {/* Transparent Sub-Score Breakdown */}
                  <div className="grid grid-cols-3 gap-2 text-[11px] text-gray-400 bg-cine-black/40 p-2 rounded-lg border border-cine-border/50">
                    <div>
                      <span className="block text-[9px] text-gray-500 uppercase">Sharpness</span>
                      <span className="font-semibold text-gray-200">{m.blurScore}/100</span>
                    </div>
                    <div>
                      <span className="block text-[9px] text-gray-500 uppercase">Exposure</span>
                      <span className="font-semibold text-gray-200">{m.exposureScore}/100</span>
                    </div>
                    <div>
                      <span className="block text-[9px] text-gray-500 uppercase">Stability</span>
                      <span className="font-semibold text-gray-200">{m.stabilityScore ?? 90}/100</span>
                    </div>
                  </div>

                  {m.explanation && (
                    <p className="text-[11px] text-gray-400 leading-snug line-clamp-2">
                      {m.explanation}
                    </p>
                  )}

                  <div className="flex flex-wrap gap-1">
                    {m.tags.map((t, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-cine-surface text-[10px] text-gray-300 border border-cine-border">
                        #{t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="p-4 pt-2 border-t border-cine-border flex items-center justify-between text-xs">
                <span className="text-gray-500 font-mono">{m.fileSizeMB} MB</span>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleDelete(m.id, m.isDemo)}
                    className="text-gray-500 hover:text-red-400 transition-colors"
                    title="Delete Media"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  <Link href="/editor">
                    <span className="text-cine-gold-400 hover:underline font-medium flex items-center gap-1">
                      Open Studio <ArrowRight className="w-3 h-3" />
                    </span>
                  </Link>
                </div>
              </div>
            </GlassPanel>
          ))}
        </div>
      </div>
    </div>
  );
}
