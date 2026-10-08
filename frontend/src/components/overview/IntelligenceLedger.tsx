import React from "react";
import { useNavigate } from "react-router-dom";
import { Threat } from "../../api";
import { Badge } from "../common/Badge";
import { ArrowUpRight } from "lucide-react";

interface IntelligenceLedgerProps {
  threats: Threat[];
}

export const IntelligenceLedger: React.FC<IntelligenceLedgerProps> = ({ threats }) => {
  const navigate = useNavigate();

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-[var(--border-subtle)]">
        <div>
          <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)] uppercase font-semibold">
            RECENT INTELLIGENCE LEDGER
          </span>
          <p className="text-xs text-[var(--text-muted)] font-mono mt-0.5">
            Deterrent observations derived from persisted engine analysis.
          </p>
        </div>
      </div>

      {threats.length > 0 ? (
        <div className="space-y-0 divide-y divide-[var(--border-subtle)]">
          {threats.map((t) => (
            <div
              key={t.id}
              onClick={() => navigate(`/threats/${t.id}`)}
              className="py-4 px-3 group flex flex-col md:flex-row md:items-center justify-between gap-4 transition-colors duration-150 hover:bg-[var(--bg-surface)] cursor-pointer rounded-sm"
            >
              {/* Candidate & Channel */}
              <div className="flex items-baseline gap-4 min-w-[280px]">
                <span className="font-serif text-lg font-normal text-[var(--text-primary)] group-hover:text-white">
                  {t.name}
                </span>
                <span className="font-mono text-[11px] text-[var(--text-muted)] uppercase tracking-wider">
                  {t.source}
                </span>
              </div>

              {/* Classification */}
              <div className="font-mono text-xs text-[var(--text-muted)] hidden lg:block">
                {t.threat_type ? t.threat_type.replaceAll("_", " ") : "UNCATEGORIZED"}
              </div>

              {/* Risk Score & Severity Badge */}
              <div className="flex items-center gap-6">
                <div className="flex items-baseline gap-2">
                  <span className="font-mono text-[10px] text-[var(--text-muted)] uppercase">RISK</span>
                  <span className="font-serif text-xl font-normal text-[var(--text-primary)]">
                    {t.risk_score.toFixed(2)}
                  </span>
                </div>

                <Badge value={t.severity} />

                <ArrowUpRight
                  size={16}
                  className="text-[var(--text-faint)] group-hover:text-[var(--text-primary)] transition-colors"
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-12 text-center text-xs font-mono text-[var(--text-muted)]">
          No recent threat candidates recorded in active perimeter telemetry.
        </div>
      )}
    </div>
  );
};

