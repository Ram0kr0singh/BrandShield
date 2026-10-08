import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Detection } from "../../api";
import { Badge } from "../common/Badge";

interface SpatialThreatSurfaceProps {
  detections: Detection[];
}

export const SpatialThreatSurface: React.FC<SpatialThreatSurfaceProps> = ({ detections }) => {
  const navigate = useNavigate();
  const [hovered, setHovered] = useState<Detection | null>(null);
  const [pos, setPos] = useState({ x: 0, y: 0 });

  const width = 800;
  const height = 440;
  const cx = width / 2;
  const cy = height / 2;

  // Split social (left) and app (right)
  const socialDetections = detections.filter((d) => d.candidate.source === "Social Media");
  const appDetections = detections.filter((d) => d.candidate.source === "App Store" || d.candidate.source === "App Stores");
  const otherDetections = detections.filter(
    (d) => d.candidate.source !== "Social Media" && d.candidate.source !== "App Store" && d.candidate.source !== "App Stores"
  );

  const calcPoints = (list: Detection[], side: "left" | "right" | "center") => {
    return list.map((d, idx) => {
      const isHigh = d.severity === "CRITICAL" || d.severity === "HIGH";
      const isMedium = d.severity === "MEDIUM" || d.severity === "LOW";

      // Radial distance: High risk closer to center core
      let r = 240;
      if (isHigh) r = 100;
      else if (isMedium) r = 170;

      const count = list.length;
      const angleSpread = Math.PI * 0.75;
      let baseAngle = 0;

      if (side === "left") baseAngle = Math.PI;
      else if (side === "right") baseAngle = 0;

      const angle =
        count > 1
          ? baseAngle - angleSpread / 2 + (idx / (count - 1)) * angleSpread
          : baseAngle;

      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);

      let color = "var(--color-legitimate)";
      if (isHigh) color = "var(--color-critical)";
      else if (isMedium) color = "var(--color-suspicious)";

      return { d, x, y, color, radius: r };
    });
  };

  const leftPoints = calcPoints(socialDetections, "left");
  const rightPoints = calcPoints(appDetections, "right");
  const otherPoints = calcPoints(otherDetections, "center");
  const allPoints = [...leftPoints, ...rightPoints, ...otherPoints];

  return (
    <div className="aegis-card relative overflow-hidden flex flex-col items-center justify-center p-8 mb-8">
      {/* Header telemetry */}
      <div className="flex items-center justify-between w-full mb-4 pb-3 border-b border-[var(--border-subtle)]">
        <div>
          <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)] uppercase font-semibold">
            SPATIAL THREAT RELATIONSHIP SURFACE
          </span>
          <p className="text-xs text-[var(--text-secondary)] font-mono mt-0.5">
            Left Hemisphere: Social Media Candidates · Center: Protected Core Baseline · Right Hemisphere: App Store Candidates
          </p>
        </div>
        <div className="font-mono text-xs text-[var(--text-muted)]">
          {detections.length} ACTIVE SPECIMENS
        </div>
      </div>

      {/* Surface Canvas Map */}
      <div className="relative w-full flex justify-center py-2 select-none">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full max-w-[800px] h-auto overflow-visible"
        >
          {/* Radial Concentric Bounds & Radar Ticks */}
          <circle cx={cx} cy={cy} r={100} fill="none" stroke="rgba(228, 87, 74, 0.2)" strokeDasharray="3 3" />
          <circle cx={cx} cy={cy} r={170} fill="none" stroke="var(--border-subtle)" strokeDasharray="4 4" />
          <circle cx={cx} cy={cy} r={240} fill="none" stroke="var(--border-subtle)" strokeDasharray="5 5" />

          {/* Central Baseline Divider */}
          <line x1={cx} y1={30} x2={cx} y2={height - 30} stroke="var(--border-subtle)" strokeWidth="1" strokeDasharray="4 4" />

          {/* Core Target Node */}
          <circle cx={cx} cy={cy} r={32} fill="var(--bg-elevated)" stroke="var(--color-legitimate)" strokeWidth="1.5" />
          <text
            x={cx}
            y={cy + 4}
            textAnchor="middle"
            fill="var(--text-primary)"
            fontSize="10"
            fontWeight="bold"
            fontFamily="var(--font-mono)"
            letterSpacing="0.1em"
          >
            PROTECTED
          </text>

          {/* Axis Labels */}
          <text x={cx - 180} y={35} textAnchor="end" fill="var(--text-faint)" fontSize="9" fontFamily="var(--font-mono)" letterSpacing="0.1em">
            SOCIAL VECTOR [HEMISPHERE L]
          </text>
          <text x={cx + 180} y={35} textAnchor="start" fill="var(--text-faint)" fontSize="9" fontFamily="var(--font-mono)" letterSpacing="0.1em">
            APP STORE VECTOR [HEMISPHERE R]
          </text>

          {/* Threat Points & Vector Lines */}
          {allPoints.map(({ d, x, y, color }) => {
            const isHovered = hovered?.id === d.id;
            const isHigh = d.severity === "CRITICAL" || d.severity === "HIGH";

            return (
              <g
                key={d.id}
                className="cursor-pointer"
                onClick={() => navigate(`/threats/${d.id}`)}
                onMouseEnter={(e) => {
                  setHovered(d);
                  setPos({ x: e.clientX, y: e.clientY });
                }}
                onMouseLeave={() => setHovered(null)}
              >
                <line
                  x1={cx}
                  y1={cy}
                  x2={x}
                  y2={y}
                  stroke={color}
                  strokeOpacity={isHovered ? 0.4 : 0.1}
                  strokeWidth={isHovered ? 1.5 : 1}
                />

                {isHigh && (
                  <circle
                    cx={x}
                    cy={y}
                    r={isHovered ? 15 : 11}
                    fill="none"
                    stroke="var(--color-critical)"
                    strokeOpacity="0.4"
                    className="pulse-critical"
                  />
                )}
                <circle
                  cx={x}
                  cy={y}
                  r={isHovered ? 8 : 5}
                  fill={color}
                  stroke="var(--bg-canvas)"
                  strokeWidth="2"
                />

                {isHovered && (
                  <text
                    x={x}
                    y={y - 12}
                    textAnchor="middle"
                    fill="var(--text-primary)"
                    fontSize="10"
                    fontFamily="var(--font-mono)"
                    fontWeight="600"
                  >
                    {d.candidate.name}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip */}
        {hovered && (
          <div
            className="fixed z-50 aegis-card-raised p-3 shadow-2xl pointer-events-none max-w-xs border border-[var(--border-strong)]"
            style={{ left: pos.x + 14, top: pos.y - 45 }}
          >
            <div className="flex items-center justify-between gap-3 mb-1">
              <span className="font-serif text-sm font-semibold text-[var(--text-primary)] truncate">
                {hovered.candidate.name}
              </span>
              <Badge value={hovered.severity} />
            </div>
            <div className="text-xs text-[var(--text-muted)] font-mono space-y-0.5">
              <p>Channel: {hovered.candidate.source}</p>
              <p>Risk Score: {hovered.risk_score.toFixed(2)}</p>
              {hovered.candidate.publisher && <p>Publisher: {hovered.candidate.publisher}</p>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

