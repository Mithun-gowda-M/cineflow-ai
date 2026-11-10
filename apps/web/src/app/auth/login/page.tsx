"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Film, Lock, Mail, Sparkles, ArrowRight, ShieldCheck, AlertCircle, RefreshCw } from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { GoldButton } from "@/components/ui/GoldButton";
import { loginStudent } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");
    try {
      const auth = await loginStudent({ email: email.trim(), password });
      if (auth.user.role === "admin" || auth.user.role === "club_lead") {
        router.push("/admin");
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  const fillDemoStudent = () => {
    setEmail("student.innovator@bmsit.in");
    setPassword("bmsit2026cineflow");
  };

  const fillDemoAdmin = () => {
    setEmail("media.club@bmsit.in");
    setPassword("bmsit2026admin");
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4 relative">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-cine-gold-500/10 blur-[130px] pointer-events-none rounded-full" />

      <div className="w-full max-w-md relative z-10">
        <GlassPanel variant="active" className="p-8 space-y-6">
          {/* Brand Header */}
          <div className="text-center space-y-2">
            <div className="w-12 h-12 rounded-xl bg-gold-gradient p-[1px] mx-auto flex items-center justify-center shadow-gold-sm">
              <div className="w-full h-full bg-cine-black rounded-[11px] flex items-center justify-center">
                <Film className="w-6 h-6 text-cine-gold-400" />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-wide">CINEFLOW AI</h1>
            <p className="text-xs text-gray-400">Institutional JWT Portal • BMSIT Open Studio</p>
          </div>

          {errorMsg && (
            <div className="p-3 rounded-lg bg-red-500/15 border border-red-500/30 text-xs text-red-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">
                College Domain Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-gray-500 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="student@bmsit.in"
                  className="w-full pl-9 pr-3 py-2 rounded-lg bg-cine-black border border-cine-border text-white text-sm focus:outline-none focus:border-cine-gold-500 font-sans"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-500 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2 rounded-lg bg-cine-black border border-cine-border text-white text-sm focus:outline-none focus:border-cine-gold-500 font-sans"
                />
              </div>
            </div>

            <div className="pt-2">
              <GoldButton
                type="submit"
                size="md"
                className="w-full"
                disabled={loading}
                icon={loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
              >
                {loading ? "Signing In..." : "Authenticate & Enter Studio"}
              </GoldButton>
            </div>
          </form>

          {/* Demo Shortcuts & Register */}
          <div className="pt-3 border-t border-cine-border flex flex-col items-center gap-2 text-center">
            <div className="flex flex-wrap items-center justify-center gap-4">
              <button
                type="button"
                onClick={fillDemoStudent}
                className="text-xs text-cine-gold-400 hover:underline inline-flex items-center gap-1 font-medium"
              >
                <Sparkles className="w-3.5 h-3.5" /> Demo Student
              </button>
              <button
                type="button"
                onClick={fillDemoAdmin}
                className="text-xs text-cine-cyan-400 hover:underline inline-flex items-center gap-1 font-medium"
              >
                <ShieldCheck className="w-3.5 h-3.5" /> Demo Club Admin
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              New BMSIT member?{" "}
              <Link href="/auth/register" className="text-cine-gold-400 hover:underline">
                Register account
              </Link>
            </p>
          </div>
        </GlassPanel>
      </div>
    </div>
  );
}
