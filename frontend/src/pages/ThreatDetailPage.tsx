import React, { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  api,
  AnalystAnalysis,
  Detection,
  Investigation,
} from "../api";
import { LoadingState } from "../components/common/LoadingState";
import { ThreatHeader } from "../components/investigation/ThreatHeader";
import { OfficialVsSuspect } from "../components/investigation/OfficialVsSuspect";
import { ThreatDNA } from "../components/investigation/ThreatDNA";
import { AIAnalystPanel } from "../components/investigation/AIAnalystPanel";
import { RemediationDraftViewer } from "../components/investigation/RemediationDraftViewer";
import { ActivityTimeline } from "../components/investigation/ActivityTimeline";

export const ThreatDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [detection, setDetection] = useState<Detection | null>(null);
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [analysis, setAnalysis] = useState<AnalystAnalysis | null>(null);

  const [busy, setBusy] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");

  const loadDetails = useCallback(() => {
    if (!id) return;
    setError("");
    Promise.all([api.detection(id), api.investigation(id)])
      .then(([det, inv]) => {
        setDetection(det);
        setInvestigation(inv);
      })
      .catch(() =>
        setError(
          "Unable to load threat specimen investigation data from backend."
        )
      );
  }, [id]);

  useEffect(() => {
    loadDetails();
  }, [loadDetails]);

  const handleStatusChange = async (newStatus: string) => {
    if (!id) return;
    setBusy(true);
    setError("");
    try {
      const updated = await api.status(id, newStatus);
      setInvestigation(updated);
      loadDetails();
    } catch {
      setError("Failed to update investigation state.");
    } finally {
      setBusy(false);
    }
  };

  const handleAddNote = async (content: string) => {
    if (!id) return;
    setBusy(true);
    setError("");
    try {
      const updated = await api.note(id, content);
      setInvestigation(updated);
      loadDetails();
    } catch {
      setError("Failed to record analyst note.");
    } finally {
      setBusy(false);
    }
  };

  const handleGenerateDraft = async (draftType: string) => {
    if (!id) return;
    setBusy(true);
    setError("");
    try {
      await api.draft(id, draftType);
      const updatedInv = await api.investigation(id);
      setInvestigation(updatedInv);
    } catch {
      setError("Failed to generate remediation draft template.");
    } finally {
      setBusy(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!id) return;
    setAnalyzing(true);
    setError("");
    try {
      const res = await api.analyze(id);
      setAnalysis(res);
    } catch {
      setError("AI Analyst failed to generate explanatory analysis.");
    } finally {
      setAnalyzing(false);
    }
  };

  if (error) {
    return <LoadingState error={error} onRetry={loadDetails} />;
  }

  if (!detection || !investigation) {
    return <LoadingState message="Loading threat specimen forensic investigation..." />;
  }

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <ThreatHeader
        detection={detection}
        investigation={investigation}
        onStatusChange={handleStatusChange}
        busy={busy}
      />

      {/* Official vs Suspect Specimen Comparative View */}
      <OfficialVsSuspect detection={detection} />

      {/* Threat DNA Visual Evidence Breakdown */}
      <ThreatDNA evidence={detection.evidence} />

      {/* AI Analyst Explanatory Intelligence Panel */}
      <AIAnalystPanel
        analysis={analysis}
        analyzing={analyzing}
        onRunAnalysis={handleRunAnalysis}
      />

      {/* Remediation Draft Viewer */}
      <RemediationDraftViewer
        drafts={investigation.drafts}
        onGenerateDraft={handleGenerateDraft}
        busy={busy}
        source={detection.candidate.source}
      />

      {/* Activity Audit Trail & Analyst Notes */}
      <ActivityTimeline
        activity={investigation.activity}
        notes={investigation.notes}
        onAddNote={handleAddNote}
        busy={busy}
      />
    </div>
  );
};
