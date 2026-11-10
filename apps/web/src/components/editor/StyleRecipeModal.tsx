"use client";

import React, { useEffect, useState } from "react";
import { ShieldCheck, Sparkles, Upload, Link2, CheckCircle2, RefreshCw, AlertCircle, Activity } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";
import {
  analyzeReferenceVideoUpload,
  analyzeSafeReferenceUrl,
  BackendStyleRecipe,
  listStyleRecipes,
} from "@/lib/api";

interface StyleRecipeModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeRecipeId: string | null;
  onApplyRecipe: (recipe: BackendStyleRecipe) => Promise<void> | void;
  onSelectForDirector: (recipe: BackendStyleRecipe) => void;
}

const FALLBACK_RECIPES: BackendStyleRecipe[] = [
  {
    id: "recipe_bmsit_aftermovie",
    name: "BMSIT Cultural Fest Aftermovie",
    description: "High-impact 4-act campus recap curve with teal & orange glow and climax speed ramps.",
    source_type: "builtin",
    is_builtin: true,
    cuts_per_minute: 24.0,
    avg_shot_duration_seconds: 2.5,
    cut_cadence: "moderate",
    motion_velocity_score: 68.0,
    motion_profile: "dynamic_burst",
    color_mood: "warm_golden",
    recommended_color_grade: "cinematic_teal_orange",
    recommended_aspect_ratio: "16:9",
    recommended_pacing: "dynamic_arc",
    recommended_speed_ramp: "fast_to_slow",
    recommended_transition: "crossfade",
    cinematic_effects: {
      vignette: true,
      film_grain: false,
      ken_burns_on_images: true,
      audio_ducking: true,
      loudness_normalize: true,
    },
    dominant_palette: ["#0B0D13", "#E5B869", "#38BDF8"],
    prompt_hint: "Dynamic 4-act festive aftermovie with climax speed ramp.",
    safety_audit: {
      copyright_safe: true,
      media_downloaded: false,
      private_scraping_blocked: true,
      raw_frames_retained: false,
      compliance_note: "Abstract style rules only.",
    },
    created_at: "",
  },
  {
    id: "recipe_viral_reel_9x16",
    name: "Viral 9:16 Rapid Hook Reel",
    description: "Ultra-fast vertical beat-driven pacing tuned for YouTube Shorts and Instagram Reels.",
    source_type: "builtin",
    is_builtin: true,
    cuts_per_minute: 44.0,
    avg_shot_duration_seconds: 1.35,
    cut_cadence: "rapid",
    motion_velocity_score: 84.0,
    motion_profile: "high_velocity",
    color_mood: "bright",
    recommended_color_grade: "cinematic_teal_orange",
    recommended_aspect_ratio: "9:16",
    recommended_pacing: "fast",
    recommended_speed_ramp: "slow_to_fast",
    recommended_transition: "zoom_in",
    cinematic_effects: {
      vignette: false,
      film_grain: false,
      ken_burns_on_images: true,
      audio_ducking: true,
      loudness_normalize: true,
    },
    dominant_palette: ["#38BDF8", "#E5B869", "#11141E"],
    prompt_hint: "Fast 9:16 vertical reel.",
    safety_audit: {
      copyright_safe: true,
      media_downloaded: false,
      private_scraping_blocked: true,
      raw_frames_retained: false,
      compliance_note: "Abstract style rules only.",
    },
    created_at: "",
  },
];

