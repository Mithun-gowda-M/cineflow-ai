"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  ShieldCheck, Cpu, HardDrive, Activity, Users, 
  Trash2, RefreshCw, CheckCircle2, AlertTriangle, ArrowLeft 
} from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";

export default function AdminDashboardPage() {
  const [isCleaning, setIsCleaning] = useState(false);
  const [cleanMessage, setCleanMessage] = useState("");

  const handleCleanCache = () => {
    setIsCleaning(true);
    setTimeout(() => {
      setIsCleaning(false);
      setCleanMessage("Successfully purged 2.4 GB of temporary proxy render caches.");
    }, 1200);
  };

  const studentAccounts = [
    { email: "mithun.k@bmsit.in", role: "Club Lead", projects: 8, storage: "4.8 GB", quota: "25.0 GB" },
    { email: "rahul.s@bmsit.in", role: "Student Member", projects: 3, storage: "1.2 GB", quota: "20.0 GB" },
    { email: "ananya.m@bmsit.in", role: "Student Member", projects: 5, storage: "3.1 GB", quota: "20.0 GB" },
    { email: "media.club@bmsit.in", role: "Admin", projects: 14, storage: "9.6 GB", quota: "50.0 GB" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-cine-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Campus Platform Admin & Diagnostics
            </h1>
            <Badge variant="gold">BMSIT Technical Club</Badge>
          </div>
          <p className="text-sm text-gray-400">
            Monitor institutional node health, student quotas, and rendering queue operations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <GoldButton
            variant="secondary"
            size="md"
            icon={<RefreshCw className={`w-4 h-4 ${isCleaning ? "animate-spin" : ""}`} />}
            onClick={handleCleanCache}
          >
            Purge Render Cache
          </GoldButton>
        </div>
      </div>

      {cleanMessage && (
        <div className="p-3 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4" />
          <span>{cleanMessage}</span>
        </div>
      )}

      {/* System Resource Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <GlassPanel variant="surface" className="p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>CPU Core Load</span>
            <Cpu className="w-4 h-4 text-cine-cyan-400" />
          </div>
          <div className="text-3xl font-bold text-white">24%</div>
          <p className="text-[11px] text-emerald-400">Adaptive CPU Encoder Active</p>
        </GlassPanel>

        <GlassPanel variant="surface" className="p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Memory Allocated</span>
            <Activity className="w-4 h-4 text-cine-gold-400" />
          </div>
          <div className="text-3xl font-bold text-white">3.4 GB</div>
          <p className="text-[11px] text-gray-500">of 16.0 GB System RAM</p>
        </GlassPanel>

        <GlassPanel variant="surface" className="p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Campus Storage Pool</span>
            <HardDrive className="w-4 h-4 text-cine-gold-400" />
          </div>
          <div className="text-3xl font-bold text-white">18.7 GB</div>
          <p className="text-[11px] text-gray-500">of 100 GB Local Allocation</p>
        </GlassPanel>

        <GlassPanel variant="surface" className="p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Active Student Users</span>
            <Users className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-bold text-white">4</div>
          <p className="text-[11px] text-emerald-400">All Nodes Healthy</p>
        </GlassPanel>
      </div>

      {/* Student Accounts Table */}
      <GlassPanel variant="surface" className="p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-cine-border">
          <h2 className="text-base font-bold text-white">Student Quota Allocations</h2>
          <span className="text-xs text-gray-400">Role-Based Access Control</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-cine-border text-gray-400">
                <th className="pb-3 font-semibold">Student Institutional Email</th>
                <th className="pb-3 font-semibold">Club Role</th>
                <th className="pb-3 font-semibold">Projects</th>
                <th className="pb-3 font-semibold">Storage Used</th>
                <th className="pb-3 font-semibold">Quota Cap</th>
                <th className="pb-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cine-border/40 text-gray-200">
              {studentAccounts.map((account, idx) => (
                <tr key={idx} className="hover:bg-white/5 transition-colors">
                  <td className="py-3 font-mono font-medium">{account.email}</td>
                  <td className="py-3">
                    <span className="px-2 py-0.5 rounded bg-cine-surface text-[11px] border border-cine-border text-cine-gold-400">
                      {account.role}
                    </span>
                  </td>
                  <td className="py-3">{account.projects}</td>
                  <td className="py-3 font-mono text-gray-300">{account.storage}</td>
                  <td className="py-3 font-mono text-gray-400">{account.quota}</td>
                  <td className="py-3 text-right">
                    <button className="text-cine-gold-400 hover:underline text-xs mr-3">
                      Adjust Quota
                    </button>
                    <button className="text-red-400 hover:underline text-xs">
                      Revoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassPanel>
    </div>
  );
}
