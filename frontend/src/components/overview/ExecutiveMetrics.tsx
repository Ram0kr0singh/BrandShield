import React from "react";
import { Overview } from "../../api";

interface ExecutiveMetricsProps {
  overview: Overview;
}

export const ExecutiveMetrics: React.FC<ExecutiveMetricsProps> = ({ overview }) => {
  const { summary } = overview;
  const detectedThreats = summary.detected_threats ?? 0;
  const highRisk = summary.high_risk ?? 0;
  const lookalikes = summary.lookalikes ?? 0;
  const candidatesMonitored = summary.total_candidates ?? 0;

  const metrics = [
    {
      label: "DETECTED THREATS",
      value: detectedThreats,
      caption: detectedThreats === 1 ? "Active threat" : "Active threats",
      dotColor: detectedThreats > 0 ? "bg-[var(--color-critical)]" : "bg-[var(--color-legitimate)]",
      valueColor: detectedThreats > 0 ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)]",
    },
    {
      label: "HIGH RISK",
      value: highRisk,
      caption: highRisk > 0 ? "Critical priority" : "None detected",
      dotColor: highRisk > 0 ? "bg-[var(--color-critical)]" : "bg-[var(--text-muted)]",
      valueColor: highRisk > 0 ? "text-[var(--color-critical)]" : "text-[var(--text-secondary)]",
    },
    {
      label: "LOOK-ALIKES",
      value: lookalikes,
      caption: lookalikes > 0 ? "Name variants" : "Zero variants",
      dotColor: lookalikes > 0 ? "bg-[var(--color-suspicious)]" : "bg-[var(--color-legitimate)]",
      valueColor: lookalikes > 0 ? "text-[var(--color-suspicious)]" : "text-[var(--text-secondary)]",
    },
    {
      label: "CANDIDATES MONITORED",
      value: candidatesMonitored,
      caption: "Perimeter surface",
      dotColor: "bg-[var(--color-legitimate)]",
      valueColor: "text-[var(--text-primary)]",
    },
  ];

  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)] rounded-lg grid grid-cols-2 lg:grid-cols-4 divide-y lg:divide-y-0 lg:divide-x divide-[var(--border-subtle)] mb-8">
      {metrics.map((m) => (
        <div key={m.label} className="p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <span className="font-mono text-[10px] tracking-[0.18em] text-[var(--text-muted)] uppercase font-semibold">
              {m.label}
            </span>
            <span className={`w-1.5 h-1.5 rounded-full ${m.dotColor}`} />
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`font-serif text-3xl lg:text-4xl font-normal leading-none ${m.valueColor}`}>
              {m.value}
            </span>
            <span className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-wider">
              {m.caption}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};
