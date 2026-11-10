import React from "react";
import Link from "next/link";
import { Film, Github, Sparkles, Heart } from "lucide-react";
import { HeroSection } from "@/components/landing/HeroSection";
import { InteractiveWorkflowDemo } from "@/components/landing/InteractiveWorkflowDemo";
import { FeaturesGrid } from "@/components/landing/FeaturesGrid";
import { OpenSourceShowcase } from "@/components/landing/OpenSourceShowcase";
import { GoldButton } from "@/components/ui/GoldButton";

export default function HomePage() {
  return (
    <div className="relative">
      <HeroSection />
      <InteractiveWorkflowDemo />
      <FeaturesGrid />
      <OpenSourceShowcase />

      {/* Footer */}
      <footer className="bg-cine-black border-t border-cine-border py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gold-gradient p-[1px] flex items-center justify-center">
              <div className="w-full h-full bg-cine-black rounded-[7px] flex items-center justify-center">
                <Film className="w-4 h-4 text-cine-gold-400" />
              </div>
            </div>
            <div>
              <span className="font-bold text-white tracking-wider">CINEFLOW AI</span>
              <p className="text-xs text-gray-500">Your AI. Your Story. Your Cinema.</p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs text-gray-400">
            <Link href="/features" className="hover:text-cine-gold-400 transition-colors">
              Technology Stack
            </Link>
            <Link href="/dashboard" className="hover:text-cine-gold-400 transition-colors">
              Student Dashboard
            </Link>
            <Link href="/upload" className="hover:text-cine-gold-400 transition-colors">
              Media Hub
            </Link>
            <Link href="/admin" className="hover:text-cine-gold-400 transition-colors">
              Campus Admin
            </Link>
          </div>

          <div className="text-xs text-gray-500 text-center md:text-right">
            <p>Engineered for BMSIT & International Competitions</p>
            <p className="text-[11px] text-gray-600 mt-0.5">Distributed under the MIT License • 100% Free</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

