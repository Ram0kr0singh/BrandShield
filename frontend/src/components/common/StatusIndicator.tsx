import React from "react";

interface StatusIndicatorProps {
  label?: string;
  active?: boolean;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  label = "MONITORING ACTIVE",
  active = true,
}) => {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs font-mono">
      <span
        className={`w-2 h-2 rounded-full ${
          active ? "bg-[var(--color-legitimate)]" : "bg-[var(--text-muted)]"
        } inline-block`}
        style={{
          boxShadow: active ? "0 0 8px rgba(134, 184, 164, 0.6)" : "none",
        }}
      />
      <span className="text-[var(--text-secondary)] text-[11px] tracking-wider uppercase">
        {label}
      </span>
    </div>
  );
};
