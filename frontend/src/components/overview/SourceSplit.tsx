import React from "react";
import { Overview } from "../../api";

interface SourceSplitProps {
  overview: Overview;
}

export const SourceSplit: React.FC<SourceSplitProps> = ({ overview }) => {
  const { source_distribution } = overview;
  const social = source_distribution.find((s) => s.source === "Social Media")?.count || 0;
  const apps = source_distribution.find((s) => s.source === "App Stores")?.count || 0;
  const total = social + apps || 1;

  const socialPct = Math.round((social / total) * 100);
  const appsPct = Math.round((apps / total) * 100);

  return (
    <div className="py-6 border-y border-[var(--border-subtle)] my-8">
      <div className="flex items-center justify-between mb-4">
        <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)] uppercase font-semibold">
          MONITORING CHANNEL DISTRIBUTION
        </span>
        <span className="font-mono text-xs text-[var(--text-muted)]">
          {total} TOTAL MONITORED CANDIDATES
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        {/* Social Channel Split */}
        <div className="flex items-baseline justify-between pr-0 md:pr-6">
          <div>
            <span className="font-mono text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider block">
              SOCIAL MEDIA CHANNELS
            </span>
            <span className="font-mono text-[11px] text-[var(--text-muted)]">
              {social} MONITORED CANDIDATES
            </span>
          </div>
          <span className="font-serif text-3xl font-normal text-[var(--text-primary)]">
            {socialPct}%
          </span>
        </div>

        {/* Application Channel Split */}
        <div className="flex items-baseline justify-between pl-0 md:pl-6 border-t md:border-t-0 md:border-l border-[var(--border-subtle)] pt-4 md:pt-0">
          <div>
            <span className="font-mono text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider block">
              APPLICATION STORES
            </span>
            <span className="font-mono text-[11px] text-[var(--text-muted)]">
              {apps} MONITORED CANDIDATES
            </span>
          </div>
          <span className="font-serif text-3xl font-normal text-[var(--text-primary)]">
            {appsPct}%
          </span>
        </div>
      </div>

      {/* Subtle Hairline Proportion Bar */}
      <div className="w-full h-[2px] bg-[var(--bg-elevated)] mt-5 flex overflow-hidden">
        <div
          className="h-full bg-[var(--text-primary)] opacity-80 transition-all duration-300"
          style={{ width: `${socialPct}%` }}
        />
        <div
          className="h-full bg-[var(--text-muted)] opacity-40 transition-all duration-300"
          style={{ width: `${appsPct}%` }}
        />
      </div>
    </div>
  );
};

