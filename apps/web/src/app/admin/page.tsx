"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Cpu,
  HardDrive,
  Activity,
  Users,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Database,
  Lock,
} from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { GoldButton } from "@/components/ui/GoldButton";
import { Badge } from "@/components/ui/Badge";
import {
  BackendAdminOverview,
  BackendAdminUserRecord,
  BackendMigrationStatus,
  getAdminMigrationStatus,
  getAdminOverview,
  getAdminUsers,
  getStoredAuthUser,
  triggerAdminCleanup,
  updateAdminUser,
} from "@/lib/api";

function formatBytes(bytes: number): string {
  if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
  if (bytes >= 1024 ** 2) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${Math.max(0, Math.round(bytes / 1024))} KB`;
}

export default function AdminDashboardPage() {
  const [overview, setOverview] = useState<BackendAdminOverview | null>(null);
  const [users, setUsers] = useState<BackendAdminUserRecord[]>([]);
  const [migration, setMigration] = useState<BackendMigrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState("");
  const [isCleaning, setIsCleaning] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");

  const loadDiagnostics = useCallback(async () => {
    setLoading(true);
    setAuthError("");
    try {
      const [ov, usrList, mig] = await Promise.all([
        getAdminOverview(),
        getAdminUsers(),
        getAdminMigrationStatus(),
      ]);
      setOverview(ov);
      setUsers(usrList);
      setMigration(mig);
    } catch (err) {
      setAuthError(
        err instanceof Error
          ? err.message
          : "Institutional Admin access requires Club Admin JWT authentication."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDiagnostics();
  }, [loadDiagnostics]);

  const handleCleanCache = async () => {
    setIsCleaning(true);
    setStatusMessage("");
    try {
      const res = await triggerAdminCleanup({
        purge_cache: true,
        purge_expired_renders: true,
        max_age_hours: 0,
      });
      setStatusMessage(
        `Purged ${res.files_removed} cache/render file(s) reclaiming ${formatBytes(res.freed_bytes)} cleanly.`
      );
      await loadDiagnostics();
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Cleanup failed.");
    } finally {
      setIsCleaning(false);
    }
  };

  const handleBumpQuota = async (u: BackendAdminUserRecord) => {
    const nextGb = Math.max(1, Math.round(u.storage_quota_bytes / 1024 ** 3) + 5);
    try {
      const updated = await updateAdminUser(u.id, { storage_quota_gb: nextGb });
      setUsers((prev) => prev.map((item) => (item.id === u.id ? updated : item)));
      setStatusMessage(`Updated storage quota for ${u.email} to ${nextGb} GB.`);
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Failed to adjust quota.");
    }
  };

  const handleToggleActive = async (u: BackendAdminUserRecord) => {
    try {
      const updated = await updateAdminUser(u.id, { is_active: !u.is_active });
      setUsers((prev) => prev.map((item) => (item.id === u.id ? updated : item)));
      setStatusMessage(
        `${updated.email} is now ${updated.is_active ? "Active" : "Suspended"}.`
      );
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Failed to update account status.");
    }
  };

  const currentUser = getStoredAuthUser();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
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
            Live OS telemetry, RBAC student quota control, expired cache purging, and PostgreSQL schema readiness.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <GoldButton
            variant="secondary"
            size="md"
            disabled={!overview || isCleaning}
            icon={<RefreshCw className={`w-4 h-4 ${isCleaning ? "animate-spin" : ""}`} />}
            onClick={handleCleanCache}
          >
            {isCleaning ? "Cleaning..." : "Purge Temp & Render Cache"}
          </GoldButton>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {authError && (
        <GlassPanel variant="active" className="p-6 space-y-3 border-amber-500/40">
          <div className="flex items-start gap-3">
            <Lock className="w-5 h-5 text-cine-gold-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-white">Club Admin Authentication Required</h3>
              <p className="text-xs text-gray-300">{authError}</p>
              {currentUser && (
                <p className="text-[11px] font-mono text-gray-400">
                  Current Session: {currentUser.email} (role: {currentUser.role})
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3 pt-1">
            <Link href="/auth/login">
              <GoldButton size="sm" icon={<ShieldCheck className="w-4 h-4" />}>
                Sign In via JWT Portal
              </GoldButton>
            </Link>
            <button
              type="button"
              onClick={loadDiagnostics}
              className="text-xs text-cine-cyan-400 hover:underline"
            >
              Retry Diagnostics
            </button>
          </div>
        </GlassPanel>
      )}

      {!loading && overview && (
        <>
          {/* Live System Resource Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <GlassPanel variant="surface" className="p-5 space-y-2">
              <div className="flex items-center justify-between text-gray-400 text-xs">
                <span>CPU Load ({overview.system.cpu_cores} Cores)</span>
                <Cpu className="w-4 h-4 text-cine-cyan-400" />
              </div>
              <div className="text-3xl font-bold text-white">{overview.system.cpu_percent}%</div>
              <p className="text-[11px] text-emerald-400">Encoder: {overview.system.hardware_encoder}</p>
            </GlassPanel>

            <GlassPanel variant="surface" className="p-5 space-y-2">
              <div className="flex items-center justify-between text-gray-400 text-xs">
                <span>System Memory</span>
                <Activity className="w-4 h-4 text-cine-gold-400" />
              </div>
              <div className="text-3xl font-bold text-white">{overview.system.memory_used_gb} GB</div>
              <p className="text-[11px] text-gray-500">
                of {overview.system.memory_total_gb} GB RAM ({overview.system.memory_percent}%)
              </p>
            </GlassPanel>

            <GlassPanel variant="surface" className="p-5 space-y-2">
              <div className="flex items-center justify-between text-gray-400 text-xs">
                <span>Managed Studio Storage</span>
                <HardDrive className="w-4 h-4 text-cine-gold-400" />
              </div>
              <div className="text-3xl font-bold text-white">
                {formatBytes(overview.storage.total_managed_bytes)}
              </div>
              <p className="text-[11px] text-gray-500">
                {overview.system.disk_free_gb} GB free on host disk
              </p>
            </GlassPanel>

            <GlassPanel variant="surface" className="p-5 space-y-2">
              <div className="flex items-center justify-between text-gray-400 text-xs">
                <span>Campus Accounts & Queue</span>
                <Users className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-3xl font-bold text-white">
                {overview.active_users_count}/{overview.total_users_count}
              </div>
              <p className="text-[11px] text-emerald-400">
                {overview.render_queue.completed || 0} Completed • {overview.render_queue.processing || 0} Running
              </p>
            </GlassPanel>
          </div>

          {/* Student Accounts & Quota Table */}
          <GlassPanel variant="surface" className="p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-cine-border">
              <h2 className="text-base font-bold text-white">Student Accounts & Quota Allocations</h2>
              <span className="text-xs text-gray-400">Live SQLite / RBAC Control</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-cine-border text-gray-400">
                    <th className="pb-3 font-semibold">Institutional Email</th>
                    <th className="pb-3 font-semibold">Role</th>
                    <th className="pb-3 font-semibold">Projects</th>
                    <th className="pb-3 font-semibold">Used</th>
                    <th className="pb-3 font-semibold">Quota Cap</th>
                    <th className="pb-3 font-semibold">Status</th>
                    <th className="pb-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cine-border/40 text-gray-200">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-white/5 transition-colors">
                      <td className="py-3 font-mono font-medium">{u.email}</td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded bg-cine-surface text-[11px] border border-cine-border text-cine-gold-400 uppercase">
                          {u.role}
                        </span>
                      </td>
                      <td className="py-3">{u.projects_count}</td>
                      <td className="py-3 font-mono text-gray-300">{formatBytes(u.used_storage_bytes)}</td>
                      <td className="py-3 font-mono text-gray-400">{formatBytes(u.storage_quota_bytes)}</td>
                      <td className="py-3">
                        <span
                          className={`text-[11px] font-semibold ${
                            u.is_active ? "text-emerald-400" : "text-red-400"
                          }`}
                        >
                          {u.is_active ? "Active" : "Suspended"}
                        </span>
                      </td>
                      <td className="py-3 text-right space-x-3">
                        <button
                          type="button"
                          onClick={() => handleBumpQuota(u)}
                          className="text-cine-gold-400 hover:underline text-xs"
                        >
                          +5 GB Quota
                        </button>
                        <button
                          type="button"
                          onClick={() => handleToggleActive(u)}
                          className={`hover:underline text-xs ${
                            u.is_active ? "text-red-400" : "text-emerald-400"
                          }`}
                        >
                          {u.is_active ? "Suspend" : "Activate"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassPanel>

          {/* Database & PostgreSQL Migration Readiness */}
          {migration && (
            <GlassPanel variant="surface" className="p-6 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-cine-border">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Database className="w-4 h-4 text-cine-cyan-400" /> Database Schema & PostgreSQL Migration Readiness
                </h2>
                <Badge variant={migration.postgres_ddl_ready ? "gold" : "amber"}>
                  {migration.postgres_ddl_ready ? `DDL Ready (${migration.schema_version})` : "DDL Missing"}
                </Badge>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2 text-xs">
                {Object.entries(migration.table_counts).map(([tbl, count]) => (
                  <div key={tbl} className="p-2 rounded bg-cine-black border border-cine-border text-center">
                    <div className="text-gray-400 font-mono text-[10px]">{tbl}</div>
                    <div className="text-lg font-bold text-white">{count}</div>
                  </div>
                ))}
              </div>
              <p className="text-[11px] font-mono text-gray-400">
                Active Engine: <span className="text-cine-cyan-300">{migration.active_engine}</span> • CLI:{" "}
                <span className="text-gray-200">{migration.postgres_migration_cli}</span>
              </p>
            </GlassPanel>
          )}
        </>
      )}

      {loading && (
        <div className="py-12 text-center text-xs text-gray-400 flex items-center justify-center gap-2">
          <AlertTriangle className="w-4 h-4 text-cine-gold-400 animate-pulse" />
          Loading institutional diagnostics...
        </div>
      )}
    </div>
  );
}
