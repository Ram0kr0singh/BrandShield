import React from "react";
import { AnalystAnalysis } from "../../api";
import { Sparkles, FileText } from "lucide-react";

interface AIAnalystPanelProps {
  analysis: AnalystAnalysis | null;
  analyzing: boolean;
  onRunAnalysis: () => void;
  error?: string;
}

export const AIAnalystPanel: React.FC<AIAnalystPanelProps> = ({
  analysis,
  analyzing,
  onRunAnalysis,
  error,
}) => {
  return (
    <div className="aegis-card-raised mb-8 border border-[var(--color-purple)]/25">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-3">
          <FileText size={18} className="text-[var(--color-purple)]" />
          <div>
            <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--color-purple)] uppercase font-semibold">
              ANALYST NOTE · EXPLANATORY ASSESSMENT
            </span>
            <p className="text-xs text-[var(--text-muted)] font-mono mt-0.5">
              Evidence-grounded prose assessment generated server-side.
            </p>
          </div>
        </div>

        <button
          className="btn btn-ai"
          onClick={onRunAnalysis}
          disabled={analyzing}
        >
          <Sparkles size={13} className={analyzing ? "spin" : ""} />
          {analyzing ? "GENERATING ASSESSMENTS..." : "GENERATE ANALYST NOTE"}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-[var(--color-critical-bg)] border border-[var(--color-critical-border)] rounded text-xs font-mono text-[var(--color-critical)] mb-6">
          {error}
        </div>
      )}

      {analysis ? (
        <div className="space-y-6">
          {/* Assessment Heading & Summary */}
          <div>
            <span className="font-mono text-[10px] tracking-widest text-[var(--text-muted)] uppercase block mb-1">
              ASSESSMENT
            </span>
            <p className="font-serif text-lg md:text-xl text-[var(--text-primary)] leading-relaxed italic bg-[var(--bg-elevated)] p-5 rounded border border-[var(--border-subtle)]">
              "{analysis.summary}"
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 text-xs font-mono">
            {/* Left Column: Rationale & Key Evidence */}
            <div className="space-y-4">
              <div>
                <span className="text-[var(--text-muted)] uppercase text-[10px] tracking-wider block mb-1">
                  RISK RATIONALE
                </span>
                <p className="text-[var(--text-secondary)] leading-relaxed bg-[var(--bg-elevated)] p-4 rounded border border-[var(--border-subtle)]">
                  {analysis.risk_rationale}
                </p>
              </div>

              <div>
                <span className="text-[var(--text-muted)] uppercase text-[10px] tracking-wider block mb-1">
                  KEY EVIDENCE
                </span>
                <div className="space-y-1.5">
                  {analysis.key_evidence.map((ev) => (
                    <div
                      key={ev.signal_type}
                      className="p-3 bg-[var(--bg-elevated)] rounded border border-[var(--border-subtle)] flex items-center justify-between"
                    >
                      <span className="text-[var(--text-primary)]">{ev.summary}</span>
                      <span className="font-serif text-sm font-normal text-[var(--text-primary)]">
                        {ev.score !== null ? ev.score.toFixed(2) : "UNAVAILABLE"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Actions & Uncertainties */}
            <div className="space-y-4">
              <div>
                <span className="text-[var(--text-muted)] uppercase text-[10px] tracking-wider block mb-1">
                  RECOMMENDED ACTIONS
                </span>
                <ol className="list-decimal list-inside space-y-1.5 bg-[var(--bg-elevated)] p-4 rounded border border-[var(--border-subtle)] text-[var(--text-secondary)]">
                  {analysis.recommended_actions.map((act, i) => (
                    <li key={i} className="mb-1">
                      {act}
                    </li>
                  ))}
                </ol>
              </div>

              <div>
                <span className="text-[var(--text-muted)] uppercase text-[10px] tracking-wider block mb-1">
                  UNCERTAINTIES & LIMITATIONS
                </span>
                <ul className="list-disc list-inside space-y-1.5 bg-[var(--bg-elevated)] p-4 rounded border border-[var(--border-subtle)] text-[var(--text-muted)]">
                  {analysis.uncertainties.map((unc, i) => (
                    <li key={i}>{unc}</li>
                  ))}
                </ul>
              </div>

              <div className="p-3 bg-[var(--bg-elevated)] rounded border border-[var(--border-subtle)] text-[11px] text-[var(--text-muted)] flex items-center justify-between">
                <span>MODEL PROVIDER: {analysis.provider.replaceAll("_", " ").toUpperCase()}</span>
                <span>GENERATED: {new Date(analysis.generated_at).toLocaleTimeString()}</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="py-8 text-center text-xs font-mono text-[var(--text-muted)]">
          Click "GENERATE ANALYST NOTE" to request an evidence-grounded prose assessment.
        </div>
      )}
    </div>
  );
};

