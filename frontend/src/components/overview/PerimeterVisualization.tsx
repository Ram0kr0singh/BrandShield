import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Threat } from "../../api";
import { Badge } from "../common/Badge";

interface PerimeterVisualizationProps {
  brandName: string;
  threats: Threat[];
}

export const PerimeterVisualization: React.FC<PerimeterVisualizationProps> = ({
  brandName,
  threats,
}) => {
  const navigate = useNavigate();
  const [hoveredThreat, setHoveredThreat] = useState<Threat | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Canvas Dimensions
  const width = 720;
  const height = 400;
  const cx = width / 2;
  const cy = height / 2;

  // Concentric perimeter ring radii
  const rCritical = 75;
  const rSuspicious = 135;
  const rSafe = 185;

  // Separate social (left side) and app store (right side) threats
  const socialThreats = threats.filter((t) => t.source === "Social Media");
  const appThreats = threats.filter((t) => t.source === "App Store" || t.source === "App Stores");
  const otherThreats = threats.filter(
    (t) => t.source !== "Social Media" && t.source !== "App Store" && t.source !== "App Stores"
  );

  const calculateSpatialPosition = (threat: Threat, index: number, totalOnSide: number, side: "left" | "right" | "center") => {
    let radius = rSafe;
    let color = "var(--color-legitimate)";

    if (threat.severity === "CRITICAL" || threat.severity === "HIGH") {
      radius = rCritical;
      color = "var(--color-critical)";
    } else if (threat.severity === "MEDIUM" || threat.severity === "LOW") {
      radius = rSuspicious;
      color = "var(--color-suspicious)";
    } else {
      radius = rSafe;
      color = "var(--color-legitimate)";
    }

    // Angle distribution
    let angle = 0;
    const arcSpread = Math.PI * 0.75;

    if (side === "left") {
      const baseAngle = Math.PI; // 180 degrees (Left)
      angle =
        totalOnSide > 1
          ? baseAngle - arcSpread / 2 + (index / (totalOnSide - 1)) * arcSpread
          : baseAngle;
    } else if (side === "right") {
      const baseAngle = 0; // 0 degrees (Right)
      angle =
        totalOnSide > 1
          ? baseAngle - arcSpread / 2 + (index / (totalOnSide - 1)) * arcSpread
          : baseAngle;
    } else {
      angle = -Math.PI / 2 + (index / (Math.max(1, totalOnSide))) * Math.PI;
    }

    const x = cx + radius * Math.cos(angle);
    const y = cy + radius * Math.sin(angle);

    return { threat, x, y, color, radius };
  };

  const socialPoints = socialThreats.map((t, idx) =>
    calculateSpatialPosition(t, idx, socialThreats.length, "left")
  );
  const appPoints = appThreats.map((t, idx) =>
    calculateSpatialPosition(t, idx, appThreats.length, "right")
  );
  const otherPoints = otherThreats.map((t, idx) =>
    calculateSpatialPosition(t, idx, otherThreats.length, "center")
  );

  const allPoints = [...socialPoints, ...appPoints, ...otherPoints];

  return (
    <div className="aegis-card relative overflow-hidden flex flex-col items-center justify-center p-8 mb-8">
      {/* Header Info */}
      <div className="flex items-center justify-between w-full mb-4 pb-3 border-b border-[var(--border-subtle)]">
        <div>
          <span className="font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)] uppercase font-semibold">
            THE DIGITAL PERIMETER · ORBITAL OBSERVATORY
          </span>
          <p className="text-xs text-[var(--text-secondary)] font-mono mt-0.5">
            Core: {brandName} · Left: Social Candidates · Right: Application Candidates
          </p>
        </div>

        <div className="flex items-center gap-4 font-mono text-[10px] text-[var(--text-muted)]">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-legitimate)]" />
            LEGITIMATE CORE
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-suspicious)]" />
            SUSPICIOUS HORIZON
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-critical)]" />
            CRITICAL VECTOR
          </span>
        </div>
      </div>

      {/* SVG Observatory Surface */}
      <div className="relative w-full flex justify-center py-2">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full max-w-[720px] h-auto overflow-visible select-none"
        >
          <defs>
            <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#86b8a4" stopOpacity="0.2" />
              <stop offset="60%" stopColor="#86b8a4" stopOpacity="0.05" />
              <stop offset="100%" stopColor="#86b8a4" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="critGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#e4574a" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#e4574a" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Background Vector Horizon Line */}
          <line
            x1={40}
            y1={cy}
            x2={width - 40}
            y2={cy}
            stroke="var(--border-subtle)"
            strokeDasharray="2 6"
            strokeWidth="1"
          />

          {/* Concentric Perimeter Rings */}
          <g className="orbit-spin">
            <circle
              cx={cx}
              cy={cy}
              r={rSafe}
              fill="none"
              stroke="var(--border-subtle)"
              strokeDasharray="3 7"
              strokeWidth="1"
            />
            <circle
              cx={cx}
              cy={cy}
              r={rSuspicious}
              fill="none"
              stroke="rgba(217, 174, 95, 0.15)"
              strokeDasharray="4 4"
              strokeWidth="1"
            />
            <circle
              cx={cx}
              cy={cy}
              r={rCritical}
              fill="none"
              stroke="rgba(228, 87, 74, 0.25)"
              strokeWidth="1.2"
            />
          </g>

          {/* Core Brand Glow & Node */}
          <circle cx={cx} cy={cy} r={54} fill="url(#coreGlow)" />
          <circle cx={cx} cy={cy} r={rCritical} fill="url(#critGlow)" />

          <circle
            cx={cx}
            cy={cy}
            r={28}
            fill="var(--bg-elevated)"
            stroke="var(--color-legitimate-border)"
            strokeWidth="1.5"
            className="shadow-lg"
          />

          <text
            x={cx}
            y={cy + 4}
            textAnchor="middle"
            fill="var(--text-primary)"
            fontSize="12"
            fontWeight="bold"
            fontFamily="var(--font-serif)"
            letterSpacing="0.05em"
          >
            {brandName.substring(0, 6).toUpperCase()}
          </text>

          {/* Orbital Perimeter Axis Labels */}
          <text
            x={cx - rSafe - 10}
            y={cy - 8}
            textAnchor="end"
            fill="var(--text-faint)"
            fontSize="9"
            fontFamily="var(--font-mono)"
            letterSpacing="0.1em"
          >
            SOCIAL ORBIT
          </text>
          <text
            x={cx + rSafe + 10}
            y={cy - 8}
            textAnchor="start"
            fill="var(--text-faint)"
            fontSize="9"
            fontFamily="var(--font-mono)"
            letterSpacing="0.1em"
          >
            APPLICATION ORBIT
          </text>

          {/* Threat Entity Nodes */}
          {allPoints.map(({ threat, x, y, color }) => {
            const isHovered = hoveredThreat?.id === threat.id;
            const isCritical = threat.severity === "HIGH" || threat.severity === "CRITICAL";

            return (
              <g
                key={threat.id}
                className="cursor-pointer transition-transform duration-200"
                onClick={() => navigate(`/threats/${threat.id}`)}
                onMouseEnter={(e) => {
                  setHoveredThreat(threat);
                  setTooltipPos({ x: e.clientX, y: e.clientY });
                }}
                onMouseLeave={() => setHoveredThreat(null)}
              >
                {/* Threat Proximity Line connecting to Core */}
                <line
                  x1={cx}
                  y1={cy}
                  x2={x}
                  y2={y}
                  stroke={color}
                  strokeOpacity={isHovered ? 0.4 : 0.1}
                  strokeWidth={isHovered ? 1.5 : 1}
                  strokeDasharray={isCritical ? "2 2" : "none"}
                />

                {/* Pulse ring for high/critical threat nodes */}
                {isCritical && (
                  <circle
                    cx={x}
                    cy={y}
                    r={isHovered ? 16 : 11}
                    fill="none"
                    stroke="var(--color-critical)"
                    strokeOpacity="0.4"
                    className="pulse-critical"
                  />
                )}

                {/* Outer halo & dot */}
                <circle
                  cx={x}
                  cy={y}
                  r={isHovered ? 9 : 6}
                  fill={color}
                  fillOpacity={isHovered ? 1 : 0.85}
                  stroke="var(--bg-canvas)"
                  strokeWidth="2"
                />

                {/* Monospace candidate tag on hover */}
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
                    {threat.name}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip Card */}
        {hoveredThreat && (
          <div
            className="fixed z-50 aegis-card-raised p-3 shadow-2xl pointer-events-none max-w-xs border border-[var(--border-strong)]"
            style={{
              left: tooltipPos.x + 14,
              top: tooltipPos.y - 45,
            }}
          >
            <div className="flex items-center justify-between gap-3 mb-1.5">
              <span className="font-serif text-sm font-semibold text-[var(--text-primary)] truncate">
                {hoveredThreat.name}
              </span>
              <Badge value={hoveredThreat.severity} />
            </div>
            <div className="text-xs text-[var(--text-muted)] font-mono space-y-0.5">
              <p>Source: {hoveredThreat.source}</p>
              <p>Risk Score: {hoveredThreat.risk_score.toFixed(2)}</p>
              {hoveredThreat.publisher && <p>Publisher: {hoveredThreat.publisher}</p>}
            </div>
          </div>
        )}
      </div>

      {/* Honest Perimeter Telemetry Summary */}
      <div className="w-full pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between font-mono text-[11px] text-[var(--text-muted)]">
        <span>MONITORING ACTIVE · {threats.length} CANDIDATES EVALUATED</span>
        <span>DETERMINISTIC PERIMETER RADIAL PROXIMITY</span>
      </div>
    </div>
  );
};