export const StyleRecipeModal: React.FC<StyleRecipeModalProps> = ({
  isOpen,
  onClose,
  activeRecipeId,
  onApplyRecipe,
  onSelectForDirector,
}) => {
  const [tab, setTab] = useState<"library" | "upload" | "url">("library");
  const [recipes, setRecipes] = useState<BackendStyleRecipe[]>(FALLBACK_RECIPES);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Ephemeral video analyzer state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState("");

  // Safe URL descriptor state
  const [refUrl, setRefUrl] = useState("");
  const [urlName, setUrlName] = useState("");
  const [styleNotes, setStyleNotes] = useState("");

  useEffect(() => {
    if (!isOpen) return;
    setErrorMsg("");
    listStyleRecipes()
      .then((list) => {
        if (list.length > 0) setRecipes(list);
      })
      .catch(() => {
        // Keep curated fallback recipes if backend offline
      });
  }, [isOpen]);

  const handleAnalyzeUpload = async () => {
    if (!uploadFile) return;
    setLoading(true);
    setErrorMsg("");
    try {
      const created = await analyzeReferenceVideoUpload(uploadFile, uploadName.trim() || undefined);
      setRecipes((prev) => [created, ...prev.filter((r) => r.id !== created.id)]);
      setUploadFile(null);
      setUploadName("");
      setTab("library");
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to extract style from reference clip.");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeUrl = async () => {
    if (!refUrl.trim()) return;
    setLoading(true);
    setErrorMsg("");
    try {
      const created = await analyzeSafeReferenceUrl({
        referenceUrl: refUrl.trim(),
        recipeName: urlName.trim() || undefined,
        styleNotes: styleNotes.trim(),
      });
      setRecipes((prev) => [created, ...prev.filter((r) => r.id !== created.id)]);
      setRefUrl("");
      setUrlName("");
      setStyleNotes("");
      setTab("library");
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Safe URL analysis rejected.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Trend Intelligence & Style Recipes"
      subtitle="Extract quantitative cut rhythm, motion velocity, and color mood — zero copyright retention."
      maxWidth="max-w-2xl"
    >
      <div className="space-y-4">
        {/* Strict Copyright Safety Banner */}
        <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-2 text-xs text-emerald-300">
          <ShieldCheck className="w-4 h-4 shrink-0" />
          <span>
            <strong>Copyright-Safe Architecture:</strong> Only numeric editing rules (cuts/min, velocity, LUTs) are extracted. Zero frames, audio, or scraped web media are stored.
          </span>
        </div>

        {/* Navigation Tabs */}
        <div className="flex gap-1.5 border-b border-cine-border pb-2 text-xs">
          {[
            { id: "library" as const, label: `Style Library (${recipes.length})`, icon: Sparkles },
            { id: "upload" as const, label: "Extract from Reference Video", icon: Upload },
            { id: "url" as const, label: "Safe URL Descriptor", icon: Link2 },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  setTab(item.id);
                  setErrorMsg("");
                }}
                className={`px-3 py-1.5 rounded-lg font-semibold flex items-center gap-1.5 transition-colors ${
                  tab === item.id
                    ? "bg-cine-gold-500 text-cine-black"
                    : "bg-cine-surface text-gray-300 hover:text-white border border-cine-border"
                }`}
              >
                <Icon className="w-3.5 h-3.5" /> {item.label}
              </button>
            );
          })}
        </div>

        {errorMsg && (
          <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-xs text-red-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {tab === "library" && (
          <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
            {recipes.map((recipe) => {
              const isSelected = activeRecipeId === recipe.id;
              return (
                <div
                  key={recipe.id}
                  className={`p-3 rounded-xl border transition-all space-y-2 ${
                    isSelected
                      ? "bg-cine-gold-500/10 border-cine-gold-500 shadow-gold-sm"
                      : "bg-cine-black/60 border-cine-border hover:border-cine-gold-500/40"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-bold text-white">{recipe.name}</h4>
                        <Badge variant={recipe.is_builtin ? "gold" : "cyan"} size="sm">
                          {recipe.is_builtin ? "Curated" : recipe.source_type === "uploaded_reference" ? "Clip Telemetry" : "URL Rule"}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5">{recipe.description}</p>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {recipe.dominant_palette.slice(0, 4).map((hex, i) => (
                        <span
                          key={`${hex}-${i}`}
                          className="w-3.5 h-3.5 rounded-full border border-white/20"
                          style={{ backgroundColor: hex }}
                          title={hex}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Extracted Telemetry Pills */}
                  <div className="flex flex-wrap items-center gap-2 text-[10px] font-mono text-gray-300">
                    <span className="px-2 py-0.5 rounded bg-cine-surface border border-cine-border">
                      {recipe.cuts_per_minute.toFixed(0)} cuts/min ({recipe.avg_shot_duration_seconds.toFixed(1)}s avg)
                    </span>
                    <span className="px-2 py-0.5 rounded bg-cine-surface border border-cine-border flex items-center gap-1">
                      <Activity className="w-3 h-3 text-cine-cyan-400" />
                      Velocity {recipe.motion_velocity_score.toFixed(0)}/100 ({recipe.motion_profile})
                    </span>
                    <span className="px-2 py-0.5 rounded bg-cine-surface border border-cine-border text-cine-gold-300">
                      {recipe.recommended_aspect_ratio} • {recipe.recommended_color_grade.replace(/_/g, " ")} • {recipe.recommended_speed_ramp}
                    </span>
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => {
                        onSelectForDirector(recipe);
                        onClose();
                      }}
                      className="px-2.5 py-1 rounded-lg border border-cine-border text-[11px] text-gray-300 hover:text-white hover:border-cine-gold-500/50"
                    >
                      Use with AI Director
                    </button>
                    <GoldButton
                      size="sm"
                      onClick={async () => {
                        await onApplyRecipe(recipe);
                        onClose();
                      }}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Apply Style Now
                    </GoldButton>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {tab === "upload" && (
          <div className="p-4 rounded-xl bg-cine-black/60 border border-cine-border space-y-3 text-xs">
            <p className="text-gray-300">
              Upload any user-owned MP4/MOV reference clip. CINEFLOW computes OpenCV optical motion velocity, PySceneDetect cut cadence, and dominant palette — then immediately deletes the temporary file.
            </p>
            <input
              type="text"
              value={uploadName}
              onChange={(e) => setUploadName(e.target.value)}
              placeholder="Recipe name (optional, e.g. Neon Concert Energy)"
              className="w-full px-3 py-2 rounded-lg bg-cine-surface border border-cine-border text-white placeholder-gray-500 focus:outline-none focus:border-cine-gold-500"
            />
            <input
              type="file"
              accept="video/mp4,video/quicktime,video/webm,video/x-matroska"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              className="block w-full text-gray-300 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border file:border-cine-gold-500/40 file:text-xs file:font-semibold file:bg-cine-gold-500/15 file:text-cine-gold-300 hover:file:bg-cine-gold-500/25"
            />
            <div className="flex justify-end">
              <GoldButton
                size="sm"
                onClick={handleAnalyzeUpload}
                disabled={!uploadFile || loading}
                icon={loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
              >
                {loading ? "Extracting Telemetry..." : "Extract Style Recipe"}
              </GoldButton>
            </div>
          </div>
        )}

        {tab === "url" && (
          <div className="p-4 rounded-xl bg-cine-black/60 border border-cine-border space-y-3 text-xs">
            <p className="text-gray-300">
              Provide a public HTTPS reference URL plus desired style notes. Strictly blocks internal SSRF IPs and never downloads or scrapes external copyrighted video/audio.
            </p>
            <input
              type="url"
              value={refUrl}
              onChange={(e) => setRefUrl(e.target.value)}
              placeholder="https://example.com/reels/fest-aftermovie"
              className="w-full px-3 py-2 rounded-lg bg-cine-surface border border-cine-border text-white placeholder-gray-500 focus:outline-none focus:border-cine-gold-500"
            />
            <input
              type="text"
              value={urlName}
              onChange={(e) => setUrlName(e.target.value)}
              placeholder="Recipe name (optional)"
              className="w-full px-3 py-2 rounded-lg bg-cine-surface border border-cine-border text-white placeholder-gray-500 focus:outline-none focus:border-cine-gold-500"
            />
            <textarea
              rows={2}
              value={styleNotes}
              onChange={(e) => setStyleNotes(e.target.value)}
              placeholder="Style descriptors (e.g. fast 9:16 vertical cuts, bleach bypass contrast, film grain, vignette)"
              className="w-full px-3 py-2 rounded-lg bg-cine-surface border border-cine-border text-white placeholder-gray-500 focus:outline-none focus:border-cine-gold-500 resize-none"
            />
            <div className="flex justify-end">
              <GoldButton
                size="sm"
                onClick={handleAnalyzeUrl}
                disabled={!refUrl.trim() || loading}
                icon={loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Link2 className="w-3.5 h-3.5" />}
              >
                {loading ? "Validating Rules..." : "Create Safe URL Recipe"}
              </GoldButton>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

