"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Sparkles, ArrowRight, Play, Film, CheckCircle2, Cpu } from "lucide-react";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";
import { GlassPanel } from "@/components/ui/GlassPanel";

export const HeroSection: React.FC = () => {
  const [activePrompt, setActivePrompt] = useState(
    "Create a 90-second high-energy campus fest recap with beat-synced cuts, golden-hour grading, and animated subtitles."
  );

  const samplePrompts = [
    "Create a 90-second campus fest recap with beat-synced cuts and golden-hour grading.",
    "Make an emotional two-minute Deepavali documentary with slow dramatic intro.",
    "Produce a fast-paced vertical 9:16 Instagram Reel from Goa travel clips.",
  ];

  return (
    <section className="relative overflow-hidden pt-12 pb-20 md:pt-20 md:pb-28">
      {/* Background Cinematic Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-cine-gold-500/10 blur-[140px] pointer-events-none rounded-full" />
      <div className="absolute top-1/3 left-1/4 w-[400px] h-[300px] bg-cine-cyan-500/10 blur-[120px] pointer-events-none rounded-full" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
        {/* Top Badges */}
        <div className="inline-flex items-center gap-2 p-1.5 px-3 rounded-full bg-cine-card border border-cine-border shadow-gold-sm mb-6 animate-in fade-in duration-700">
          <Badge variant="gold">BMSIT Platform</Badge>
          <span className="text-xs text-gray-300 font-medium flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-cine-gold-400" /> Free & Open Source AI Video Director
          </span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white max-w-5xl mx-auto leading-[1.1]">
          Your Footage Deserves a <span className="bg-gold-gradient bg-clip-text text-transparent">Director.</span>
        </h1>

        {/* Subtitle */}
        <p className="mt-6 text-lg sm:text-xl text-gray-300 max-w-3xl mx-auto font-normal leading-relaxed">
          Transform 20–30+ raw videos and photos into professionally paced, beat-synchronized cinematic stories. Built entirely on free, open-source technology — zero recurring subscriptions.
        </p>

        {/* CTAs */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/editor">
            <GoldButton size="lg" icon={<Sparkles className="w-5 h-5" />} className="w-full sm:w-auto text-base px-8 py-3.5 shadow-gold-lg">
              Launch CINEFLOW Studio
            </GoldButton>
          </Link>
          <Link href="/upload">
            <GoldButton variant="secondary" size="lg" icon={<Film className="w-5 h-5" />} className="w-full sm:w-auto text-base px-6">
              Batch Ingest Footage (20+ Clips)
            </GoldButton>
          </Link>
        </div>

        {/* Live Director Prompt Teaser */}
        <div className="mt-12 max-w-3xl mx-auto text-left">
          <GlassPanel variant="active" className="p-4 sm:p-5">
            <div className="flex items-center justify-between mb-3 text-xs text-gray-400">
              <span className="flex items-center gap-1.5 font-semibold text-cine-gold-400">
                <Sparkles className="w-3.5 h-3.5" /> AI Director Command Preview
              </span>
              <span className="text-[11px] bg-white/5 px-2 py-0.5 rounded border border-white/10">Natural Language Planner</span>
            </div>
            <div className="bg-cine-black/70 rounded-lg p-3 border border-cine-border/70 text-sm font-mono text-gray-200">
              <span className="text-cine-gold-400">&gt; </span>
              {activePrompt}
            </div>

            <div className="mt-3 flex flex-wrap gap-2 items-center text-xs">
              <span className="text-gray-400 text-[11px]">Quick Styles:</span>
              {samplePrompts.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => setActivePrompt(p)}
                  className="px-2.5 py-1 rounded bg-cine-surface border border-cine-border text-gray-300 hover:text-cine-gold-400 hover:border-cine-gold-500/50 text-[11px] transition-colors"
                >
                  {idx === 0 ? "Campus Fest" : idx === 1 ? "Deepavali Film" : "Goa Reel (9:16)"}
                </button>
              ))}
            </div>
          </GlassPanel>
        </div>

        {/* Feature Signals */}
        <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-4xl mx-auto text-left">
          <div className="flex items-center gap-2.5 text-xs text-gray-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>₹0 Recurring Cost (100% Free)</span>
          </div>
          <div className="flex items-center gap-2.5 text-xs text-gray-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Real Multi-Track Timeline</span>
          </div>
          <div className="flex items-center gap-2.5 text-xs text-gray-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Audio Beat-Snapped Cuts</span>
          </div>
          <div className="flex items-center gap-2.5 text-xs text-gray-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>CPU Laptop & GPU Adaptive</span>
          </div>
        </div>
      </div>
    </section>
  );
};
