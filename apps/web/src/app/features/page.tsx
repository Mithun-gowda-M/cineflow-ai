"use client";

import React from "react";
import Link from "next/link";
import { 
  Film, Cpu, ShieldCheck, Terminal, Layers, Music, 
  Sparkles, ExternalLink, ArrowRight, CheckCircle2 
} from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";

export default function FeaturesPage() {
  const deepTech = [
    {
      name: "FFmpeg & FFprobe",
      role: "Deterministic Multimedia Muxing & Encoding",
      version: "6.x / 7.x",
      license: "LGPL v2.1+ / GPL",
      desc: "Executes parameterized complex filtergraphs (`xfade`, `scale`, `eq`, `amix`, `loudnorm`). Zero unescaped shell execution. Cross-platform H.264/AAC output conforming to broadcast specs.",
    },
    {
      name: "OpenCV (Computer Vision)",
      role: "Laplacian Blur, Exposure & Histogram Scoring",
      version: "4.10.x",
      license: "Apache 2.0",
      desc: "Calculates Laplacian variance to score frame sharpness (> 100.0 = sharp, < 50.0 = blurred). Extracts luminance histograms and dominant color palettes for automated grading calibration.",
    },
    {
      name: "PySceneDetect",
      role: "Automated Cut & Boundary Detection",
      version: "0.6.x",
      license: "BSD 3-Clause",
      desc: "Splits raw footage into natural scenes using `ContentDetector` and `AdaptiveDetector`. Enables intelligent clip ordering without manual razor blade trimming.",
    },
    {
      name: "Librosa (Audio Intelligence)",
      role: "Beat Grid Detection & Tempo Estimation",
      version: "0.10.x",
      license: "ISC (MIT compatible)",
      desc: "Analyzes audio spectrograms and onset strength envelopes. Video cut transitions automatically align with musical downbeats within a tight ±0.15s tolerance.",
    },
    {
      name: "Whisper.cpp / faster-whisper",
      role: "Local Speech-to-Text & Word Cues",
      version: "1.5+ / 1.0+",
      license: "MIT",
      desc: "Extracts word-level timestamps from spoken dialogue on standard CPU architectures. Powers animated typography tracks and speech-aware audio ducking.",
    },
    {
      name: "Ollama (Llama 3.2)",
      role: "Open-Weights Natural Language AI Director",
      version: "Latest",
      license: "MIT",
      desc: "Translates high-level storytelling instructions into structured, validated JSON timeline plans. Guaranteed 100% offline functionality through the deterministic heuristic fallback.",
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      {/* Page Header */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <Badge variant="gold">System Architecture</Badge>
        <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
          Open-Source Technology Architecture
        </h1>
        <p className="text-gray-300 text-sm sm:text-base leading-relaxed">
          Engineered for international hackathons and permanent institutional deployment at BMSIT. 100% free from proprietary cloud API billing meters.
        </p>
      </div>

      {/* Deep Tech Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {deepTech.map((tech, idx) => (
          <GlassPanel key={idx} variant="surface" className="p-6 space-y-3 hover:border-cine-gold-500/50 transition-all">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  {tech.name}
                </h3>
                <span className="text-xs text-cine-gold-400 font-medium">{tech.role}</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-cine-black border border-cine-border font-mono text-[11px] text-gray-300">
                {tech.license}
              </span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed pt-1">
              {tech.desc}
            </p>
          </GlassPanel>
        ))}
      </div>

      {/* Hardware Adaptive Matrix Table */}
      <GlassPanel variant="active" className="p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-cine-border">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cine-gold-400" /> Hardware-Adaptive Processing Profiles
          </h2>
          <span className="text-xs text-emerald-400 font-semibold">Auto-Configured</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-cine-border text-gray-400">
                <th className="pb-3 font-semibold">Hardware Profile</th>
                <th className="pb-3 font-semibold">Target Hardware</th>
                <th className="pb-3 font-semibold">Video Encoder</th>
                <th className="pb-3 font-semibold">In-Browser Scrub Proxy</th>
                <th className="pb-3 font-semibold">Whisper Model</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cine-border/40 text-gray-300">
              <tr>
                <td className="py-3 font-bold text-cine-cyan-400">Low Profile</td>
                <td className="py-3">4 Cores, 8GB RAM (Student Laptop)</td>
                <td className="py-3 font-mono">libx264 -preset veryfast</td>
                <td className="py-3 font-mono">540p 24fps</td>
                <td className="py-3 font-mono">tiny.en (INT8)</td>
              </tr>
              <tr>
                <td className="py-3 font-bold text-cine-gold-400">Medium Profile</td>
                <td className="py-3">6-8 Cores, 16GB RAM</td>
                <td className="py-3 font-mono">libx264 medium / QSV</td>
                <td className="py-3 font-mono">720p 30fps</td>
                <td className="py-3 font-mono">base (INT8)</td>
              </tr>
              <tr>
                <td className="py-3 font-bold text-purple-400">High Profile</td>
                <td className="py-3">8+ Cores, Dedicated GPU (Workstation)</td>
                <td className="py-3 font-mono">h264_nvenc / AMF</td>
                <td className="py-3 font-mono">1080p 30fps</td>
                <td className="py-3 font-mono">small / medium</td>
              </tr>
            </tbody>
          </table>
        </div>
      </GlassPanel>

      {/* Bottom CTA */}
      <div className="p-8 rounded-2xl bg-cine-surface border border-cine-border text-center space-y-4">
        <h2 className="text-2xl font-bold text-white">Experience CINEFLOW AI in Action</h2>
        <p className="text-gray-400 text-xs sm:text-sm max-w-xl mx-auto">
          No credit card, no API keys, and no subscriptions. Start directing your footage immediately.
        </p>
        <Link href="/editor" className="inline-block">
          <GoldButton size="lg" icon={<Sparkles className="w-5 h-5" />}>
            Launch Multi-Track Studio
          </GoldButton>
        </Link>
      </div>
    </div>
  );
}
