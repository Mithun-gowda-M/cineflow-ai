"use client";

import React, { useState } from "react";
import { Download, Sparkles, CheckCircle2, Film, AlertCircle, RefreshCw, Layers } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";
import { AspectRatio, ColorGradePreset } from "@/types";

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectTitle: string;
  aspectRatio: AspectRatio;
  colorGrade: ColorGradePreset;
  durationSeconds: number;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  projectTitle,
  aspectRatio,
  colorGrade,
  durationSeconds,
}) => {
  const [resolution, setResolution] = useState<"720p" | "1080p" | "4k">("1080p");
  const [encoderProfile, setEncoderProfile] = useState<"auto" | "nvenc" | "cpu">("auto");
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<string>("");
  const [isComplete, setIsComplete] = useState<boolean>(false);

  const startExport = () => {
    setIsExporting(true);
    setProgress(5);
    setCurrentStep("1/4: Analyzing Timeline & Probing Media...");

    setTimeout(() => {
      setProgress(30);
      setCurrentStep("2/4: Assembling FFmpeg Complex Filtergraph & LUTs...");
    }, 1000);

    setTimeout(() => {
      setProgress(68);
      setCurrentStep("3/4: Encoding H.264 Video & Librosa Audio Mix...");
    }, 2200);

    setTimeout(() => {
      setProgress(95);
      setCurrentStep("4/4: Final Muxing & MP4 Faststart Packaging...");
    }, 3400);

    setTimeout(() => {
      setProgress(100);
      setCurrentStep("Export Complete! Broadcast MP4 Ready.");
      setIsComplete(true);
      setIsExporting(false);
    }, 4200);
  };

  const handleDownload = () => {
    // Generate a downloadable dummy MP4 blob so the download button actually downloads a file
    const fakeMp4Content = "CINEFLOW_AI_RENDERED_MP4_EXPORT_HEADER_TEST_PAYLOAD";
    const blob = new Blob([fakeMp4Content], { type: "video/mp4" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${projectTitle.toLowerCase().replace(/\s+/g, "_")}_${resolution}.mp4`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleReset = () => {
    setIsComplete(false);
    setProgress(0);
    setCurrentStep("");
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={isExporting ? () => {} : handleReset}
      title="Export Cinematic Production"
      subtitle="Render your timeline into a high-definition MP4 with embedded color science and beat synchronization."
      maxWidth="max-w-lg"
    >
      {!isComplete && !isExporting ? (
        <div className="space-y-4">
          {/* Summary Box */}
          <div className="p-3 rounded-lg bg-cine-black border border-cine-border text-xs space-y-1.5">
            <div className="flex justify-between text-gray-300">
              <span>Project Title:</span>
              <strong className="text-white">{projectTitle}</strong>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>Aspect Ratio:</span>
              <span className="font-mono text-cine-gold-400">{aspectRatio}</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>Active LUT:</span>
              <span className="text-cine-gold-400">{colorGrade.replace("_", " ").toUpperCase()}</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>Estimated Duration:</span>
              <span>{Math.round(durationSeconds)} seconds</span>
            </div>
          </div>

          {/* Resolution Options */}
          <div>
            <label className="text-xs font-semibold text-gray-300 block mb-1.5">
              Export Resolution
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: "720p", label: "720p HD", desc: "Fast CPU export" },
                { id: "1080p", label: "1080p FHD", desc: "Recommended" },
                { id: "4k", label: "4K UHD", desc: "Master quality" },
              ].map((res) => (
                <button
                  key={res.id}
                  type="button"
                  onClick={() => setResolution(res.id as any)}
                  className={`p-2.5 rounded-lg border text-left transition-all ${
                    resolution === res.id
                      ? "bg-cine-gold-500/20 border-cine-gold-500 text-cine-gold-400 shadow-gold-sm"
                      : "bg-cine-surface border-cine-border text-gray-300 hover:border-cine-borderBright"
                  }`}
                >
                  <div className="text-xs font-bold">{res.label}</div>
                  <div className="text-[10px] text-gray-500">{res.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Encoder Selection */}
          <div>
            <label className="text-xs font-semibold text-gray-300 block mb-1.5">
              Hardware Engine
            </label>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => setEncoderProfile("auto")}
                className={`p-2 rounded-lg border text-left ${
                  encoderProfile === "auto"
                    ? "bg-cine-gold-500/15 border-cine-gold-500 text-cine-gold-400"
                    : "bg-cine-surface border-cine-border text-gray-300"
                }`}
              >
                Auto-Detect (NVENC / CPU)
              </button>
              <button
                type="button"
                onClick={() => setEncoderProfile("cpu")}
                className={`p-2 rounded-lg border text-left ${
                  encoderProfile === "cpu"
                    ? "bg-cine-gold-500/15 border-cine-gold-500 text-cine-gold-400"
                    : "bg-cine-surface border-cine-border text-gray-300"
                }`}
              >
                CPU libx264 (Universal)
              </button>
            </div>
          </div>

          {/* Actions */}
          <div className="pt-4 flex justify-end gap-3 border-t border-cine-border">
            <GoldButton variant="ghost" size="md" onClick={onClose}>
              Cancel
            </GoldButton>
            <GoldButton
              size="md"
              icon={<Sparkles className="w-4 h-4" />}
              onClick={startExport}
            >
              Start Render Job
            </GoldButton>
          </div>
        </div>
      ) : isExporting ? (
        /* Progress View */
        <div className="py-6 text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-cine-black border border-cine-gold-500/50 mx-auto flex items-center justify-center shadow-gold-sm animate-pulse">
            <RefreshCw className="w-8 h-8 text-cine-gold-400 animate-spin" />
          </div>

          <div>
            <h4 className="text-base font-bold text-white mb-1">Rendering Video...</h4>
            <p className="text-xs font-mono text-cine-gold-400">{currentStep}</p>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-cine-black rounded-full h-3 overflow-hidden border border-cine-border">
            <div
              className="bg-gold-gradient h-full rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>

          <span className="text-xs font-mono text-gray-400">{progress}% complete</span>
        </div>
      ) : (
        /* Completed View */
        <div className="py-6 text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-emerald-500/20 border border-emerald-500 mx-auto flex items-center justify-center shadow-lg">
            <CheckCircle2 className="w-8 h-8 text-emerald-400" />
          </div>

          <div>
            <h4 className="text-lg font-bold text-white">Rendering Completed!</h4>
            <p className="text-xs text-gray-400 mt-1">
              Your video has been rendered and conformed to {resolution} {aspectRatio}.
            </p>
          </div>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
            <GoldButton
              size="lg"
              icon={<Download className="w-5 h-5" />}
              onClick={handleDownload}
              className="w-full sm:w-auto px-8"
            >
              Download MP4
            </GoldButton>
            <GoldButton
              variant="secondary"
              size="md"
              onClick={handleReset}
              className="w-full sm:w-auto"
            >
              Close & Keep Editing
            </GoldButton>
          </div>
        </div>
      )}
    </Modal>
  );
};
