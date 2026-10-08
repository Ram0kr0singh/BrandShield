import React from "react";
import { Overview } from "../../api";
import { RefreshCw } from "lucide-react";

interface DigitalPerimeterBriefingProps {
  overview: Overview;
  onScan: () => void;
  scanning: boolean;
}

export const DigitalPerimeterBriefing: React.FC<DigitalPerimeterBriefingProps> = ({
  overview,
  onScan,
  scanning,
}) => {
  const { brand, summary, last_scan } = overview;
  const highRisk = summary.high_risk || 0;
  const detected = summary.detected_threats || 0;
  const totalMonitored = summary.total_candidates || 0;

  let narrativeStatus = `Continuous monitoring active across ${totalMonitored} channel candidates.`;
  if (highRisk > 0) {
    narrativeStatus = `Perimeter alert: ${highRisk} high-priority threat candidate${highRisk > 1 ? "s" : ""} require forensic inspection for ${brand.name}.`;
  } else if (detected === 0) {
    narrativeStatus = `Digital perimeter secure. Zero active threat vectors detected for ${brand.name}.`;
  }

  return (
    <div className="border-b border-[var(--border-subtle)] pb-8 mb-8">
      {/* Top Header Row */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--color-legitimate)] uppercase font-semibold">
              MONITORING ACTIVE
            </span>
            <span className="text-[var(--text-faint)]">·</span>
            <span className="font-mono text-[10px] tracking-widest text-[var(--text-muted)] uppercase">
              {brand.official_domain || "AUTHORITATIVE PERIMETER"}
            </span>
          </div>

          <h1 className="font-serif text-4xl md:text-5xl lg:text-6xl text-[var(--text-primary)] font-normal tracking-tight">
            {brand.name}
          </h1>

          <p className="font-serif italic text-lg md:text-xl text-[var(--text-secondary)] mt-2 max-w-2xl font-normal leading-snug">
            "{narrativeStatus}"
          </p>
        </div>

        {/* Dramatic Large Active Threat Number Treatment (Section 9) */}
        <div className="flex items-center gap-8 pl-0 lg:pl-8 border-l-0 lg:border-l border-[var(--border-subtle)]">
          <div className="flex items-baseline gap-4">
            <span className="font-serif text-6xl md:text-7xl font-normal text-[var(--text-primary)] leading-none">
              {detected}
            </span>
            <div className="flex flex-col">
              <span className="font-mono text-xs font-semibold tracking-widest text-[var(--text-primary)] uppercase">
                ACTIVE THREATS
              </span>
              <span className="font-mono text-[11px] text-[var(--text-muted)] mt-0.5">
                {highRisk} CRITICAL · {Math.max(0, detected - highRisk)} SUSPICIOUS
              </span>
            </div>
          </div>

          {/* Action Trigger */}
          <div className="flex flex-col items-end gap-1.5">
            <button
              className="btn btn-primary text-xs tracking-wider uppercase font-mono"
              onClick={onScan}
              disabled={scanning}
            >
              <RefreshCw size={13} className={scanning ? "spin" : ""} />
              {scanning ? "SCANNING..." : "SCAN PERIMETER"}
            </button>
            {last_scan && (
              <span className="font-mono text-[10px] text-[var(--text-muted)]">
                LAST SCAN:{" "}
                {last_scan.completed_at
                  ? new Date(last_scan.completed_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : "RECENT"}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

