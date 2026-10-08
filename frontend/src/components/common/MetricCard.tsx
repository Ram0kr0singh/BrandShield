import React from "react";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: number | string;
  icon?: LucideIcon;
  subtext?: string;
  variant?: "default" | "critical" | "warning" | "success";
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  icon: Icon,
  subtext,
  variant = "default",
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case "critical":
        return { borderColor: "rgba(228, 87, 74, 0.3)", iconColor: "#e4574a" };
      case "warning":
        return { borderColor: "rgba(217, 174, 95, 0.3)", iconColor: "#d9ae5f" };
      case "success":
        return { borderColor: "rgba(134, 184, 164, 0.3)", iconColor: "#86b8a4" };
      default:
        return { borderColor: "var(--border-subtle)", iconColor: "var(--text-muted)" };
    }
  };

  const styles = getVariantStyles();

  return (
    <div
      className="aegis-card flex flex-col justify-between"
      style={{ borderColor: styles.borderColor }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono tracking-wider text-[var(--text-muted)] uppercase">
          {label}
        </span>
        {Icon && <Icon size={16} style={{ color: styles.iconColor }} />}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="font-serif text-3xl font-semibold tracking-tight text-[var(--text-primary)]">
          {value}
        </span>
      </div>
      {subtext && (
        <span className="text-xs text-[var(--text-muted)] mt-1.5 font-mono">
          {subtext}
        </span>
      )}
    </div>
  );
};
