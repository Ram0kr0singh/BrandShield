import React from "react";
import { Detection } from "../../api";
import { Badge } from "../common/Badge";
import { ShieldCheck, AlertTriangle } from "lucide-react";

interface OfficialVsSuspectProps {
  detection: Detection;
}

export const OfficialVsSuspect: React.FC<OfficialVsSuspectProps> = ({ detection }) => {
  const isOfficial = detection.official_match === true;
  const publisherEvidence = detection.evidence.find(
    (e) => e.signal_type === "PUBLISHER_MISMATCH"
  );
  const nameEvidence = detection.evidence.find(
    (e) => e.signal_type === "NAME_SIMILARITY" || e.signal_type === "LOOKALIKE_NAME"
  );

  const officialDevelopers = Array.isArray(publisherEvidence?.details?.official_developers)
    ? publisherEvidence.details.official_developers.join(", ")
    : "Authorized Brand Owner";

  const candidateDev = detection.candidate.publisher || "Observed Developer";

  const hasPublisherMismatch =
    publisherEvidence?.available &&
    publisherEvidence?.details?.result === "MISMATCH";

  return (
    <div className="aegis-card relative overflow-hidden mb-8">
      <div className="flex items-center justify-between mb-6 pb-3 border-b border-[var(--border-subtle)]">
        <div>
          <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)] uppercase font-semibold">
            DIVERGENCE ANALYSIS · BASELINE vs OBSERVED SPECIMEN
          </span>
          <p className="text-xs text-[var(--text-muted)] font-mono mt-0.5">
            Central identity divergence spine evaluating authentic brand baseline against candidate specimen.
          </p>
        </div>
      </div>

      {/* Central Divergence Grid with Spine */}
      <div className="relative grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Central hairline divergence spine */}
        <div className="hidden md:block absolute top-0 bottom-0 left-1/2 -ml-[0.5px] w-[1px] bg-gradient-to-b from-[var(--border-subtle)] via-[var(--border-default)] to-[var(--border-subtle)] z-10" />

        {/* Left Side: Authentic Brand Baseline */}
        <div className="space-y-4 pr-0 md:pr-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-[var(--color-legitimate)]" />
              <span className="font-mono text-xs font-semibold text-[var(--color-legitimate)] uppercase tracking-wider">
                AUTHENTIC BRAND BASELINE
              </span>
            </div>
            <span className="font-mono text-[10px] text-[var(--text-muted)]">ANCHORED</span>
          </div>

          <div className="p-4 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-md space-y-3 font-mono text-xs">
            <div>
              <span className="text-[10px] text-[var(--text-muted)] uppercase block">AUTHORIZED ENTITY NAME</span>
              <p className="font-serif text-lg text-[var(--text-primary)] font-normal mt-0.5">
                {(publisherEvidence?.details?.official_name as string) || (nameEvidence?.details?.official_name as string) || "Protected Brand Target"}
              </p>
            </div>

            <div>
              <span className="text-[10px] text-[var(--text-muted)] uppercase block">AUTHORIZED PUBLISHER / DEVELOPER</span>
              <p className="text-[var(--color-legitimate)] font-medium mt-0.5">
                {officialDevelopers}
              </p>
            </div>

            <div>
              <span className="text-[10px] text-[var(--text-muted)] uppercase block">AUTHENTICATION STATUS</span>
              <div className="mt-1">
                <Badge value="LEGITIMATE BASELINE" />
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Observed Candidate Specimen */}
        <div className="space-y-4 pl-0 md:pl-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {isOfficial ? (
                <ShieldCheck size={16} className="text-[var(--color-legitimate)]" />
              ) : (
                <AlertTriangle size={16} className="text-[var(--color-suspicious)]" />
              )}
              <span className="font-mono text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
                OBSERVED SPECIMEN CANDIDATE
              </span>
            </div>
            <span className="font-mono text-[10px] text-[var(--text-muted)]">SPECIMEN</span>
          </div>

          <div
            className={`p-4 rounded-md border space-y-3 font-mono text-xs ${
              isOfficial
                ? "bg-[var(--color-legitimate-bg)] border-[var(--color-legitimate-border)]"
                : "bg-[var(--bg-elevated)] border-[var(--border-subtle)]"
            }`}
          >
            <div>
              <span className="text-[10px] text-[var(--text-muted)] uppercase block">CANDIDATE SPECIMEN NAME</span>
              <p className="font-serif text-lg text-[var(--text-primary)] font-normal mt-0.5">
                {detection.candidate.name}
              </p>
            </div>

            <div>
              <span className="text-[10px] text-[var(--text-muted)] uppercase block">OBSERVED PUBLISHER / DEVELOPER</span>
              <p
                className={`font-medium mt-0.5 ${
                  hasPublisherMismatch
                    ? "text-[var(--color-critical)] font-bold"
                    : "text-[var(--text-primary)]"
                }`}
              >
                {candidateDev}
              </p>
            </div>

            <div>
              <span className="text-[10px] text-[var(--text-muted)] uppercase block">PUBLISHER VERDICT</span>
              <div className="mt-1">
                {hasPublisherMismatch ? (
                  <Badge value="PUBLISHER MISMATCH" />
                ) : isOfficial ? (
                  <Badge value="AUTHORIZED MATCH" />
                ) : (
                  <Badge value="UNVERIFIED PUBLISHER" />
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

