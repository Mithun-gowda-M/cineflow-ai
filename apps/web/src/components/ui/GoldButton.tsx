import React from "react";
import { cn } from "@/lib/utils";

interface GoldButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  icon?: React.ReactNode;
}

export const GoldButton: React.FC<GoldButtonProps> = ({
  variant = "primary",
  size = "md",
  icon,
  className,
  children,
  ...props
}) => {
  const baseStyles = "inline-flex items-center justify-center font-medium transition-all duration-200 rounded-lg active:scale-95 disabled:opacity-50 disabled:pointer-events-none";

  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs gap-1.5",
    md: "px-4 py-2 text-sm gap-2",
    lg: "px-6 py-3 text-base gap-2.5",
  };

  const variantStyles = {
    primary: "bg-gold-gradient text-cine-black font-semibold hover:shadow-gold-sm hover:brightness-105",
    secondary: "bg-cine-card text-cine-gold-400 border border-cine-border hover:border-cine-gold-500 hover:bg-cine-panel",
    outline: "bg-transparent text-cine-gold-400 border border-cine-gold-500/50 hover:border-cine-gold-400 hover:bg-cine-gold-500/10",
    ghost: "bg-transparent text-gray-300 hover:text-cine-gold-400 hover:bg-white/5",
    danger: "bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30",
  };

  return (
    <button
      className={cn(baseStyles, sizeStyles[size], variantStyles[variant], className)}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </button>
  );
};
