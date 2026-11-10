"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Cpu,
  DollarSign,
  Film,
  Gauge,
  Layers,
  Loader2,
  Play,
  Presentation,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";
import {
  BackendBenchmarkReport,
  BackendShowcaseStatus,
  fetchShowcaseBenchmarks,
  fetchShowcaseStatus,
  loadShowcaseProject,
  runShowcaseBenchmarks,
} from "@/lib/api";

// Verified baseline snapshot captured from docs/benchmarks/BENCHMARK_REPORT.json (used only when backend is offline)
const VERIFIED_HOST_SNAPSHOT: BackendBenchmarkReport = {
  generated_at: "2026-11-10T15:41:22Z",
  host_os: "Windows 11 (AMD64)",
  python_version: "3.12.10",
  cpu_cores: 16,
  ram_total_gb: 15.7,
  ffmpeg_version: "ffmpeg version 9.0.2-full_build-www.gyan.dev",
  hardware_profile: {
    profile: "high",
    cpu_cores: 16,
    free_disk_gb: 339.95,
    video_encoder: "h264_qsv",
    hw_accel_available: true,
    detected_encoders: ["h264_qsv", "libx264"],
    max_concurrent_renders: 4,
  },
  stages: [
    {
      stage_id: "ingest_probe_proxy",
      stage_name: "FFprobe & 720p Proxy Generation",
      duration_seconds: 4.315,
      throughput_label: "4 HD clips in 4.32s (0.93 clips/s)",
      cpu_percent_avg: 2.5,
      memory_rss_mb: 67.4,
      notes: "3x 1920x1080 + 1x 1080x1920 -> 720p proxies (h264_qsv)",
    },
    {
      stage_id: "cv_scene_analysis",
      stage_name: "OpenCV CV Scoring & PySceneDetect",
      duration_seconds: 84.654,
      throughput_label: "0.05 clips/s (5 scenes)",
      cpu_percent_avg: 131.8,
      memory_rss_mb: 143.4,
      notes: "Mean quality score 79.9/100 across 1080p footage",
    },
    {
      stage_id: "librosa_beat_sync",
      stage_name: "Librosa Tempo & Beat Tracking",
      duration_seconds: 3.776,
      throughput_label: "4.24x realtime (60.1 BPM)",
      cpu_percent_avg: 75.2,
      memory_rss_mb: 296.0,
      notes: "15 beats detected on 16.0s track",
    },
    {
      stage_id: "render_1080p_cold",
      stage_name: "Cold 1080p Multi-Clip MP4 Render",
      duration_seconds: 19.401,
      throughput_label: "0.49x realtime (9.6s @ 1920x1080)",
      cpu_percent_avg: 0.9,
      memory_rss_mb: 296.2,
      notes: "Encoder: h264_qsv; LUT + ASS captions + xfade + loudnorm",
    },
    {
      stage_id: "render_1080p_warm_partial",
      stage_name: "Warm Partial-Cache Re-Render",
      duration_seconds: 7.633,
      throughput_label: "60.7% faster (2/3 cached)",
      cpu_percent_avg: 0.8,
      memory_rss_mb: 296.5,
      notes: "SHA-256 segment cache reuses untouched 1080p clips",
    },
    {
      stage_id: "render_vertical_9_16",
      stage_name: "Vertical 9:16 (1080x1920) Reel Export",
      duration_seconds: 2.311,
      throughput_label: "1.51x realtime (1080x1920)",
      cpu_percent_avg: 0.0,
      memory_rss_mb: 296.6,
      notes: "Teal & Orange grade + portrait crop/scale",
    },
  ],
  cold_render_seconds: 19.401,
  warm_cached_render_seconds: 7.633,
  cache_speedup_percent: 60.7,
  segment_cache_hits: 2,
  segment_cache_misses: 1,
  output_duration_seconds: 9.6,
  realtime_speedup_x: 0.49,
  portrait_render_seconds: 2.311,
  output_file_bytes: 3821124,
};

interface PitchSlide {
  slideNumber: number;
  tag: string;
  title: string;
  headline: string;
  bullets: string[];
  metricHighlight: string;
}

