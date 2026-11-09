import React from "react";
import Link from "next/link";
import { Terminal, Shield, Cpu, BookOpen, ExternalLink, ArrowRight } from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";

export const OpenSourceShowcase: React.FC = () => {
  const stack = [
    { name: "FFmpeg & FFprobe", role: "Primary Video & Audio Rendering Engine", license: "LGPL v2.1" },
    { name: "OpenCV (Computer Vision)", role: "Laplacian Blur, Exposure & Histogram Scoring", license: "Apache 2.0" },
    { name: "PySceneDetect", role: "Automated Cut & Boundary Detection", license: "BSD 3-Clause" },
    { name: "Librosa", role: "Music Beat Tracking, BPM & Downbeats", license: "ISC" },
    { name: "Ollama (Llama 3.2)", role: "Local Open-Weights AI Director Engine", license: "MIT" },
    { name: "Whisper.cpp", role: "Speech-to-Text & Subtitle Synchronization", license: "MIT" },
  ];

  return (
    <section className="py-20 bg-cine-surface/30 border-t border-cine-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Text */}
          <div className="lg:col-span-6 space-y-6">
            <div className="inline-flex items-center gap-2">
              <Badge variant="emerald">100% Open Source</Badge>
              <span className="text-xs text-gray-400">Audited Licenses</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Zero Cloud Subscriptions.<br />
              Total Institutional Freedom.
            </h2>
            <p className="text-gray-300 text-sm sm:text-base leading-relaxed">
              Proprietary SaaS video tools trap university students with expensive recurring subscription fees and cloud compute limits. CINEFLOW AI was engineered from day one on 100% free, permissive open-source primitives.
            </p>
            <p className="text-gray-400 text-xs sm:text-sm leading-relaxed">
              Designed as a permanent software asset for the BMSIT Technical Club and national/international hackathon competition, every dependency runs cleanly on personal laptops with full offline heuristic fallback.
            </p>

            <div className="pt-2 flex flex-wrap gap-3">
              <Link href="/features">
                <GoldButton variant="secondary" size="md" icon={<BookOpen className="w-4 h-4" />}>
                  Explore Technical Specs
                </GoldButton>
              </Link>
              <Link href="/editor">
                <GoldButton size="md" icon={<ArrowRight className="w-4 h-4" />}>
                  Try in Studio
                </GoldButton>
              </Link>
            </div>
          </div>

          {/* Right Architecture Stack Cards */}
          <div className="lg:col-span-6">
            <GlassPanel variant="active" className="p-6 space-y-3">
              <div className="flex items-center justify-between pb-3 border-b border-cine-border text-xs text-gray-400 font-mono">
                <span>COMPONENT ARCHITECTURE</span>
                <span>VERIFIED LICENSE</span>
              </div>

              {stack.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 rounded-lg bg-cine-black/50 border border-cine-border hover:border-cine-gold-500/30 transition-colors"
                >
                  <div>
                    <h4 className="text-sm font-bold text-white">{item.name}</h4>
                    <p className="text-xs text-gray-400">{item.role}</p>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-cine-gold-500/10 text-cine-gold-400 border border-cine-gold-500/20">
                    {item.license}
                  </span>
                </div>
              ))}
            </GlassPanel>
          </div>
        </div>
      </div>
    </section>
  );
};
