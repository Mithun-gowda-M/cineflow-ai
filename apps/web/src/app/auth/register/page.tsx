"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Film, Lock, Mail, User, ArrowRight, ShieldCheck } from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [department, setDepartment] = useState("Computer Science & Engineering");

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    router.push("/dashboard");
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4 relative">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-cine-cyan-500/10 blur-[130px] pointer-events-none rounded-full" />

      <div className="w-full max-w-md relative z-10">
        <GlassPanel variant="active" className="p-8 space-y-6">
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-bold text-white tracking-wide">Student Onboarding</h1>
            <p className="text-xs text-gray-400">Join BMSIT CINEFLOW AI Production Network</p>
          </div>

          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">
                Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-gray-500 absolute left-3 top-3" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Mithun Kumar"
                  className="w-full pl-9 pr-3 py-2 rounded-lg bg-cine-black border border-cine-border text-white text-sm focus:outline-none focus:border-cine-gold-500 font-sans"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">
                Institutional Email (@bmsit.in)
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-gray-500 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name.dept@bmsit.in"
                  className="w-full pl-9 pr-3 py-2 rounded-lg bg-cine-black border border-cine-border text-white text-sm focus:outline-none focus:border-cine-gold-500 font-sans"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">
                Department
              </label>
              <select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-cine-black border border-cine-border text-white text-xs focus:outline-none focus:border-cine-gold-500 font-sans"
              >
                <option value="Computer Science & Engineering">Computer Science & Engineering (CSE)</option>
                <option value="Information Science & Engineering">Information Science & Engineering (ISE)</option>
                <option value="AI & Machine Learning">AI & Machine Learning (AIML)</option>
                <option value="Electronics & Communication">Electronics & Communication (ECE)</option>
              </select>
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
              <GoldButton type="submit" size="md" className="w-full" icon={<ArrowRight className="w-4 h-4" />}>
                Create Free Student Account
              </GoldButton>
            </div>
          </form>

          <div className="text-center text-xs text-gray-400">
            Already registered?{" "}
            <Link href="/auth/login" className="text-cine-gold-400 hover:underline">
              Log in to Studio
            </Link>
          </div>
        </GlassPanel>
      </div>
    </div>
  );
}

