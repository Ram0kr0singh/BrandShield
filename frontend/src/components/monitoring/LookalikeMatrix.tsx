import React from "react";
import { useNavigate } from "react-router-dom";
import { Detection } from "../../api";
import { Badge } from "../common/Badge";
import { ArrowRight } from "lucide-react";

interface LookalikeMatrixProps {
  detections: Detection[];
}

function renderTransformationDetails(
  transformations: any[] | undefined,
  official: string,
  candidate: string
) {
  if (!transformations || transformations.length === 0) {
    return (
      <span className="text-[var(--text-muted)] text-xs">
        No character sequence details recorded
      </span>
    );
  }

  return (
    <div className="space-y-2 font-mono text-xs">
      {transformations.map((t: any, idx: number) => {
        if (t.type === "CHARACTER_SUBSTITUTION") {
          return (
            <div key={idx} className="p-2 bg-[var(--bg-elevated)] rounded border border-[var(--border-subtle)] flex items-center justify-between">
              <span className="text-[var(--text-muted)] uppercase text-[10px]">SUBSTITUTION</span>
              <span className="text-[var(--color-suspicious)] font-bold">
                '{t.from}' → '{t.to}'
              </span>
            </div>
          );
        }
        if (t.type === "ADDED_WORDS" && t.tokens) {
          return (
            <div key={idx} className="p-2 bg-[var(--bg-elevated)] rounded border border-[var(--border-subtle)] flex items-center justify-between">
              <span className="text-[var(--text-muted)] uppercase text-[10px]">ADDED TOKENS</span>
              <span className="text-[var(--color-suspicious)] font-bold">
                + {t.tokens.join(", ")}
              </span>
            </div>
          );
        }
        if (t.type === "SPACING_VARIATION") {
          return (
            <div key={idx} className="p-2 bg-[var(--bg-elevated)] rounded border border-[var(--border-subtle)] flex items-center justify-between">
              <span className="text-[var(--text-muted)] uppercase text-[10px]">SPACING</span>
              <span className="text-[var(--color-suspicious)] font-bold">MODIFIED BOUNDARY</span>
            </div>
          );
        }
        return null;
      })}
    </div>
  );
}

export const LookalikeMatrix: React.FC<LookalikeMatrixProps> = ({ detections }) => {
  const navigate = useNavigate();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {detections.map((d) => {
        const lookalikeEvidence = d.evidence.find(
          (v) => v.signal_type === "LOOKALIKE_NAME"
        );
        const officialName = String(
          lookalikeEvidence?.details?.official_name || "Official Brand"
        );
        const candName = d.candidate.name;
        const transformations = lookalikeEvidence?.details?.transformations as any[];

        return (
          <div
            key={d.id}
            onClick={() => navigate(`/threats/${d.id}`)}
            className="aegis-card hover:border-[var(--border-strong)] cursor-pointer flex flex-col justify-between transition-colors"
          >
            <div>
              {/* Header telemetry */}
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-[var(--border-subtle)]">
                <Badge value={d.severity} />
                <div className="flex items-baseline gap-1 font-mono">
                  <span className="text-[10px] text-[var(--text-muted)]">SCORE</span>
                  <span className="font-serif text-lg text-[var(--text-primary)] font-normal">
                    {d.risk_score.toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Transformation Specimen Laboratory Box */}
              <div className="p-4 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-md mb-4">
                <div className="flex items-center justify-between font-mono text-[10px] text-[var(--text-muted)] uppercase mb-2">
                  <span>AUTHENTIC</span>
                  <span>TRANSFORMATION</span>
                </div>

                <div className="flex items-center justify-between gap-2 font-mono">
                  <span className="font-serif text-lg font-normal text-[var(--color-legitimate)]">
                    {officialName}
                  </span>
                  <ArrowRight size={14} className="text-[var(--text-muted)]" />
                  <span className="font-serif text-lg font-normal text-[var(--color-suspicious)]">
                    {candName}
                  </span>
                </div>
              </div>

              {/* Specific Transformation Breakdown */}
              <div className="space-y-1.5">
                <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider block">
                  TRANSFORMATION LAB EVIDENCE
                </span>
                {renderTransformationDetails(transformations, officialName, candName)}
              </div>
            </div>

            <div className="mt-6 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between font-mono text-[11px] text-[var(--text-muted)]">
              <span>{d.candidate.source.toUpperCase()}</span>
              <span className="text-[var(--color-legitimate)]">INSPECT SPECIMEN →</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

