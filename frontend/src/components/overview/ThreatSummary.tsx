import React from "react";
import { Overview } from "../../api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from "recharts";

interface ThreatSummaryProps {
  overview: Overview;
}

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "var(--color-critical)",
  HIGH: "var(--color-critical)",
  MEDIUM: "var(--color-suspicious)",
  LOW: "var(--color-low)",
  SAFE: "var(--color-legitimate)",
};

export const ThreatSummary: React.FC<ThreatSummaryProps> = ({ overview }) => {
  const { risk_distribution, threat_type_distribution } = overview;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      {/* Risk Severity Breakdown */}
      <div className="aegis-card flex flex-col justify-between">
        <span className="font-mono text-[11px] tracking-widest text-[var(--text-muted)] uppercase font-semibold mb-4">
          RISK SEVERITY DISTRIBUTION
        </span>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={risk_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="severity" tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fill: "var(--text-muted)", fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--bg-raised)",
                  borderColor: "var(--border-default)",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "var(--text-primary)",
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {risk_distribution.map((entry) => (
                  <Cell key={entry.severity} fill={SEVERITY_COLORS[entry.severity] || "var(--color-low)"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Threat Types Breakdown */}
      <div className="aegis-card flex flex-col justify-between">
        <span className="font-mono text-[11px] tracking-widest text-[var(--text-muted)] uppercase font-semibold mb-4">
          THREAT TYPE CLASSIFICATION
        </span>
        {threat_type_distribution.length > 0 ? (
          <div className="h-56 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={threat_type_distribution}
                  dataKey="count"
                  nameKey="threat_type"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={45}
                  paddingAngle={4}
                >
                  {threat_type_distribution.map((entry, index) => {
                    const colors = ["#e4574a", "#d9ae5f", "#9d8ec7", "#648ba6"];
                    return <Cell key={entry.threat_type} fill={colors[index % colors.length]} />;
                  })}
                </Pie>
                <Tooltip
                  formatter={(val, name) => [val, String(name).replaceAll("_", " ")]}
                  contentStyle={{
                    backgroundColor: "var(--bg-raised)",
                    borderColor: "var(--border-default)",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "var(--text-primary)",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-56 flex items-center justify-center text-xs font-mono text-[var(--text-muted)]">
            No active threat classifications recorded.
          </div>
        )}
      </div>
    </div>
  );
};
