"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  Play, Pause, Sliders, Scissors, Music, Wand2, 
  Layers, CheckCircle2, Sparkles, Eye, ArrowRight 
} from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";

export const InteractiveWorkflowDemo: React.FC = () => {
  const [activeStep, setActiveStep] = useState<number>(3); // Default to final step
  const [selectedColorGrade, setSelectedColorGrade] = useState<string>("golden_hour");
  const [isPlaying, setIsPlaying] = useState<boolean>(true);

  const steps = [
    {
      id: 1,
      title: "1. Media Ingestion",
      desc: "Batch analyze 20–30+ clips with FFprobe & OpenCV",
      icon: <Layers className="w-4 h-4" />,
    },
    {
      id: 2,
      title: "2. Scene Detection",
      desc: "PySceneDetect cuts & blur score filtering",
      icon: <Scissors className="w-4 h-4" />,
    },
    {
      id: 3,
      title: "3. Beat Synchronization",
      desc: "Librosa downbeat detection & rhythm snapping",
      icon: <Music className="w-4 h-4" />,
    },
    {
      id: 4,
      title: "4. Multi-Track Cinema",
      desc: "Color LUTs, typography, and MP4 rendering",
      icon: <Wand2 className="w-4 h-4" />,
    },
  ];

  // Visual filter simulation based on grade
  const colorGradeFilters: Record<string, string> = {
    natural: "contrast(100%) saturate(100%) brightness(100%)",
    golden_hour: "sepia(25%) saturate(140%) contrast(115%) brightness(105%) hue-rotate(-10deg)",
    cinematic_teal_orange: "contrast(130%) saturate(125%) hue-rotate(15deg)",
    moody_dark: "contrast(120%) saturate(80%) brightness(85%)",
  };

  return (
    <section className="py-16 md:py-24 bg-cine-surface/40 border-y border-cine-border relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <Badge variant="cyan" className="mb-3">Live Interactive Pipeline</Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            See How the AI Director Thinks & Cuts
          </h2>
          <p className="mt-3 text-gray-400 text-sm sm:text-base">
            Not a black-box video generator. CINEFLOW AI constructs a genuine multi-track editing timeline from your source clips and musical tempo.
          </p>
        </div>

        {/* Step Selector Tabs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
          {steps.map((s, idx) => {
            const isActive = activeStep === idx + 1;
            return (
              <button
                key={s.id}
                onClick={() => setActiveStep(idx + 1)}
                className={`p-4 rounded-xl text-left transition-all border ${
                  isActive
                    ? "bg-cine-card border-cine-gold-500 shadow-gold-sm"
                    : "bg-cine-black/60 border-cine-border hover:border-cine-borderBright hover:bg-cine-card/60"
                }`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <span className={`p-1.5 rounded-lg ${isActive ? "bg-cine-gold-500 text-cine-black" : "bg-white/5 text-gray-400"}`}>
                    {s.icon}
                  </span>
                  <span className={`text-sm font-semibold ${isActive ? "text-cine-gold-400" : "text-gray-200"}`}>
                    {s.title}
                  </span>
                </div>
                <p className="text-xs text-gray-400 line-clamp-1">{s.desc}</p>
              </button>
            );
          })}
        </div>

        {/* Interactive Workspace Simulator Window */}
        <GlassPanel variant="active" className="p-4 sm:p-6 rounded-2xl overflow-hidden border-cine-gold-500/30">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: Video Preview Canvas */}
            <div className="lg:col-span-7 flex flex-col justify-between">
              <div className="relative aspect-video rounded-xl overflow-hidden bg-black border border-cine-border shadow-2xl group">
                {/* Mock Video Canvas with live CSS color grade */}
                <div
                  className="w-full h-full bg-cover bg-center transition-all duration-500"
                  style={{
                    backgroundImage: "url('https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=1200&q=80')",
                    filter: colorGradeFilters[selectedColorGrade],
                  }}
                >
                  {/* Overlay Vignette & Cinema Bars */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 pointer-events-none" />

                  {/* Subtitle Cue Overlay */}
                  <div className="absolute bottom-10 inset-x-4 text-center">
                    <span className="inline-block px-4 py-1.5 rounded bg-black/75 backdrop-blur-md text-cine-gold-300 font-medium text-sm sm:text-base tracking-wide border border-cine-gold-500/20 shadow-lg">
                      &ldquo;When tradition ignites the festival night&rdquo;
                    </span>
                  </div>

                  {/* Timecode & Resolution Badge */}
                  <div className="absolute top-3 left-3 flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-black/80 text-[11px] font-mono text-cine-cyan-400 border border-white/10">
                      00:01:14:18
                    </span>
                    <span className="px-2 py-0.5 rounded bg-black/80 text-[10px] text-gray-300 border border-white/10">
                      1080p 60fps • 16:9
                    </span>
                  </div>

                  {/* Audio Beat Pulse indicator */}
                  <div className="absolute top-3 right-3 flex items-center gap-1.5 px-2.5 py-1 rounded bg-black/80 border border-cine-gold-500/30 text-[11px] text-cine-gold-400">
                    <span className="w-2 h-2 rounded-full bg-cine-gold-400 animate-ping" />
                    <span>Beat Drop Sync (124 BPM)</span>
                  </div>

                  {/* Center Play Button Overlay */}
                  <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="absolute inset-0 m-auto w-14 h-14 rounded-full bg-cine-black/60 border border-cine-gold-500/50 flex items-center justify-center text-cine-gold-400 hover:scale-110 transition-transform backdrop-blur-md"
                  >
                    {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-0.5" />}
                  </button>
                </div>
              </div>

              {/* Color Grade Controls */}
              <div className="mt-4 p-3 rounded-xl bg-cine-surface border border-cine-border flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs text-gray-400 font-medium flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-cine-gold-400" /> Live Cinematic LUT:
                </span>
                <div className="flex gap-1.5 flex-wrap">
                  {[
                    { id: "natural", label: "Natural Rec.709" },
                    { id: "golden_hour", label: "Golden Hour" },
                    { id: "cinematic_teal_orange", label: "Teal & Orange" },
                    { id: "moody_dark", label: "Moody Dark" },
                  ].map((lut) => (
                    <button
                      key={lut.id}
                      onClick={() => setSelectedColorGrade(lut.id)}
                      className={`px-2.5 py-1 rounded text-xs transition-colors ${
                        selectedColorGrade === lut.id
                          ? "bg-cine-gold-500 text-cine-black font-semibold shadow-gold-sm"
                          : "bg-cine-card text-gray-300 hover:text-white border border-cine-border"
                      }`}
                    >
                      {lut.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Right: Multi-Track Timeline & Intelligence Feed */}
            <div className="lg:col-span-5 flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-cine-border">
                  <span className="text-xs font-semibold uppercase tracking-wider text-gray-300">
                    Active Multi-Track Timeline
                  </span>
                  <Badge variant="emerald">Auto-Synced</Badge>
                </div>

                {/* Track V1 */}
                <div className="p-2.5 rounded-lg bg-cine-surface border border-cine-border">
                  <div className="flex items-center justify-between text-[11px] text-gray-400 mb-1.5">
                    <span className="font-semibold text-cine-gold-400">V1 • Primary Storyline</span>
                    <span>16:9 • 4 Clips</span>
                  </div>
                  <div className="grid grid-cols-4 gap-1 h-10">
                    <div className="bg-cine-gold-500/20 border border-cine-gold-500/40 rounded p-1 text-[10px] text-cine-gold-300 truncate flex items-center justify-center font-medium">
                      01. Intro (Diya Hook)
                    </div>
                    <div className="bg-cine-gold-500/30 border border-cine-gold-500/60 rounded p-1 text-[10px] text-cine-gold-300 truncate flex items-center justify-center font-medium">
                      02. Crowd Joy
                    </div>
                    <div className="bg-cine-gold-500/40 border border-cine-gold-500 rounded p-1 text-[10px] text-white truncate flex items-center justify-center font-bold shadow-gold-sm">
                      03. Fireworks Drop
                    </div>
                    <div className="bg-cine-gold-500/20 border border-cine-gold-500/40 rounded p-1 text-[10px] text-cine-gold-300 truncate flex items-center justify-center font-medium">
                      04. Emotional Finale
                    </div>
                  </div>
                </div>

                {/* Track A1 - Music with Beat Markers */}
                <div className="p-2.5 rounded-lg bg-cine-surface border border-cine-border">
                  <div className="flex items-center justify-between text-[11px] text-gray-400 mb-1.5">
                    <span className="font-semibold text-cine-cyan-400">A1 • Soundtrack (Librosa Beat Grid)</span>
                    <span>124 BPM • Auto-Ducked</span>
                  </div>
                  <div className="h-9 bg-cine-black/60 rounded border border-cine-border relative flex items-center justify-around px-2 overflow-hidden">
                    {/* Simulated Waveform Bars */}
                    {[40, 65, 30, 85, 95, 60, 45, 90, 100, 75, 40, 80, 95, 35, 60, 90].map((h, i) => (
                      <div
                        key={i}
                        className={`w-1 rounded-full transition-all ${
                          i === 8 ? "bg-cine-gold-400 scale-y-125 timeline-beat-marker" : "bg-cine-cyan-500/60"
                        }`}
                        style={{ height: `${h}%` }}
                      />
                    ))}
                  </div>
                </div>

                {/* Track T1 - Subtitles */}
                <div className="p-2.5 rounded-lg bg-cine-surface border border-cine-border">
                  <div className="flex items-center justify-between text-[11px] text-gray-400 mb-1.5">
                    <span className="font-semibold text-purple-400">T1 • Whisper Animated Subtitles</span>
                    <span>Word-Level Cues</span>
                  </div>
                  <div className="h-7 bg-cine-black/40 rounded border border-cine-border flex items-center px-3 text-[11px] text-purple-300 font-mono truncate">
                    [00:01:12] &ldquo;When tradition ignites the festival night&rdquo;
                  </div>
                </div>
              </div>

              {/* Bottom Quick Action */}
              <div className="pt-2">
                <Link href="/editor" className="w-full block">
                  <GoldButton size="md" className="w-full gap-2" icon={<ArrowRight className="w-4 h-4" />}>
                    Open in Full Multi-Track Editor Studio
                  </GoldButton>
                </Link>
              </div>
            </div>
          </div>
        </GlassPanel>
      </div>
    </section>
  );
};

