import React from "react";
import { 
  Scan, Sliders, Mic, Sparkles, Layers, ShieldCheck, 
  Cpu, Music2, Film, Download 
} from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { Badge } from "@/components/ui/Badge";

export const FeaturesGrid: React.FC = () => {
  const features = [
    {
      icon: <Scan className="w-6 h-6 text-cine-gold-400" />,
      title: "Intelligent Scene & Blur Detection",
      desc: "PySceneDetect and OpenCV analyze every frame. Blurry, overexposed, or duplicate shots are filtered automatically with clear 0–100 quality scoring.",
      badge: "OpenCV + PySceneDetect",
    },
    {
      icon: <Music2 className="w-6 h-6 text-cine-cyan-400" />,
      title: "Audio Beat & Rhythm Snapping",
      desc: "Librosa analyzes musical tempo, spectral energy, and downbeat timestamps. Cuts snap right on the drop for irresistible visual impact.",
      badge: "Librosa Audio AI",
    },
    {
      icon: <Sparkles className="w-6 h-6 text-purple-400" />,
      title: "AI Director Storyboarding",
      desc: "Tell the AI what film you envision in plain English or voice. Ollama (Llama 3.2) plans an intelligent narrative arc from hook to emotional climax.",
      badge: "Local Ollama LLM",
    },
    {
      icon: <Sliders className="w-6 h-6 text-cine-gold-400" />,
      title: "Cinematic Color Grading & LUTs",
      desc: "Apply professional color science: Golden Hour, Teal & Orange, Moody Monochrome, and Film Grain calibrated directly into FFmpeg filtergraphs.",
      badge: "Native FFmpeg LUTs",
    },
    {
      icon: <Layers className="w-6 h-6 text-cine-cyan-400" />,
      title: "True Multi-Track Timeline",
      desc: "Not a black box. You retain complete director control over Video V1/V2, Audio A1/A2, and Subtitle tracks with live browser scrubbing.",
      badge: "Non-Destructive Canvas",
    },
    {
      icon: <ShieldCheck className="w-6 h-6 text-emerald-400" />,
      title: "100% Privacy & Zero Subscription",
      desc: "All processing runs locally or on your private campus server. Zero recurring API fees, zero cloud storage meters, zero data harvesting.",
      badge: "₹0 Recurring Cost",
    },
  ];

  return (
    <section className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <Badge variant="gold" className="mb-3">Engineering Quality</Badge>
        <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
          Built for International Competition
        </h2>
        <p className="mt-4 text-gray-300 text-base sm:text-lg">
          Every capability is backed by real, deterministic media engineering pipelines. No mock buttons, no fake AI loaders.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((feat, i) => (
          <GlassPanel
            key={i}
            variant="surface"
            className="p-6 hover:border-cine-gold-500/50 hover:bg-cine-card transition-all group"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 rounded-xl bg-cine-black border border-cine-border group-hover:scale-110 transition-transform">
                {feat.icon}
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-white/5 text-gray-400 border border-white/10">
                {feat.badge}
              </span>
            </div>
            <h3 className="text-lg font-bold text-white group-hover:text-cine-gold-300 transition-colors">
              {feat.title}
            </h3>
            <p className="mt-2 text-sm text-gray-400 leading-relaxed">
              {feat.desc}
            </p>
          </GlassPanel>
        ))}
      </div>
    </section>
  );
};

