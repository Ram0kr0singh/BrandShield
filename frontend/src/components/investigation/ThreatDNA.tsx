import React from "react";
import { EvidenceSignal } from "../../api";

interface ThreatDNAProps {
  evidence: EvidenceSignal[];
}

export const ThreatDNA: React.FC<ThreatDNAProps> = ({ evidence }) => {
  return (
    <div className="aegis-card mb-8">
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-[var(--border-subtle)]">
        <div>
          <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)] uppercase font-semibold">
            THREAT DNA · DETERMINISTIC SPECTRAL BARCODE
          </span>
          <p className="text-xs text-[var(--text-muted)] font-mono mt-0.5">
            Persisted evidence signals rendered as authoritative spectral barcode bands.
          </p>
        </div>
      </div>

      {/* Spectral Barcode Strip Grid */}
      <div className="space-y-4">
        {evidence.map((sig) => {
          const isAvailable = sig.available;
          const score = sig.score;
          const label = sig.signal_type.replaceAll("_", " ");

          let bandColor = "var(--color-legitimate)";
          if (score !== null && score !== undefined) {
            if (score >= 70) bandColor = "var(--color-critical)";
            else if (score >= 30) bandColor = "var(--color-suspicious)";
          }

          const fillPct = score !== null && score !== undefined ? Math.min(Math.max(score, 5), 100) : 0;

          return (
            <div key={sig.signal_type} className="space-y-1.5 font-mono">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[var(--text-primary)] uppercase tracking-wider">
                    {label}
                  </span>
                  <span
                    className={`text-[9px] px-1.5 py-0.2 rounded border ${
                      isAvailable
                        ? "bg-[var(--bg-raised)] text-[var(--text-secondary)] border-[var(--border-subtle)]"
                        : "bg-[var(--bg-canvas)] text-[var(--text-muted)] border-[var(--border-subtle)]"
                    }`}
                  >
                    {isAvailable ? "EVALUATED" : "UNAVAILABLE"}
                  </span>
                </div>

                <span className="font-serif text-base text-[var(--text-primary)] font-normal">
                  {score !== null && score !== undefined ? score.toFixed(2) : "—"}
                </span>
              </div>

              {/* Spectral Barcode Strip (Segmented Visual Barcode) */}
              <div className="w-full h-2.5 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-sm overflow-hidden flex gap-0.5 p-0.5">
                {Array.from({ length: 20 }).map((_, idx) => {
                  const segmentPct = (idx + 1) * 5;
                  const isActive = isAvailable && fillPct >= segmentPct;
                  return (
                    <div
                      key={idx}
                      className="flex-1 h-full rounded-[1px] transition-colors duration-150"
                      style={{
                        backgroundColor: isActive ? bandColor : "rgba(255,255,255,0.03)",
                        opacity: isActive ? (segmentPct > 80 ? 1 : 0.8) : 0.2,
                      }}
                    />
                  );
                })}
              </div>

              {/* Monospace Detail Metadata */}
              <p className="text-[10px] text-[var(--text-muted)] truncate pt-0.5">
                {Object.entries(sig.details)
                  .map(([k, v]) => `${k}: ${typeof v === "object" ? JSON.stringify(v) : v}`)
                  .join(" · ")}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

