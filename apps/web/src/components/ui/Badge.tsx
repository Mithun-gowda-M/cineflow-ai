import React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps {
  variant?: "gold" | "cyan" | "emerald" | "amber" | "default";
  size?: "sm" | "md";
  className?: string;
  children: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "default",
  size = "sm",
  className,
  children,
}) => {
  const styles = {
    gold: "bg-cine-gold-500/15 text-cine-gold-400 border border-cine-gold-500/30",
    cyan: "bg-cine-cyan-500/15 text-cine-cyan-400 border border-cine-cyan-500/30",
    emerald: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
    amber: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
    default: "bg-gray-800/80 text-gray-300 border border-gray-700",
  };

  const sizes = {
    sm: "px-2 py-0.5 text-xs font-medium rounded-full",
    md: "px-2.5 py-1 text-xs font-semibold rounded-full",
  };

  return (
    <span className={cn("inline-flex items-center gap-1", styles[variant], sizes[size], className)}>
      {children}
    </span>
  );
};
