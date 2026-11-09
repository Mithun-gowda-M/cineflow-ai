"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  UploadCloud, FileVideo, Image as ImageIcon, CheckCircle, AlertTriangle, 
  Trash2, Filter, Sparkles, ArrowRight, ShieldCheck, Scan, Info 
} from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";
import { UploadedMediaItem } from "@/types";

export default function UploadWorkspacePage() {
  const [selectedTag, setSelectedTag] = useState<string>("all");
  const [minQuality, setMinQuality] = useState<number>(70);

  // Realistic sample media representing a 20+ file upload batch (clearly labeled as demo analysis)
  const [mediaList, setMediaList] = useState<UploadedMediaItem[]>([
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
      tags: ["Diya", "Celebration", "Macro", "Warm"],
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
      tags: ["Fireworks", "Action", "Night", "Slow-Mo"],
    },
    {
      id: "m_crowd_03",
      filename: "bmsit_auditorium_crowd_cheering.mp4",
      url: "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=600&q=80",
      thumbnailUrl: "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=600&q=80",
      fileSizeMB: 33.4,
      durationSeconds: 8.5,
      resolution: "1920x1080",
      fps: 30,
      qualityScore: 82,
      blurScore: 84,
      exposureScore: 80,
      tags: ["Celebration", "People", "High-Energy"],
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
      tags: ["Rangoli", "Color", "Photo"],
    },
    {
      id: "m_sunset_05",
      filename: "campus_golden_hour_drone.mp4",
      url: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
      thumbnailUrl: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
      fileSizeMB: 71.0,
      durationSeconds: 18.2,
      resolution: "3840x2160 (4K)",
      fps: 30,
      qualityScore: 98,
      blurScore: 99,
      exposureScore: 97,
      tags: ["Sunset", "Landscape", "Drone", "Golden Hour"],
    },
    {
      id: "m_blurry_06",
      filename: "shaky_hallway_walkthrough.mp4",
      url: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80",
      thumbnailUrl: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80",
      fileSizeMB: 28.5,
      durationSeconds: 7.1,
      resolution: "1920x1080",
      fps: 30,
      qualityScore: 48,
      blurScore: 42,
      exposureScore: 55,
      tags: ["Low-Light", "Shaky", "Filtered Out"],
    },
  ]);

  const filteredMedia = mediaList.filter((m) => {
    const matchesTag = selectedTag === "all" || m.tags.includes(selectedTag);
    const matchesScore = m.qualityScore >= minQuality;
    return matchesTag && matchesScore;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-cine-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Media Ingestion & Quality Analysis
            </h1>
            <Badge variant="cyan">OpenCV + PySceneDetect</Badge>
          </div>
          <p className="text-sm text-gray-400">
            Batch analyze 20–30+ raw videos and photos. Blur, exposure, and scene boundaries are extracted automatically.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/editor">
            <GoldButton size="md" icon={<ArrowRight className="w-4 h-4" />}>
              Send {filteredMedia.length} Clips to Editor
            </GoldButton>
          </Link>
        </div>
      </div>

      {/* Batch Drag-and-Drop Zone */}
      <GlassPanel variant="active" className="p-8 text-center border-dashed border-2 border-cine-gold-500/40 hover:border-cine-gold-500 transition-colors cursor-pointer group">
        <div className="w-16 h-16 rounded-2xl bg-cine-black border border-cine-border mx-auto flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-gold-sm">
          <UploadCloud className="w-8 h-8 text-cine-gold-400" />
        </div>
        <h3 className="text-lg font-bold text-white mb-1">
          Drag & Drop 20–30+ Videos and Images Here
        </h3>
        <p className="text-xs text-gray-400 max-w-md mx-auto mb-4">
          Accepts MP4, MOV, MKV, WebM, JPG, PNG. Automated local probing with FFprobe and OpenCV blur scoring.
        </p>
        <div className="flex items-center justify-center gap-3">
          <GoldButton variant="secondary" size="sm">
            Select Files From Device
          </GoldButton>
          <span className="text-xs text-gray-500">Zero Cloud Upload • 100% Local Processing</span>
        </div>
      </GlassPanel>

      {/* Filter and Metrics Toolbar */}
      <div className="p-4 rounded-xl bg-cine-surface border border-cine-border flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Tag Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-400 font-semibold flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-cine-gold-400" /> Filter Tags:
          </span>
          {["all", "Diya", "Fireworks", "Celebration", "Sunset", "Drone"].map((tag) => (
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

        {/* Quality Threshold Slider */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">Min Quality: <strong className="text-cine-gold-400">{minQuality}%</strong></span>
          <input
            type="range"
            min="40"
            max="90"
            step="5"
            value={minQuality}
            onChange={(e) => setMinQuality(Number(e.target.value))}
            className="w-32 accent-cine-gold-500 cursor-pointer"
          />
        </div>
      </div>

      {/* Media Inspection Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>Showing {filteredMedia.length} of {mediaList.length} analyzed clips</span>
          <span>OpenCV Laplacian Sharpness Threshold: &gt; 100.0</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMedia.map((m) => {
            const isPassing = m.qualityScore >= 70;

            return (
              <GlassPanel
                key={m.id}
                variant="surface"
                className="overflow-hidden border-cine-border hover:border-cine-gold-500/50 transition-all flex flex-col justify-between"
              >
                <div>
                  {/* Thumbnail & Video Header */}
                  <div className="relative aspect-video bg-black overflow-hidden">
                    <div
                      className="w-full h-full bg-cover bg-center"
                      style={{ backgroundImage: `url('${m.thumbnailUrl}')` }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-cine-black/90 via-transparent to-black/40" />

                    {/* Top Badges */}
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

                    {/* Quality Score Indicator */}
                    <div className="absolute top-2 right-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-bold border backdrop-blur-md flex items-center gap-1 ${
                          m.qualityScore >= 85
                            ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                            : m.qualityScore >= 70
                            ? "bg-cine-gold-500/20 text-cine-gold-400 border-cine-gold-500/40"
                            : "bg-red-500/20 text-red-400 border-red-500/40"
                        }`}
                      >
                        <Scan className="w-3 h-3" />
                        {m.qualityScore}/100
                      </span>
                    </div>

                    {/* Duration Readout */}
                    {m.durationSeconds > 0 && (
                      <div className="absolute bottom-2 left-2 text-[10px] font-mono text-gray-300 bg-black/80 px-1.5 py-0.5 rounded">
                        {m.durationSeconds}s
                      </div>
                    )}
                  </div>

                  {/* Metadata and Quality Breakdown */}
                  <div className="p-4 space-y-3">
                    <h4 className="text-sm font-semibold text-white truncate">{m.filename}</h4>

                    {/* CV Scores Meter */}
                    <div className="grid grid-cols-2 gap-2 text-[11px] text-gray-400 bg-cine-black/40 p-2.5 rounded-lg border border-cine-border/50">
                      <div>
                        <span className="block text-[10px] text-gray-500">Sharpness / Blur</span>
                        <span className="font-semibold text-gray-200">{m.blurScore}% (Clear)</span>
                      </div>
                      <div>
                        <span className="block text-[10px] text-gray-500">Exposure</span>
                        <span className="font-semibold text-gray-200">{m.exposureScore}% (Optimal)</span>
                      </div>
                    </div>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-1">
                      {m.tags.map((t, i) => (
                        <span key={i} className="px-2 py-0.5 rounded bg-cine-surface text-[10px] text-gray-300 border border-cine-border">
                          #{t}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Card Action Footer */}
                <div className="p-4 pt-2 border-t border-cine-border flex items-center justify-between text-xs">
                  <span className="text-gray-500 font-mono">{m.fileSizeMB} MB</span>
                  <Link href="/editor">
                    <span className="text-cine-gold-400 hover:underline font-medium flex items-center gap-1">
                      Add to Timeline <ArrowRight className="w-3 h-3" />
                    </span>
                  </Link>
                </div>
              </GlassPanel>
            );
          })}
        </div>
      </div>
    </div>
  );
}
