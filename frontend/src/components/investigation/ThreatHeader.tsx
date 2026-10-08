import React from "react";
import { Detection, Investigation } from "../../api";
import { Badge } from "../common/Badge";

interface ThreatHeaderProps {
  detection: Detection;
  investigation: Investigation;
  onStatusChange: (newStatus: string) => void;
  busy?: boolean;
}

export const ThreatHeader: React.FC<ThreatHeaderProps> = ({
  detection,
  investigation,
  onStatusChange,
  busy = false,
}) => {
  const isOfficial = detection.official_match === true;
  const validStatuses = [
    "NEW",
    "INVESTIGATING",
    "CONFIRMED_THREAT",
    "FALSE_POSITIVE",
    "DISMISSED",
  ];

  return (
    <div className="pb-6 mb-6 border-b border-[var(--border-subtle)]">
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)] uppercase font-semibold">
              SPECIMEN FORENSIC DOSSIER
            </span>
            <span className="text-[var(--text-faint)]">·</span>
            <span className="font-mono text-[10px] text-[var(--text-muted)] font-semibold uppercase">
              ID: {detection.id.substring(0, 8)}
            </span>
          </div>

          <h1 className="font-serif text-3xl md:text-5xl font-normal text-[var(--text-primary)] tracking-tight">
            {detection.candidate.name}
          </h1>

          <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-[var(--text-muted)] mt-2">
            <span>CHANNEL: {detection.candidate.source.toUpperCase()}</span>
            {detection.candidate.publisher && (
              <>
                <span className="text-[var(--text-faint)]">·</span>
                <span>PUBLISHER: {detection.candidate.publisher}</span>
              </>
            )}
            {detection.candidate.package_identifier && (
              <>
                <span className="text-[var(--text-faint)]">·</span>
                <span>PACKAGE: {detection.candidate.package_identifier}</span>
              </>
            )}
          </div>
        </div>

        {/* Risk Score & State Control */}
        <div className="flex items-center gap-8 pl-0 lg:pl-8 border-l-0 lg:border-l border-[var(--border-subtle)]">
          <div>
            <span className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-wider block mb-0.5">
              AUTHORITATIVE RISK SCORE
            </span>
            <div className="flex items-baseline gap-3">
              <span className="font-serif text-5xl font-normal text-[var(--text-primary)] leading-none">
                {detection.risk_score.toFixed(2)}
              </span>
              {isOfficial ? (
                <Badge value="SAFE" />
              ) : (
                <Badge value={detection.severity} />
              )}
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="font-mono text-[10px] text-[var(--text-muted)] uppercase tracking-wider">
              INVESTIGATION STATE
            </label>
            <select
              value={investigation.status}
              disabled={busy}
              onChange={(e) => onStatusChange(e.target.value)}
              className="font-mono text-xs font-semibold px-3 py-1.5 bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-md text-[var(--text-primary)] cursor-pointer"
            >
              {validStatuses.map((st) => (
                <option key={st} value={st}>
                  {st.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};