const PITCH_SLIDES: PitchSlide[] = [
  {
    slideNumber: 1,
    tag: "Opening Hook",
    title: "Your AI. Your Story. Your Cinema.",
    headline: "100% Local-First AI Video Production Studio for BMSIT & Indie Creators",
    bullets: [
      "Transforms 20-30+ raw festival/event clips into a beat-synced multi-track MP4 edit.",
      "Zero paid SaaS subscriptions, zero cloud GPU queues, zero watermark lock-in.",
      "Combines genuine AI reasoning with full frame-level NLE timeline control.",
    ],
    metricHighlight: "INR 0 / $0 Recurring Cost",
  },
  {
    slideNumber: 2,
    tag: "Problem Statement",
    title: "Why Cloud Video AI Fails Students",
    headline: "Subscriptions, Upload Bottlenecks & Hallucinated Video Frames",
    bullets: [
      "Commercial AI suites cost ~$25-$65/user/month — prohibitive across a 50-student college club.",
      "Uploading gigabytes of 1080p/4K fest footage over campus Wi-Fi stalls workflows and risks privacy.",
      "Text-to-video generators invent fake pixels instead of editing real authentic footage.",
    ],
    metricHighlight: "$27,000+ Club Annual SaaS Cost Avoided",
  },
  {
    slideNumber: 3,
    tag: "Architecture Innovation",
    title: "Zero-Failure Dual-Mode AI Director",
    headline: "Ollama Local LLM Paired with Deterministic 4-Act Heuristic Sequencer",
    bullets: [
      "Queries local Ollama (llama3.2) for structured JSON storyboards when available.",
      "Automatically engages a deterministic 4-Act Algorithmic Sequencer when completely offline.",
      "Enforces no-duplicate clip constraints and stores every edit in SQLite/PostgreSQL revisions.",
    ],
    metricHighlight: "100% Uptime Even Offline",
  },
  {
    slideNumber: 4,
    tag: "Computer Vision",
    title: "Transparent Quality & Scene Intelligence",
    headline: "PySceneDetect Cut Boundaries + OpenCV Sharpness, Exposure & dHash Dedupe",
    bullets: [
      "Laplacian variance sharpness + luminance histograms rank every shot transparently (0-100).",
      "PySceneDetect identifies natural scene cuts inside long raw recordings automatically.",
      "Perceptual dHash flags near-duplicate burst clips before sequencing.",
    ],
    metricHighlight: "Natural Language Search Over Clips",
  },
  {
    slideNumber: 5,
    tag: "Audio & Speech",
    title: "Librosa Beat Sync & Local CPU Whisper",
    headline: "Musical Downbeat Alignment + INT8 Speech Subtitles & Ducking",
    bullets: [
      "Librosa analyzes tempo (BPM), onset strength, and 64-bar waveform peaks at 4.24x realtime.",
      "Snaps video cut transitions onto musical beats within source trim bounds.",
      "faster-whisper (tiny INT8) burns crisp .ass subtitles locally with audio sidechain ducking.",
    ],
    metricHighlight: "4.24x Realtime Beat Extraction",
  },
  {
    slideNumber: 6,
    tag: "Render Performance",
    title: "SHA-256 Partial Segment Render Cache",
    headline: "FFmpeg Complex Filtergraph with Hardware Encoding & Instant Incremental Exports",
    bullets: [
      "Probes hardware automatically: h264_qsv / h264_nvenc / h264_amf with libx264 baseline.",
      "Fingerprints every clip + LUT + speed ramp + grade with SHA-256 keys.",
      "Editing one clip reuses untouched segments — verified 60.7% faster warm re-renders on host.",
    ],
    metricHighlight: "60.7% Faster Partial Re-Renders",
  },
  {
    slideNumber: 7,
    tag: "Copyright Safety",
    title: "Ethical Trend Style Recipes",
    headline: "Mathematical Rhythm Transfer Without Scraping or Frame Retention",
    bullets: [
      "Extracts cut cadence (cuts/min), motion velocity, LUT tone, and speed ramps only.",
      "Ephemeral reference uploads are wiped immediately after math extraction.",
      "URL analyzer blocks SSRF private/loopback subnets and downloads zero copyrighted streams.",
    ],
    metricHighlight: "Zero Copyrighted Streams Downloaded",
  },
  {
    slideNumber: 8,
    tag: "Institutional Readiness",
    title: "BMSIT Campus Security, Quotas & Postgres",
    headline: "Production RBAC, Storage Guards & Automated Cleanup Policies",
    bullets: [
      "Salted hashlib.scrypt passwords + HS256 PyJWT roles (student, club_lead, admin).",
      "Upload quota enforcement (HTTP 413) + startup/on-demand TTL disk cache pruning via psutil.",
      "Includes production PostgreSQL 15+ DDL (001_postgres_initial.sql) & SQLite migrator CLI.",
    ],
    metricHighlight: "Shell-Free Execution (shell=False)",
  },
  {
    slideNumber: 9,
    tag: "3-Minute Demo Flow",
    title: "Live Showcase Choreography",
    headline: "From 4 Full-HD Clips to Finished 1080p MP4 Live in Studio",
    bullets: [
      "Click Load Live HD Showcase to ingest committed 1080p media + 120 BPM track live.",
      "Demonstrate conversational trimming, Ctrl+Z Undo/Redo, Style Recipe apply & beat-sync.",
      "Export real 1080p MP4 via FFmpeg and verify warm partial-cache segment reuse.",
    ],
    metricHighlight: "Real H.264/AAC MP4 Output",
  },
  {
    slideNumber: 10,
    tag: "BMSIT Handover",
    title: "Permanent Campus Open-Source Asset",
    headline: "Verified Automated Test Suite & Complete Maintainer Documentation",
    bullets: [
      "Clean Next.js 15 + Python 3.12 FastAPI monorepo under permissive MIT License.",
      "Automated unit, security/SSRF, RBAC/quota, and real FFmpeg render integration tests.",
      "Complete architecture, API, deployment, and club handover guides included in docs/.",
    ],
    metricHighlight: "MIT Licensed Permanent Club Tool",
  },
];

