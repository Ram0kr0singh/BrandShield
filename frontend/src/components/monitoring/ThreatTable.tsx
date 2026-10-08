import React from "react";
import { useNavigate } from "react-router-dom";
import { Detection } from "../../api";
import { Badge } from "../common/Badge";
import { PlatformIcon } from "./PlatformIcon";

interface ThreatTableProps {
  detections: Detection[];
  showPublisherMismatch?: boolean;
}

export const ThreatTable: React.FC<ThreatTableProps> = ({
  detections,
  showPublisherMismatch = false,
}) => {
  const navigate = useNavigate();

  return (
    <div className="aegis-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="aegis-table">
          <thead>
            <tr>
              <th>Observed Candidate</th>
              <th>Source Channel</th>
              {showPublisherMismatch && <th>Publisher Mismatch</th>}
              <th>Classification</th>
              <th>Risk Score</th>
              <th>Severity</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {detections.map((d) => {
              const isOfficial = d.official_match === true;
              const publisherEvidence = d.evidence?.find(
                (e) => e.signal_type === "PUBLISHER_MISMATCH"
              );
              const hasMismatch =
                publisherEvidence?.available &&
                publisherEvidence?.details?.result === "MISMATCH";

              return (
                <tr
                  key={d.id}
                  onClick={() => navigate(`/threats/${d.id}`)}
                  className={isOfficial ? "bg-[var(--color-legitimate-bg)]" : ""}
                >
                  <td>
                    <div className="flex items-center gap-2">
                      <PlatformIcon platform={d.candidate.source} />
                      <div>
                        <p className="font-semibold text-[var(--text-primary)]">
                          {d.candidate.name}
                        </p>
                        {d.candidate.handle && (
                          <p className="font-mono text-xs text-[var(--text-muted)]">
                            @{d.candidate.handle}
                          </p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="font-mono text-xs text-[var(--text-secondary)]">
                    {d.candidate.source}
                  </td>
                  {showPublisherMismatch && (
                    <td>
                      {hasMismatch ? (
                        <span className="badge high">
                          MISMATCH: {d.candidate.publisher || "Unknown"}
                        </span>
                      ) : isOfficial ? (
                        <span className="badge safe">AUTHORIZED PUBLISHER</span>
                      ) : (
                        <span className="font-mono text-xs text-[var(--text-muted)]">
                          {d.candidate.publisher || "—"}
                        </span>
                      )}
                    </td>
                  )}
                  <td className="font-mono text-xs text-[var(--text-muted)]">
                    {d.threat_type ? d.threat_type.replaceAll("_", " ") : "UNCATEGORIZED"}
                  </td>
                  <td className="font-serif font-bold text-lg text-[var(--text-primary)]">
                    {d.risk_score.toFixed(2)}
                  </td>
                  <td>
                    {isOfficial ? (
                      <Badge value="SAFE" />
                    ) : (
                      <Badge value={d.severity} />
                    )}
                  </td>
                  <td>
                    {isOfficial ? (
                      <Badge value="LEGITIMATE" />
                    ) : (
                      <Badge value={d.status} />
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
