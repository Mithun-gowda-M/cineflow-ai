"use client";

import React, { useState, useEffect } from "react";
import {
  Film,
  Plus,
  Search,
  Scan,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import { TimelineClip } from "@/types";
import { listMediaAssets, resolveBackendUrl } from "@/lib/api";

interface MediaLibraryDrawerProps {
  onAddClip: (clip: Partial<TimelineClip>) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

interface LibraryEntry {
  id: string;
  sourceId?: string;
  mediaKind: "video" | "image" | "audio";
  title: string;
  type: "footage" | "scenes" | "broll" | "audio";
  duration: number;
  trimStart?: number;
  trimEnd?: number;
  qualityScore: number;
  thumbnail: string;
  sourceUrl: string;
  proxyUrl?: string;
  tags: string[];
  isReal?: boolean;
}

const DEMO_LIBRARY: LibraryEntry[] = [
  {
    id: "media_diya_01",
    mediaKind: "image",
    title: "Diya Lighting Hook (Demo)",
    type: "footage",
    duration: 4.5,
    qualityScore: 94,
    thumbnail: "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=400&q=80",
    sourceUrl: "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1200&q=80",
    tags: ["Diya", "Macro", "Warm"],
  },
  {
    id: "media_fireworks_02",
    mediaKind: "image",
    title: "Fireworks Climax Burst (Demo)",
    type: "footage",
    duration: 3.8,
    qualityScore: 91,
    thumbnail: "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?auto=format&fit=crop&w=400&q=80",
    sourceUrl: "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?auto=format&fit=crop&w=1200&q=80",
    tags: ["Fireworks", "Night", "Action"],
  },
  {
    id: "media_rangoli_broll",
    mediaKind: "image",
    title: "Geometric Rangoli (Demo)",
    type: "broll",
    duration: 3.0,
    qualityScore: 95,
    thumbnail: "https://images.unsplash.com/photo-1605647540924-852290f6b0d5?auto=format&fit=crop&w=400&q=80",
    sourceUrl: "https://images.unsplash.com/photo-1605647540924-852290f6b0d5?auto=format&fit=crop&w=1200&q=80",
    tags: ["Photo", "Detail", "Art"],
  },
];

export const MediaLibraryDrawer: React.FC<MediaLibraryDrawerProps> = ({
  onAddClip,
  isCollapsed,
  onToggleCollapse,
}) => {
  const [activeTab, setActiveTab] = useState<"footage" | "scenes" | "broll" | "audio">("footage");
  const [searchQuery, setSearchQuery] = useState("");
  const [realAssets, setRealAssets] = useState<LibraryEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const loadAssets = async () => {
    setLoading(true);
    try {
      const assets = await listMediaAssets();
      const mapped: LibraryEntry[] = [];

      for (const a of assets) {
        const score = a.analysis ? Math.round(a.analysis.quality.overall_score) : 85;
        const mainThumb =
          resolveBackendUrl(a.thumbnail_url) ||
          "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=400&q=80";
        const sourceUrl = resolveBackendUrl(a.source_url);
        const proxyUrl = resolveBackendUrl(a.proxy_url);

        mapped.push({
          id: a.id,
          sourceId: a.id,
          mediaKind: a.media_kind,
          title: a.original_filename,
          type: a.media_kind === "audio" ? "audio" : a.media_kind === "image" ? "broll" : "footage",
          duration: a.media_kind === "image" ? 4.0 : Math.max(0.5, Number(a.metadata.duration_seconds.toFixed(1))),
          trimStart: 0.0,
          trimEnd: a.media_kind === "image" ? 4.0 : Math.max(0.5, Number(a.metadata.duration_seconds.toFixed(1))),
          qualityScore: score,
          thumbnail: mainThumb,
          sourceUrl,
          proxyUrl,
          tags: a.tags,
          isReal: true,
        });

        // Flatten detected PySceneDetect sub-scenes into the Scenes tab
        if (a.scenes && a.scenes.length > 0) {
          for (const sc of a.scenes) {
            mapped.push({
              id: sc.scene_id,
              sourceId: a.id,
              mediaKind: "video",
              title: `${a.original_filename} · Scene ${sc.scene_index}`,
              type: "scenes",
              duration: Number(sc.duration_seconds.toFixed(1)),
              trimStart: sc.start_seconds,
              trimEnd: sc.end_seconds,
              qualityScore: Math.round(sc.quality_score),
              thumbnail: resolveBackendUrl(sc.thumbnail_url) || mainThumb,
              sourceUrl,
              proxyUrl,
              tags: sc.tags,
              isReal: true,
            });
          }
        }
      }
      setRealAssets(mapped);
    } catch {
      // Backend offline — demo assets remain available
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssets();
  }, []);

  const combinedLibrary = [...realAssets, ...DEMO_LIBRARY];

  const filtered = combinedLibrary.filter((item) => {
    const matchesTab = item.type === activeTab;
    const matchesSearch =
      !searchQuery.trim() ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesTab && matchesSearch;
  });

  if (isCollapsed) {
    return (
      <div className="w-10 bg-cine-surface border-r border-cine-border flex flex-col items-center py-3 select-none">
        <button
          onClick={onToggleCollapse}
          className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
          title="Expand Media Library"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <aside className="w-64 bg-cine-surface border-r border-cine-border flex flex-col shrink-0 select-none">
      {/* Header */}
      <div className="p-3 border-b border-cine-border flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-1.5">
          <Film className="w-3.5 h-3.5 text-cine-gold-400" /> Media Library
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={loadAssets}
            className="p-1 rounded text-gray-400 hover:text-cine-gold-400 hover:bg-white/5 transition-colors"
            title="Refresh Analyzed Media"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={onToggleCollapse}
            className="p-1 rounded text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
            title="Collapse Panel"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="grid grid-cols-4 p-1.5 bg-cine-black/50 border-b border-cine-border text-[10px]">
        <button
          onClick={() => setActiveTab("footage")}
          className={`py-1 rounded font-medium transition-colors ${
            activeTab === "footage"
              ? "bg-cine-card text-cine-gold-400 border border-cine-border shadow-sm"
              : "text-gray-400 hover:text-white"
          }`}
        >
          Clips ({combinedLibrary.filter((x) => x.type === "footage").length})
        </button>
        <button
          onClick={() => setActiveTab("scenes")}
          className={`py-1 rounded font-medium transition-colors ${
            activeTab === "scenes"
              ? "bg-cine-card text-cine-cyan-400 border border-cine-border shadow-sm"
              : "text-gray-400 hover:text-white"
          }`}
        >
          Scenes ({combinedLibrary.filter((x) => x.type === "scenes").length})
        </button>
        <button
          onClick={() => setActiveTab("broll")}
          className={`py-1 rounded font-medium transition-colors ${
            activeTab === "broll"
              ? "bg-cine-card text-cine-gold-400 border border-cine-border shadow-sm"
              : "text-gray-400 hover:text-white"
          }`}
        >
          Images
        </button>
        <button
          onClick={() => setActiveTab("audio")}
          className={`py-1 rounded font-medium transition-colors ${
            activeTab === "audio"
              ? "bg-cine-card text-cine-gold-400 border border-cine-border shadow-sm"
              : "text-gray-400 hover:text-white"
          }`}
        >
          Audio
        </button>
      </div>

      {/* Search Input */}
      <div className="p-2 border-b border-cine-border">
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-gray-500" />
          <input
            type="text"
            placeholder="Search clips or tags..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-2 py-1.5 rounded-lg bg-cine-black border border-cine-border text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cine-gold-500"
          />
        </div>
      </div>

      {/* Clip Cards List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {filtered.map((item) => (
          <div
            key={item.id}
            onClick={() => {
              onAddClip({
                sourceId: item.sourceId,
                mediaKind: item.mediaKind,
                title: item.title,
                sourceUrl: item.sourceUrl,
                proxyUrl: item.proxyUrl,
                thumbnailUrl: item.thumbnail,
                duration: item.duration,
                trimStart: item.trimStart ?? 0.0,
                trimEnd: item.trimEnd ?? item.duration,
                qualityScore: item.qualityScore,
                tags: item.tags,
                trackId: item.type === "audio" ? "a2" : "v1",
              });
            }}
            className="group p-1.5 rounded-lg bg-cine-card border border-cine-border hover:border-cine-gold-500/60 hover:bg-cine-panel transition-all cursor-pointer flex gap-2"
          >
            <div className="relative w-16 h-12 rounded overflow-hidden bg-black shrink-0">
              <div
                className="w-full h-full bg-cover bg-center group-hover:scale-105 transition-transform"
                style={{ backgroundImage: `url('${item.thumbnail}')` }}
              />
              <span className="absolute bottom-0.5 right-0.5 px-1 py-0.2 rounded bg-black/80 text-[9px] font-mono text-gray-300">
                {item.duration}s
              </span>
            </div>

            <div className="flex-1 min-w-0 flex flex-col justify-between">
              <div className="flex items-center gap-1">
                <h5 className="text-xs font-semibold text-white truncate group-hover:text-cine-gold-300 flex-1">
                  {item.title}
                </h5>
                {item.isReal && (
                  <span className="text-[9px] px-1 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    CV
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between text-[10px] text-gray-400">
                <span className="text-cine-gold-400 flex items-center gap-0.5">
                  <Scan className="w-2.5 h-2.5" /> {item.qualityScore}%
                </span>
                <span className="text-gray-500 group-hover:text-cine-cyan-400 flex items-center gap-0.5">
                  <Plus className="w-3 h-3" /> Add
                </span>
              </div>
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="text-center py-8 text-xs text-gray-500">
            No items match this filter yet.
          </div>
        )}
      </div>
    </aside>
  );
};
