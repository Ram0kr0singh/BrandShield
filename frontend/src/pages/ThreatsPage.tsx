import React, { useCallback, useEffect, useState } from "react";
import { api, Detection } from "../api";
import { LoadingState } from "../components/common/LoadingState";
import { SpatialThreatSurface } from "../components/threats/SpatialThreatSurface";
import { ThreatTable } from "../components/monitoring/ThreatTable";

export const ThreatsPage: React.FC = () => {
  const [all, setAll] = useState<Detection[] | null>(null);
  const [error, setError] = useState("");
  const [severity, setSeverity] = useState("ALL");
  const [source, setSource] = useState("ALL");
  const [status, setStatus] = useState("ALL");

  const loadData = useCallback(() => {
    setError("");
    api
      .detections()
      .then(setAll)
      .catch(() => setError("Unable to load threat surface detections dataset."));
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (error) {
    return <LoadingState error={error} onRetry={loadData} />;
  }

  if (!all) {
    return <LoadingState message="Loading master threat surface intelligence..." />;
  }

  let filtered = all;
  if (severity !== "ALL") {
    filtered = filtered.filter((d) => d.severity === severity);
  }
  if (source !== "ALL") {
    filtered = filtered.filter((d) => d.candidate.source === source);
  }
  if (status !== "ALL") {
    filtered = filtered.filter((d) => d.status === status);
  }

  return (
    <div className="space-y-6">
      {/* Header & Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-[var(--border-subtle)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--color-critical)] uppercase font-semibold">
              MASTER THREAT INTELLIGENCE SURFACE
            </span>
          </div>
          <h1 className="font-serif text-3xl md:text-4xl font-normal text-[var(--text-primary)]">
            Digital Threat Surface & Candidate Population
          </h1>
          <p className="text-xs font-mono text-[var(--text-muted)] mt-1">
            Spatial distribution map and master ledger of evaluated digital perimeter candidates.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 font-mono text-xs">
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
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="font-mono text-xs"
          >
            <option value="ALL">All Channels</option>
            <option value="Social Media">Social Media</option>
            <option value="App Store">App Store</option>
          </select>

          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="font-mono text-xs"
          >
            <option value="ALL">All States</option>
            <option value="NEW">New</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="CONFIRMED_THREAT">Confirmed Threat</option>
            <option value="FALSE_POSITIVE">False Positive</option>
            <option value="DISMISSED">Dismissed</option>
          </select>
        </div>
      </div>

      {/* Spatial Threat Surface Canvas Map */}
      <SpatialThreatSurface detections={filtered} />

      {/* Filtered Master Threat Table */}
      <ThreatTable detections={filtered} showPublisherMismatch={true} />
    </div>
  );
};

