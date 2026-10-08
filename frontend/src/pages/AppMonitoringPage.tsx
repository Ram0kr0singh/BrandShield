import React, { useCallback, useEffect, useState } from "react";
import { api, Detection } from "../api";
import { LoadingState } from "../components/common/LoadingState";
import { ThreatTable } from "../components/monitoring/ThreatTable";

export const AppMonitoringPage: React.FC = () => {
  const [all, setAll] = useState<Detection[] | null>(null);
  const [error, setError] = useState("");
  const [severity, setSeverity] = useState("ALL");
  const [status, setStatus] = useState("ALL");

  const loadData = useCallback(() => {
    setError("");
    api
      .detections()
      .then(setAll)
      .catch(() => setError("Unable to load app store candidate monitoring data."));
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (error) {
    return <LoadingState error={error} onRetry={loadData} />;
  }

  if (!all) {
    return <LoadingState message="Loading app store monitoring surface..." />;
  }

  let filtered = all.filter((d) => d.candidate.source === "App Store" || d.candidate.source === "App Stores");
  if (severity !== "ALL") {
    filtered = filtered.filter((d) => d.severity === severity);
  }
  if (status !== "ALL") {
    filtered = filtered.filter((d) => d.status === status);
  }

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-[var(--border-subtle)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--color-low)] uppercase font-semibold">
              APP STORE MONITORING SURFACE
            </span>
          </div>
          <h1 className="font-serif text-3xl md:text-4xl font-normal text-[var(--text-primary)]">
            App Store Candidates & Publisher Mismatches
          </h1>
          <p className="text-xs font-mono text-[var(--text-muted)] mt-1">
            Observed mobile application candidates, publisher mismatch signals, and package identifiers.
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="font-mono text-xs"
          >
            <option value="ALL">All Severities</option>
            <option value="HIGH">High / Critical</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
            <option value="SAFE">Safe / Official</option>
          </select>

          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="font-mono text-xs"
          >
            <option value="ALL">All Investigation States</option>
            <option value="NEW">New</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="CONFIRMED_THREAT">Confirmed Threat</option>
            <option value="FALSE_POSITIVE">False Positive</option>
            <option value="DISMISSED">Dismissed</option>
          </select>
        </div>
      </div>

      {/* Threat Table with Publisher Mismatch Column */}
      <ThreatTable detections={filtered} showPublisherMismatch={true} />
    </div>
  );
};

