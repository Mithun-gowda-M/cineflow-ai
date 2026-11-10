"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Film, Sparkles, LayoutDashboard, UploadCloud, ShieldCheck, LogIn, LogOut, Presentation } from "lucide-react";
import { GoldButton } from "./ui/GoldButton";
import { Badge } from "./ui/Badge";
import { cn } from "@/lib/utils";
import { BackendUserPublic, clearAuthSession, getStoredAuthUser } from "@/lib/api";

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const [authUser, setAuthUser] = useState<BackendUserPublic | null>(null);

  useEffect(() => {
    const sync = () => setAuthUser(getStoredAuthUser());
    sync();
    window.addEventListener("cineflow-auth-changed", sync);
    return () => window.removeEventListener("cineflow-auth-changed", sync);
  }, []);

  // If in editor, render full-width editor navbar instead of default landing navbar
  if (pathname === "/editor") {
    return null;
  }

  const links = [
    { href: "/", label: "Home" },
    { href: "/features", label: "Technology" },
    { href: "/showcase", label: "Showcase", icon: <Presentation className="w-4 h-4" /> },
    { href: "/dashboard", label: "Dashboard", icon: <LayoutDashboard className="w-4 h-4" /> },
    { href: "/upload", label: "Media Hub", icon: <UploadCloud className="w-4 h-4" /> },
    { href: "/admin", label: "Admin", icon: <ShieldCheck className="w-4 h-4" /> },
  ];

  return (
    <header className="sticky top-0 z-40 w-full bg-cine-black/80 backdrop-blur-xl border-b border-cine-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gold-gradient p-[1px] flex items-center justify-center shadow-gold-sm transition-transform group-hover:scale-105">
            <div className="w-full h-full bg-cine-black rounded-[11px] flex items-center justify-center">
              <Film className="w-5 h-5 text-cine-gold-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-wider text-white">CINEFLOW</span>
              <span className="text-xs font-semibold text-cine-gold-400 px-1.5 py-0.5 rounded bg-cine-gold-500/10 border border-cine-gold-500/20">AI</span>
            </div>
            <p className="text-[10px] text-gray-400 -mt-0.5 tracking-tight hidden sm:block">Your AI. Your Story. Your Cinema.</p>
          </div>
        </Link>

        {/* Links */}
        <nav className="hidden md:flex items-center gap-1">
          {links.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "px-3 py-1.5 text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5",
                  isActive
                    ? "text-cine-gold-400 bg-cine-gold-500/10 border border-cine-gold-500/20"
                    : "text-gray-300 hover:text-white hover:bg-white/5"
                )}
              >
                {link.icon}
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Right CTA */}
        <div className="flex items-center gap-3">
          {authUser ? (
            <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-cine-surface border border-cine-border text-xs">
              <span className="text-cine-gold-300 font-mono truncate max-w-[150px]">{authUser.email}</span>
              <button
                type="button"
                onClick={() => clearAuthSession()}
                className="text-gray-400 hover:text-red-400"
                title="Sign Out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <Link
              href="/auth/login"
              className="hidden lg:inline-flex items-center gap-1.5 text-xs text-gray-300 hover:text-cine-gold-300 px-2.5 py-1.5 rounded-lg border border-cine-border"
            >
              <LogIn className="w-3.5 h-3.5" /> Student Login
            </Link>
          )}
          <Badge variant="gold" className="hidden xl:inline-flex">
            BMSIT Open Studio
          </Badge>
          <Link href="/editor">
            <GoldButton size="sm" icon={<Sparkles className="w-4 h-4" />}>
              Launch Studio
            </GoldButton>
          </Link>
        </div>
      </div>
    </header>
  );
};

