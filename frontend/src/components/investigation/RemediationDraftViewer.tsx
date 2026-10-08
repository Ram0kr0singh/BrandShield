import React, { useState } from "react";
import { Draft } from "../../api";
import { Badge } from "../common/Badge";
import { Copy, FileText, Check } from "lucide-react";

interface RemediationDraftViewerProps {
  drafts: Draft[];
  onGenerateDraft: (draftType: string) => void;
  busy?: boolean;
  source: string;
}

export const RemediationDraftViewer: React.FC<RemediationDraftViewerProps> = ({
  drafts,
  onGenerateDraft,
  busy = false,
  source,
}) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const defaultType = source === "App Store" ? "APP_STORE" : "SOCIAL_PLATFORM";

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard?.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="aegis-card mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="font-mono text-[11px] tracking-widest text-[var(--text-muted)] uppercase font-semibold">
            REMEDIATION NOTICE DRAFTS · TEMPLATES ONLY
          </span>
          <p className="text-xs text-[var(--text-muted)]">
            Local template generation based on persisted evidence. Remediation content is never sent automatically.
          </p>
        </div>

        <button
          className="btn btn-accent text-xs"
          onClick={() => onGenerateDraft(defaultType)}
          disabled={busy}
        >
          <FileText size={14} />
          Generate {defaultType.replaceAll("_", " ")} Draft
        </button>
      </div>

      {drafts.length > 0 ? (
        <div className="space-y-4">
          {drafts.map((d) => (
            <div
              key={d.id}
              className="p-4 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-lg font-mono text-xs"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Badge value="DRAFT ONLY" />
                  <span className="text-[var(--text-secondary)] font-semibold">
                    {d.draft_type.replaceAll("_", " ")}
                  </span>
                </div>
                <span className="text-[11px] text-[var(--text-muted)]">
                  {new Date(d.created_at).toLocaleString()} · {d.actor}
                </span>
              </div>

              <pre className="p-3 bg-[var(--bg-canvas)] border border-[var(--border-subtle)] rounded text-[11px] text-[var(--text-primary)] font-mono whitespace-pre-wrap overflow-x-auto max-h-60 mb-3">
                {d.content}
              </pre>

              <div className="flex justify-end">
                <button
                  className="btn text-xs py-1 px-3"
                  onClick={() => handleCopy(d.id, d.content)}
                >
                  {copiedId === d.id ? (
                    <>
                      <Check size={12} className="text-[var(--color-legitimate)]" /> Copied to Clipboard
                    </>
                  ) : (
                    <>
                      <Copy size={12} /> Copy Draft Text
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-6 text-center text-xs font-mono text-[var(--text-muted)]">
          No remediation drafts generated yet. Click above to produce a local draft template.
        </div>
      )}
    </div>
  );
};
