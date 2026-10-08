import React, { useCallback, useEffect, useState } from "react";
import { api, Detection } from "../api";
import { LoadingState } from "../components/common/LoadingState";
import { LookalikeMatrix } from "../components/monitoring/LookalikeMatrix";

export const LookalikeDetectionPage: React.FC = () => {
  const [all, setAll] = useState<Detection[] | null>(null);
  const [error, setError] = useState("");

  const loadData = useCallback(() => {
    setError("");
    api
      .detections()
      .then(setAll)
      .catch(() => setError("Unable to load look-alike detection matrix data."));
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (error) {
    return <LoadingState error={error} onRetry={loadData} />;
  }

  if (!all) {
    return <LoadingState message="Loading look-alike identity matrix..." />;
  }

  const lookalikes = all.filter((d) =>
    d.evidence.some(
      (e) => e.signal_type === "LOOKALIKE_NAME" && e.details?.detected === true
    )
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-4 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--color-legitimate)] uppercase font-semibold">
            IDENTITY MATRIX · HOMOGLYPH & TYPOSQUATTING SPECIMENS
          </span>
        </div>
        <h1 className="font-serif text-3xl md:text-4xl font-normal text-[var(--text-primary)] mb-1">
          Look-alike Identity Transformations
        </h1>
        <p className="text-xs font-mono text-[var(--text-muted)]">
          Evaluated character substitutions (e.g. i → 1), added tokens, and spacing variations.
        </p>
      </div>

      {/* Lookalike Identity Matrix Grid */}
      {lookalikes.length > 0 ? (
        <LookalikeMatrix detections={lookalikes} />
      ) : (
        <div className="aegis-card p-12 text-center text-xs font-mono text-[var(--text-muted)]">
          No look-alike identity transformations detected in current candidate dataset.
        </div>
      )}
    </div>
  );
};

