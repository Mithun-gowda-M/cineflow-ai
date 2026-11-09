"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  Plus, Film, HardDrive, Clock, Sparkles, Sliders, 
  MoreVertical, Play, ArrowUpRight, FolderGit2, Trash2, Copy 
} from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";

interface ProjectItem {
  id: string;
  title: string;
  duration: string;
  aspectRatio: string;
  clipsCount: number;
  colorGrade: string;
  updatedAt: string;
  thumbnailUrl: string;
  isDemo?: boolean;
}

export default function DashboardPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newRatio, setNewRatio] = useState("16:9");
  const [newDuration, setNewDuration] = useState("120");
  const [newStyle, setNewStyle] = useState("golden_hour");

  const [projects, setProjects] = useState<ProjectItem[]>([
    {
      id: "proj_deepavali_01",
      title: "Deepavali 2026 Festival Highlights",
      duration: "02:00",
      aspectRatio: "16:9",
      clipsCount: 22,
      colorGrade: "Golden Hour",
      updatedAt: "2 hours ago",
      thumbnailUrl: "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=800&q=80",
      isDemo: true,
    },
    {
      id: "proj_bmsit_fest_02",
      title: "BMSIT Cultural & Tech Fest Recap",
      duration: "01:30",
      aspectRatio: "16:9",
      clipsCount: 28,
      colorGrade: "Teal & Orange",
      updatedAt: "Yesterday",
      thumbnailUrl: "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=800&q=80",
      isDemo: true,
    },
    {
      id: "proj_goa_reel_03",
      title: "Goa Coastal Monsoon Story",
      duration: "00:45",
      aspectRatio: "9:16",
      clipsCount: 14,
      colorGrade: "Moody Dark",
      updatedAt: "3 days ago",
      thumbnailUrl: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
      isDemo: true,
    },
  ]);

  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    const newProject: ProjectItem = {
      id: `proj_${Date.now()}`,
      title: newTitle.trim(),
      duration: `${Math.floor(Number(newDuration) / 60)}:${String(Number(newDuration) % 60).padStart(2, "0")}`,
      aspectRatio: newRatio,
      clipsCount: 0,
      colorGrade: newStyle === "golden_hour" ? "Golden Hour" : newStyle === "cinematic_teal_orange" ? "Teal & Orange" : "Natural",
      updatedAt: "Just now",
      thumbnailUrl: "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=800&q=80",
    };

    setProjects([newProject, ...projects]);
    setIsModalOpen(false);
    setNewTitle("");
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Top Welcome Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-cine-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Student Project Studio
            </h1>
            <Badge variant="gold">BMSIT Campus Edition</Badge>
          </div>
          <p className="text-sm text-gray-400">
            Manage your AI video productions, media libraries, and export queues.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/upload">
            <GoldButton variant="secondary" size="md" icon={<Film className="w-4 h-4" />}>
              Ingest Media
            </GoldButton>
          </Link>
          <GoldButton
            size="md"
            icon={<Plus className="w-4 h-4" />}
            onClick={() => setIsModalOpen(true)}
          >
            New Project
          </GoldButton>
        </div>
      </div>

      {/* Metric Cards & Storage Gauge */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <GlassPanel variant="surface" className="p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Total Projects</span>
            <FolderGit2 className="w-4 h-4 text-cine-gold-400" />
          </div>
          <div className="text-3xl font-bold text-white">{projects.length}</div>
          <p className="text-[11px] text-gray-500">3 sample demo projects active</p>
        </GlassPanel>

        <GlassPanel variant="surface" className="p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Renders Completed</span>
            <Film className="w-4 h-4 text-cine-cyan-400" />
          </div>
          <div className="text-3xl font-bold text-white">12</div>
          <p className="text-[11px] text-emerald-400">100% successful export rate</p>
        </GlassPanel>

        <GlassPanel variant="surface" className="p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>AI Director Runs</span>
            <Sparkles className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-bold text-white">34</div>
          <p className="text-[11px] text-gray-500">Local Llama 3.2 & Heuristic Engine</p>
        </GlassPanel>

        {/* Storage Quota Gauge */}
        <GlassPanel variant="surface" className="p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Campus Local Storage</span>
            <HardDrive className="w-4 h-4 text-cine-gold-400" />
          </div>
          <div className="flex items-baseline justify-between">
            <div className="text-2xl font-bold text-white">4.8 GB</div>
            <div className="text-xs text-gray-400">/ 25.0 GB Quota</div>
          </div>
          {/* Progress Bar */}
          <div className="w-full bg-cine-black rounded-full h-2 overflow-hidden border border-cine-border">
            <div className="bg-gold-gradient h-full rounded-full transition-all" style={{ width: "19.2%" }} />
          </div>
        </GlassPanel>
      </div>

      {/* Projects Grid Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
            <Clock className="w-4 h-4 text-cine-gold-400" /> Recent Productions
          </h2>
          <span className="text-xs text-gray-400">Showing {projects.length} projects</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => (
            <GlassPanel
              key={proj.id}
              variant="surface"
              className="overflow-hidden group hover:border-cine-gold-500/50 transition-all flex flex-col justify-between"
            >
              <div>
                {/* Thumbnail Header with Badges */}
                <div className="relative aspect-video bg-black overflow-hidden">
                  <div
                    className="w-full h-full bg-cover bg-center group-hover:scale-105 transition-transform duration-500"
                    style={{ backgroundImage: `url('${proj.thumbnailUrl}')` }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-cine-black/90 via-black/20 to-transparent" />

                  {/* Top Badges */}
                  <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
                    <span className="px-2 py-0.5 rounded bg-black/80 backdrop-blur-md text-[10px] font-mono text-cine-gold-300 border border-cine-border">
                      {proj.aspectRatio}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-black/80 backdrop-blur-md text-[10px] font-mono text-cine-cyan-300 border border-cine-border">
                      {proj.duration}
                    </span>
                  </div>

                  {proj.isDemo && (
                    <div className="absolute top-2.5 right-2.5">
                      <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[9px] uppercase font-semibold">
                        Demo Project
                      </span>
                    </div>
                  )}

                  {/* Center Play Button on hover */}
                  <Link
                    href="/editor"
                    className="absolute inset-0 m-auto w-12 h-12 rounded-full bg-cine-black/75 border border-cine-gold-500/60 flex items-center justify-center text-cine-gold-400 opacity-0 group-hover:opacity-100 transition-opacity backdrop-blur-md"
                  >
                    <Play className="w-5 h-5 ml-0.5" />
                  </Link>
                </div>

                {/* Content Info */}
                <div className="p-5 space-y-3">
                  <h3 className="font-bold text-white text-base group-hover:text-cine-gold-300 transition-colors line-clamp-1">
                    {proj.title}
                  </h3>

                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span>{proj.clipsCount} clips in timeline</span>
                    <span className="text-cine-gold-400/80 font-medium">{proj.colorGrade}</span>
                  </div>
                </div>
              </div>

              {/* Bottom Actions */}
              <div className="px-5 pb-5 pt-2 border-t border-cine-border flex items-center justify-between">
                <span className="text-[11px] text-gray-500">Updated {proj.updatedAt}</span>
                <div className="flex items-center gap-2">
                  <Link href="/editor">
                    <GoldButton size="sm" icon={<ArrowUpRight className="w-3.5 h-3.5" />}>
                      Open Editor
                    </GoldButton>
                  </Link>
                </div>
              </div>
            </GlassPanel>
          ))}
        </div>
      </div>

      {/* New Project Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create New AI Video Project"
        subtitle="Configure your canvas dimensions, target duration, and director style."
      >
        <form onSubmit={handleCreateProject} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">
              Project Title
            </label>
            <input
              type="text"
              required
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="e.g. Goa Vacation Reel 2026"
              className="w-full px-3 py-2 rounded-lg bg-cine-black border border-cine-border text-white text-sm focus:outline-none focus:border-cine-gold-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">
                Aspect Ratio
              </label>
              <select
                value={newRatio}
                onChange={(e) => setNewRatio(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-cine-black border border-cine-border text-white text-sm focus:outline-none focus:border-cine-gold-500"
              >
                <option value="16:9">16:9 (Landscape YouTube)</option>
                <option value="9:16">9:16 (Shorts / Reels)</option>
                <option value="1:1">1:1 (Square)</option>
                <option value="21:9">21:9 (Anamorphic Cinema)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">
                Target Duration
              </label>
              <select
                value={newDuration}
                onChange={(e) => setNewDuration(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-cine-black border border-cine-border text-white text-sm focus:outline-none focus:border-cine-gold-500"
              >
                <option value="30">30 Seconds</option>
                <option value="60">60 Seconds</option>
                <option value="90">90 Seconds</option>
                <option value="120">2 Minutes (Default)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">
              Initial Color Grade Style
            </label>
            <select
              value={newStyle}
              onChange={(e) => setNewStyle(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-cine-black border border-cine-border text-white text-sm focus:outline-none focus:border-cine-gold-500"
            >
              <option value="golden_hour">Golden Hour (Warm, Festival, Travel)</option>
              <option value="cinematic_teal_orange">Teal & Orange (High Contrast Cinema)</option>
              <option value="moody_dark">Moody Dark (Dramatic, Documentary)</option>
              <option value="natural">Natural Rec.709 (Clean)</option>
            </select>
          </div>

          <div className="pt-4 flex justify-end gap-3 border-t border-cine-border">
            <GoldButton
              type="button"
              variant="ghost"
              size="md"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </GoldButton>
            <GoldButton type="submit" size="md" icon={<Sparkles className="w-4 h-4" />}>
              Initialize Project & Open
            </GoldButton>
          </div>
        </form>
      </Modal>
    </div>
  );
}
