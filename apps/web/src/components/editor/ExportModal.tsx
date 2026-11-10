"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Download, Sparkles, CheckCircle2, AlertCircle, RefreshCw, XCircle } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { GoldButton } from "@/components/ui/GoldButton";
import { AspectRatio, CinematicEffects, ColorGradePreset, SubtitleCue, TimelineClip } from "@/types";
import {
  cancelRenderJob,
  checkBackendHealth,
  getRenderDownloadUrl,
  pollRenderStatus,
  submitRenderJob,
} from "@/lib/api";

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectTitle: string;
  projectId?: string;
  aspectRatio: AspectRatio;
  colorGrade: ColorGradePreset;
  durationSeconds: number;
  clips: TimelineClip[];
  subtitles?: SubtitleCue[];
  cinematicEffects?: CinematicEffects;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  projectTitle,
  projectId = "proj_studio_01",
  aspectRatio,
  colorGrade,
  durationSeconds,
  clips,
  subtitles,
  cinematicEffects,
}) => {
  const [resolution, setResolution] = useState<"720p" | "1080p" | "4k">("1080p");
  const [encoderProfile, setEncoderProfile] = useState<"auto" | "cpu">("auto");
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [detectedEncoder, setDetectedEncoder] = useState<string>("libx264");

  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<string>("");
  const [isComplete, setIsComplete] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [outputFileSize, setOutputFileSize] = useState<number | null>(null);

  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const realVideoClips = clips.filter(
    (c) => (c.trackId === "v1" || c.trackId === "v2") && Boolean(c.sourceId)
  );
  const canRenderRealMp4 = Boolean(backendOnline) && realVideoClips.length > 0;

  useEffect(() => {
    if (!isOpen) return;
    checkBackendHealth().then((health) => {
      if (health && health.ffmpeg_available) {
        setBackendOnline(true);
        setDetectedEncoder(health.hardware.video_encoder);
      } else {
        setBackendOnline(false);
      }
    });
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [isOpen]);

  const startExport = async () => {
    setErrorMessage("");
    setIsExporting(true);
    setProgress(2);
    setCurrentStep("Submitting timeline to FastAPI FFmpeg engine...");

    try {
      const job = await submitRenderJob({
        projectId,
        title: projectTitle,
        aspectRatio,
        colorGrade,
        clips,
        subtitles,
        cinematicEffects,
        resolution,
        encoderPreference: encoderProfile,
      });
      setActiveJobId(job.job_id);

      pollRef.current = setInterval(async () => {
        try {
          const status = await pollRenderStatus(job.job_id);
          setProgress(status.progress_percent);
          setCurrentStep(status.current_step);

          if (status.status === "completed") {
            if (pollRef.current) clearInterval(pollRef.current);
            setOutputFileSize(status.output_file_size_bytes || null);
            setIsExporting(false);
            setIsComplete(true);
          } else if (status.status === "failed" || status.status === "cancelled") {
            if (pollRef.current) clearInterval(pollRef.current);
            setIsExporting(false);
            setErrorMessage(status.error_message || `Render ${status.status}.`);
          }
        } catch (err) {
          if (pollRef.current) clearInterval(pollRef.current);
          setIsExporting(false);
          setErrorMessage(err instanceof Error ? err.message : "Lost connection to render worker.");
        }
      }, 500);
    } catch (err) {
      setIsExporting(false);
      setErrorMessage(err instanceof Error ? err.message : "Failed to start render job.");
    }
  };

  const handleCancelJob = async () => {
    if (pollRef.current) clearInterval(pollRef.current);
    if (activeJobId) {
      try {
        await cancelRenderJob(activeJobId);
      } catch {
        // ignore cancel error
      }
    }
    setIsExporting(false);
    setErrorMessage("Render cancelled by user.");
  };

  const handleReset = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    setIsComplete(false);
    setIsExporting(false);
    setProgress(0);
    setCurrentStep("");
    setErrorMessage("");
    setActiveJobId(null);
    setOutputFileSize(null);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={isExporting ? () => {} : handleReset}
      title="Export Cinematic Production"
      subtitle="Render your multi-track timeline into a verified H.264/AAC MP4 via local FFmpeg."
      maxWidth="max-w-lg"
    >
      {!isComplete && !isExporting ? (
        <div className="space-y-4">
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
              <span className="text-cine-gold-400">{colorGrade.replace(/_/g, " ").toUpperCase()}</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>Ingested Source Clips:</span>
              <span className={realVideoClips.length > 0 ? "text-emerald-400 font-semibold" : "text-amber-400"}>
                {realVideoClips.length} real / {clips.filter((c) => c.trackId === "v1" || c.trackId === "v2").length} total
              </span>
            </div>
          </div>

          {backendOnline === false && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Local FFmpeg Backend Offline</p>
                <p className="text-[11px] text-amber-200/80 mt-0.5">
                  Start the backend (`backend\.venv\Scripts\uvicorn backend.api.main:app --port 8000`) to render real MP4 exports. CINEFLOW never produces fake placeholder downloads.
                </p>
              </div>
            </div>
          )}

          {backendOnline && realVideoClips.length === 0 && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Timeline Contains Demo Placeholders Only</p>
                <p className="text-[11px] text-amber-200/80 mt-0.5">
                  Upload local video/image assets in the{" "}
                  <Link href="/upload" className="underline text-cine-gold-400">
                    Media Hub
                  </Link>{" "}
                  and add them from the left Media Library to render a real MP4.
                </p>
              </div>
            </div>
          )}

          {errorMessage && (
            <div className="p-3 rounded-lg bg-red-500/15 border border-red-500/30 text-red-300 text-xs flex items-center gap-2">
              <XCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div>
            <label className="text-xs font-semibold text-gray-300 block mb-1.5">Export Resolution</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: "720p", label: "720p HD", desc: "Fast CPU export" },
                { id: "1080p", label: "1080p FHD", desc: "Recommended" },
                { id: "4k", label: "4K UHD", desc: "Master quality" },
              ].map((res) => (
                <button
                  key={res.id}
                  type="button"
                  onClick={() => setResolution(res.id as "720p" | "1080p" | "4k")}
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

          <div>
            <label className="text-xs font-semibold text-gray-300 block mb-1.5">Hardware Engine</label>
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
                Auto ({detectedEncoder})
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

          <div className="pt-4 flex justify-end gap-3 border-t border-cine-border">
            <GoldButton variant="ghost" size="md" onClick={handleReset}>
              Cancel
            </GoldButton>
            <GoldButton
              size="md"
              icon={<Sparkles className="w-4 h-4" />}
              onClick={startExport}
              disabled={!canRenderRealMp4}
            >
              Start FFmpeg Render
            </GoldButton>
          </div>
        </div>
      ) : isExporting ? (
        <div className="py-6 text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-cine-black border border-cine-gold-500/50 mx-auto flex items-center justify-center shadow-gold-sm animate-pulse">
            <RefreshCw className="w-8 h-8 text-cine-gold-400 animate-spin" />
          </div>

          <div>
            <h4 className="text-base font-bold text-white mb-1">Rendering MP4 via FFmpeg...</h4>
            <p className="text-xs font-mono text-cine-gold-400">{currentStep}</p>
          </div>

          <div className="w-full bg-cine-black rounded-full h-3 overflow-hidden border border-cine-border">
            <div
              className="bg-gold-gradient h-full rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>{progress.toFixed(1)}% complete</span>
            <button onClick={handleCancelJob} className="text-red-400 hover:underline">
              Cancel Render
            </button>
          </div>
        </div>
      ) : (
        <div className="py-6 text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-emerald-500/20 border border-emerald-500 mx-auto flex items-center justify-center shadow-lg">
            <CheckCircle2 className="w-8 h-8 text-emerald-400" />
          </div>

          <div>
            <h4 className="text-lg font-bold text-white">Verified MP4 Export Ready</h4>
            <p className="text-xs text-gray-400 mt-1">
              Conformed to {resolution} ({aspectRatio})
              {outputFileSize ? ` • ${(outputFileSize / (1024 * 1024)).toFixed(2)} MB` : ""}.
            </p>
          </div>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
            {activeJobId && (
              <a
                href={getRenderDownloadUrl(activeJobId)}
                download={`${projectTitle.toLowerCase().replace(/\s+/g, "_")}_${resolution}.mp4`}
                className="w-full sm:w-auto"
              >
                <GoldButton size="lg" icon={<Download className="w-5 h-5" />} className="w-full px-8">
                  Download MP4
                </GoldButton>
              </a>
            )}
            <GoldButton variant="secondary" size="md" onClick={handleReset} className="w-full sm:w-auto">
              Close &amp; Keep Editing
            </GoldButton>
          </div>
        </div>
      )}
    </Modal>
  );
};
