import React from "react";
import { Users, AppWindow, Globe } from "lucide-react";

interface PlatformIconProps {
  platform: string;
  className?: string;
}

export const PlatformIcon: React.FC<PlatformIconProps> = ({ platform, className = "" }) => {
  const p = platform.toUpperCase();

  if (p.includes("INSTAGRAM") || p.includes("X") || p.includes("FACEBOOK") || p.includes("LINKEDIN") || p.includes("TIKTOK") || p.includes("SOCIAL")) {
    return <Users size={16} className={`text-[var(--color-suspicious)] ${className}`} />;
  }

  if (p.includes("PLAY") || p.includes("APPLE") || p.includes("STORE") || p.includes("APP")) {
    return <AppWindow size={16} className={`text-[var(--color-low)] ${className}`} />;
  }

  return <Globe size={16} className={`text-[var(--text-muted)] ${className}`} />;
};