export default function ShowcasePresentationPage() {
  const router = useRouter();
  const [status, setStatus] = useState<BackendShowcaseStatus | null>(null);
  const [report, setReport] = useState<BackendBenchmarkReport>(VERIFIED_HOST_SNAPSHOT);
  const [reportSource, setReportSource] = useState<"live" | "snapshot">("snapshot");
  const [loadingShowcase, setLoadingShowcase] = useState(false);
  const [runningBenchmark, setRunningBenchmark] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [statusNote, setStatusNote] = useState("");

  // Cost calculator controls
  const [studentCount, setStudentCount] = useState<number>(50);
  const [monthlySaasUsd, setMonthlySaasUsd] = useState<number>(45);

  // Interactive 10-slide viewer
  const [activeSlideIdx, setActiveSlideIdx] = useState<number>(0);

  useEffect(() => {
    fetchShowcaseStatus()
      .then((s) => setStatus(s))
      .catch(() => {});

    fetchShowcaseBenchmarks()
      .then((b) => {
        setReport(b);
        setReportSource("live");
      })
      .catch(() => {
        setReportSource("snapshot");
      });
  }, []);

  const handleLaunchLiveShowcase = async () => {
    setLoadingShowcase(true);
    setErrorMsg("");
    try {
      const res = await loadShowcaseProject(false);
      setStatusNote(res.message);
      router.push(`/editor?projectId=${encodeURIComponent(res.project.id)}`);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to load showcase (ensure FastAPI backend is running on port 8000).");
    } finally {
      setLoadingShowcase(false);
    }
  };

  const handleRerunBenchmarks = async () => {
    setRunningBenchmark(true);
    setErrorMsg("");
    try {
      const updated = await runShowcaseBenchmarks();
      setReport(updated);
      setReportSource("live");
      setStatusNote(`Fresh benchmark run completed at ${updated.generated_at}`);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Benchmark trigger failed (start FastAPI backend on port 8000).");
    } finally {
      setRunningBenchmark(false);
    }
  };

  const annualCloudUsd = studentCount * monthlySaasUsd * 12;
  const activeSlide = PITCH_SLIDES[activeSlideIdx];
  const coldBarPct = 100;
  const warmBarPct = Math.max(
    10,
    Math.min(100, (report.warm_cached_render_seconds / Math.max(0.1, report.cold_render_seconds)) * 100)
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Header Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-cine-border">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="gold">Phase 9 Hackathon Package</Badge>
            <Badge variant="emerald">$0 / INR 0 Recurring Cost</Badge>
            <Badge variant={reportSource === "live" ? "cyan" : "amber"}>
              {reportSource === "live" ? "Live Backend Telemetry" : `Host Snapshot (${report.generated_at})`}
            </Badge>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            CINEFLOW AI — Jury Showcase & Benchmarks
          </h1>
          <p className="text-sm text-gray-300 max-w-3xl">
            Interactive presentation hub featuring measured Full-HD pipeline benchmarks, 1-click live showcase studio
            loading, open-source architecture blueprints, and cloud TCO savings analysis.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <GoldButton
            variant="secondary"
            size="md"
            icon={runningBenchmark ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            onClick={handleRerunBenchmarks}
            disabled={runningBenchmark}
          >
            {runningBenchmark ? "Benchmarking Host..." : "Re-run Live Benchmark"}
          </GoldButton>
          <GoldButton
            size="md"
            icon={loadingShowcase ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            onClick={handleLaunchLiveShowcase}
            disabled={loadingShowcase}
          >
            {loadingShowcase ? "Ingesting 1080p Pack..." : "Launch Live HD Showcase"}
          </GoldButton>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-xs text-red-300">
          {errorMsg}
        </div>
      )}
      {statusNote && !errorMsg && (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{statusNote}</span>
        </div>
      )}

      {/* Top Measured Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <GlassPanel variant="active" className="p-5 space-y-1.5">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>Cold 1080p Render</span>
            <Film className="w-4 h-4 text-cine-gold-400" />
          </div>
          <div className="text-3xl font-bold text-white">{report.cold_render_seconds.toFixed(2)} s</div>
          <p className="text-[11px] text-gray-400">
            {report.output_duration_seconds.toFixed(1)}s MP4 ({report.hardware_profile.video_encoder})
          </p>
        </GlassPanel>

        <GlassPanel variant="surface" className="p-5 space-y-1.5">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>Warm Partial-Cache Render</span>
            <Zap className="w-4 h-4 text-cine-cyan-400" />
          </div>
          <div className="text-3xl font-bold text-cine-cyan-300">
            {report.warm_cached_render_seconds.toFixed(2)} s
          </div>
          <p className="text-[11px] text-emerald-400">
            {report.cache_speedup_percent.toFixed(1)}% faster ({report.segment_cache_hits}/{report.segment_cache_hits + report.segment_cache_misses} cached)
          </p>
        </GlassPanel>

        <GlassPanel variant="surface" className="p-5 space-y-1.5">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>9:16 Vertical Reel Export</span>
            <Gauge className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-bold text-white">{report.portrait_render_seconds.toFixed(2)} s</div>
          <p className="text-[11px] text-gray-400">1080x1920 Portrait Grade + Audio</p>
        </GlassPanel>

        <GlassPanel variant="surface" className="p-5 space-y-1.5">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>Host Hardware Profile</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white uppercase">{report.hardware_profile.profile} Tier</div>
          <p className="text-[11px] text-gray-400">
            {report.cpu_cores} Cores | {report.ram_total_gb.toFixed(1)} GB RAM | {report.hardware_profile.video_encoder}
          </p>
        </GlassPanel>
      </div>

      {/* Benchmark Speed Comparison & Interactive TCO Calculator */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <GlassPanel variant="surface" className="lg:col-span-7 p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-cine-border pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-cine-gold-400" /> Verified Host Pipeline Benchmarks
            </h2>
            <span className="text-[11px] font-mono text-gray-400">{report.host_os}</span>
          </div>

          {/* Cold vs Warm Visual Bar */}
          <div className="space-y-3 p-4 rounded-xl bg-cine-black/60 border border-cine-border">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-gray-200">Partial Segment Cache Speedup (1080p)</span>
              <span className="text-emerald-400 font-bold">{report.cache_speedup_percent.toFixed(1)}% Reduction</span>
            </div>
            <div className="space-y-2 text-[11px]">
              <div>
                <div className="flex justify-between text-gray-400 mb-1">
                  <span>Cold Full Render (3 segments + stitch)</span>
                  <span className="font-mono text-white">{report.cold_render_seconds.toFixed(3)} s</span>
                </div>
                <div className="w-full h-2.5 bg-cine-surface rounded-full overflow-hidden">
                  <div className="h-full bg-amber-400/80 rounded-full" style={{ width: `${coldBarPct}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-gray-400 mb-1">
                  <span>Warm Partial Re-Render ({report.segment_cache_hits} SHA-256 hits / {report.segment_cache_misses} edit)</span>
                  <span className="font-mono text-cine-cyan-300">{report.warm_cached_render_seconds.toFixed(3)} s</span>
                </div>
                <div className="w-full h-2.5 bg-cine-surface rounded-full overflow-hidden">
                  <div className="h-full bg-cine-cyan-400 rounded-full" style={{ width: `${warmBarPct.toFixed(1)}%` }} />
                </div>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-cine-border text-gray-400">
                  <th className="pb-2">Pipeline Stage</th>
                  <th className="pb-2 text-right">Wall Time</th>
                  <th className="pb-2 pl-3">Measured Throughput</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cine-border/40 text-gray-300">
                {report.stages.map((st) => (
                  <tr key={st.stage_id}>
                    <td className="py-2.5 pr-2 font-medium text-white">
                      {st.stage_name}
                      <div className="text-[10px] text-gray-500">{st.notes}</div>
                    </td>
                    <td className="py-2.5 text-right font-mono text-cine-gold-300 whitespace-nowrap">
                      {st.duration_seconds.toFixed(3)} s
                    </td>
                    <td className="py-2.5 pl-3 text-[11px] text-gray-300">{st.throughput_label}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassPanel>

        {/* Interactive Cloud SaaS TCO Calculator */}
        <GlassPanel variant="active" className="lg:col-span-5 p-6 space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-cine-border pb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-400" /> $0 vs Cloud SaaS Calculator
              </h2>
              <Badge variant="emerald">TCO Analysis</Badge>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs text-gray-300 mb-1">
                  <span>BMSIT Students / Club Seats</span>
                  <span className="font-mono text-cine-gold-300 font-bold">{studentCount} seats</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={200}
                  value={studentCount}
                  onChange={(e) => setStudentCount(Number(e.target.value))}
                  className="w-full accent-cine-gold-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs text-gray-300 mb-1">
                  <span>Illustrative SaaS Bundle (NLE + AI + Speech API)</span>
                  <span className="font-mono text-white font-bold">${monthlySaasUsd} / seat / mo</span>
                </div>
                <input
                  type="range"
                  min={15}
                  max={85}
                  step={5}
                  value={monthlySaasUsd}
                  onChange={(e) => setMonthlySaasUsd(Number(e.target.value))}
                  className="w-full accent-cine-cyan-400"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20">
                <span className="text-[11px] text-red-300">Commercial Cloud Stack</span>
                <div className="text-2xl font-extrabold text-white mt-1">
                  ${annualCloudUsd.toLocaleString()}
                </div>
                <span className="text-[10px] text-gray-400">per academic year</span>
              </div>
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                <span className="text-[11px] text-emerald-300">CINEFLOW AI Local Studio</span>
                <div className="text-2xl font-extrabold text-emerald-300 mt-1">$0</div>
                <span className="text-[10px] text-gray-300">INR 0 recurring API cost</span>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-cine-black/60 border border-cine-border text-[11px] text-gray-300 space-y-1.5">
            <div className="font-semibold text-cine-gold-300">Committed Full-HD Showcase Pack:</div>
            {status ? (
              <p>
                {status.sample_files.length} files verified ({(status.total_sample_bytes / (1024 * 1024)).toFixed(2)} MB) in{" "}
                <span className="font-mono text-gray-200">assets/sample_media/</span>.
              </p>
            ) : (
              <p>5 procedural copyright-free assets (4x 1080p MP4 + 120 BPM WAV, ~2.49 MB).</p>
            )}
          </div>
        </GlassPanel>
      </div>

      {/* System Pipeline Architecture Blueprint */}
      <GlassPanel variant="surface" className="p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-cine-border pb-3">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-cine-cyan-400" /> Local-First End-to-End Architecture Flow
          </h2>
          <Badge variant="gold">Zero External Dependencies</Badge>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
          {[
            {
              step: "1. Security & Ingest",
              tech: "Magic Bytes + FFprobe + 720p Proxy",
              detail: "Path-sanitized uploads, quota checks (413), hardware-profile proxy generation.",
            },
            {
              step: "2. CV & Audio Intel",
              tech: "PySceneDetect + OpenCV + Librosa",
              detail: "Cut splitting, Laplacian blur/exposure scoring, dHash dedupe, beat/BPM tracking.",
            },
            {
              step: "3. Dual AI Director",
              tech: "Ollama (llama3.2) + 4-Act Fallback",
              detail: "Natural prompts or voice commands converted to validated multi-track timelines.",
            },
            {
              step: "4. Studio & Diff UI",
              tech: "Next.js 15 + Persistent Undo/Redo",
              detail: "Multi-track scrub preview, conversational edits, CSS/LUT filters & Style Recipes.",
            },
            {
              step: "5. FFmpeg Cache Render",
              tech: "SHA-256 SegmentCache + qsv/x264",
              detail: "Complex filtergraph, ASS captions, sidechain ducking & 60.7% faster partial renders.",
            },
          ].map((node) => (
            <div
              key={node.step}
              className="p-4 rounded-xl bg-cine-black/60 border border-cine-border space-y-1.5"
            >
              <div className="text-[11px] font-mono text-cine-gold-400">{node.step}</div>
              <div className="font-bold text-white">{node.tech}</div>
              <p className="text-[11px] text-gray-400 leading-relaxed">{node.detail}</p>
            </div>
          ))}
        </div>
      </GlassPanel>

      {/* Interactive 10-Slide Pitch Deck Explorer */}
      <GlassPanel variant="active" className="p-6 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-cine-border pb-4">
          <div className="flex items-center gap-2">
            <Presentation className="w-5 h-5 text-cine-gold-400" />
            <h2 className="text-lg font-bold text-white">Interactive 10-Slide Hackathon Pitch Deck</h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveSlideIdx((i) => Math.max(0, i - 1))}
              disabled={activeSlideIdx === 0}
              className="px-3 py-1.5 rounded-lg bg-cine-black border border-cine-border text-xs text-gray-200 hover:border-cine-gold-400 disabled:opacity-40 flex items-center gap-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Prev
            </button>
            <span className="text-xs font-mono text-cine-gold-300 px-2">
              Slide {activeSlide.slideNumber} / {PITCH_SLIDES.length}
            </span>
            <button
              type="button"
              onClick={() => setActiveSlideIdx((i) => Math.min(PITCH_SLIDES.length - 1, i + 1))}
              disabled={activeSlideIdx === PITCH_SLIDES.length - 1}
              className="px-3 py-1.5 rounded-lg bg-cine-black border border-cine-border text-xs text-gray-200 hover:border-cine-gold-400 disabled:opacity-40 flex items-center gap-1"
            >
              Next <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Slide Body */}
        <div className="p-6 rounded-2xl bg-cine-black/80 border border-cine-gold-500/30 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          <div className="lg:col-span-8 space-y-3">
            <Badge variant="cyan">{activeSlide.tag}</Badge>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-white">{activeSlide.title}</h3>
            <p className="text-sm text-cine-gold-300 font-medium">{activeSlide.headline}</p>
            <ul className="space-y-2 pt-2">
              {activeSlide.bullets.map((b, bIdx) => (
                <li key={bIdx} className="flex items-start gap-2 text-xs sm:text-sm text-gray-300">
                  <Sparkles className="w-4 h-4 text-cine-gold-400 shrink-0 mt-0.5" />
                  <span>{b}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-4 p-5 rounded-xl bg-cine-surface border border-cine-border text-center space-y-2">
            <ShieldCheck className="w-7 h-7 text-emerald-400 mx-auto" />
            <div className="text-[11px] uppercase tracking-wider text-gray-400">Verified Proof Point</div>
            <div className="text-lg font-extrabold text-white">{activeSlide.metricHighlight}</div>
          </div>
        </div>

        {/* Slide Index Pills */}
        <div className="flex flex-wrap gap-1.5 pt-1">
          {PITCH_SLIDES.map((s, idx) => (
            <button
              key={s.slideNumber}
              type="button"
              onClick={() => setActiveSlideIdx(idx)}
              className={`px-2.5 py-1 rounded text-[11px] font-medium border transition-colors ${
                idx === activeSlideIdx
                  ? "bg-cine-gold-500/20 border-cine-gold-400 text-cine-gold-300"
                  : "bg-cine-black/50 border-cine-border text-gray-400 hover:text-white"
              }`}
            >
              {s.slideNumber}. {s.tag}
            </button>
          ))}
        </div>
      </GlassPanel>
    </div>
  );
}

