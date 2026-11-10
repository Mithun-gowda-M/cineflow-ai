"use client";

import React, { useEffect, useRef, useState } from "react";
import { Mic, MicOff, Loader2 } from "lucide-react";
import { getVoiceStatus, transcribeVoiceBlob } from "@/lib/api";

interface VoiceCommandButtonProps {
  onTranscript: (text: string) => void;
  onError?: (message: string) => void;
  disabled?: boolean;
}

interface SpeechRecognitionAlternativeLike {
  transcript: string;
}

interface SpeechRecognitionResultLike {
  0: SpeechRecognitionAlternativeLike;
}

interface SpeechRecognitionEventLike {
  results: ArrayLike<SpeechRecognitionResultLike>;
}

interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((ev: SpeechRecognitionEventLike) => void) | null;
  onerror: ((ev: { error?: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}

export const VoiceCommandButton: React.FC<VoiceCommandButtonProps> = ({
  onTranscript,
  onError,
  disabled = false,
}) => {
  const [status, setStatus] = useState<"idle" | "recording" | "transcribing">("idle");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const speechRecRef = useRef<SpeechRecognitionLike | null>(null);

  const stopMediaTracks = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      stopMediaTracks();
      if (speechRecRef.current) {
        try {
          speechRecRef.current.stop();
        } catch {
          // ignore cleanup error
        }
      }
    };
  }, []);

  const startWebSpeechFallback = () => {
    const win = window as unknown as {
      SpeechRecognition?: new () => SpeechRecognitionLike;
      webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    };
    const RecCtor = win.SpeechRecognition || win.webkitSpeechRecognition;
    if (!RecCtor) {
      onError?.("Browser speech recognition unavailable and local Whisper model not ready.");
      setStatus("idle");
      return;
    }

    const recognition = new RecCtor();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    speechRecRef.current = recognition;
    setStatus("recording");

    recognition.onresult = (event) => {
      const spoken = event.results?.[0]?.[0]?.transcript?.trim();
      if (spoken) {
        onTranscript(spoken);
      }
    };
    recognition.onerror = (ev) => {
      onError?.(`Microphone speech capture error: ${ev.error || "permission denied"}`);
      setStatus("idle");
    };
    recognition.onend = () => {
      setStatus("idle");
    };

    try {
      recognition.start();
    } catch (err) {
      onError?.(err instanceof Error ? err.message : "Could not start voice dictation.");
      setStatus("idle");
    }
  };

  const handleToggleMic = async () => {
    if (status === "recording") {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      } else if (speechRecRef.current) {
        speechRecRef.current.stop();
      }
      return;
    }
    if (status === "transcribing" || disabled) return;

    onError?.("");
    const whisperStatus = await getVoiceStatus().catch(() => null);
    const canUseWhisperUpload =
      Boolean(whisperStatus?.ready) &&
      typeof navigator !== "undefined" &&
      Boolean(navigator.mediaDevices?.getUserMedia) &&
      typeof MediaRecorder !== "undefined";

    if (!canUseWhisperUpload) {
      startWebSpeechFallback();
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stopMediaTracks();
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        if (blob.size === 0) {
          setStatus("idle");
          return;
        }
        setStatus("transcribing");
        try {
          const res = await transcribeVoiceBlob(blob);
          if (res.text) {
            onTranscript(res.text);
          } else {
            onError?.("No clear speech detected in recording.");
          }
        } catch (err) {
          onError?.(err instanceof Error ? err.message : "Local Whisper transcription failed.");
        } finally {
          setStatus("idle");
        }
      };

      recorder.start();
      setStatus("recording");
    } catch {
      stopMediaTracks();
      startWebSpeechFallback();
    }
  };

  return (
    <button
      type="button"
      onClick={handleToggleMic}
      disabled={disabled || status === "transcribing"}
      className={`p-2 rounded-lg border text-xs flex items-center gap-1.5 transition-all disabled:opacity-40 ${
        status === "recording"
          ? "bg-red-500/20 text-red-400 border-red-500 animate-pulse"
          : status === "transcribing"
          ? "bg-cine-cyan-500/20 text-cine-cyan-300 border-cine-cyan-500/50"
          : "bg-cine-card text-gray-300 border-cine-border hover:text-cine-gold-400"
      }`}
      title="Record Voice Editing Command (Local Whisper / Speech API)"
    >
      {status === "transcribing" ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
      ) : status === "recording" ? (
        <MicOff className="w-3.5 h-3.5" />
      ) : (
        <Mic className="w-3.5 h-3.5" />
      )}
      <span className="text-[11px]">
        {status === "recording" ? "Stop Mic" : status === "transcribing" ? "Whisper..." : "Voice"}
      </span>
    </button>
  );
};

