import React from "react";
import { cn } from "@/lib/utils";

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "gold" | "active" | "surface";
  children: React.ReactNode;
}

export const GlassPanel: React.FC<GlassPanelProps> = ({
  variant = "default",
  className,
  children,
  ...props
}) => {
  const variantStyles = {
    default: "cine-glass",
    gold: "cine-glass-gold",
    active: "cine-glass-active",
    surface: "bg-cine-surface border border-cine-border",
  };

  return (
    <div
      className={cn("rounded-xl transition-all duration-200", variantStyles[variant], className)}
      {...props}
    >
      {children}
    </div>
  );
};
