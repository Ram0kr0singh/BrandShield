import React from "react";
import { Link, useLocation } from "react-router-dom";
import { StatusIndicator } from "../common/StatusIndicator";

export const AppSidebar: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { label: "Overview", path: "/" },
    { label: "Protected Identity", path: "/profile" },
    { label: "Social Monitoring", path: "/social" },
    { label: "App Monitoring", path: "/apps" },
    { label: "Look-alike Detection", path: "/lookalikes" },
    { label: "Check Any Name", path: "/check" },
    { label: "Threat Surface", path: "/threats" },
  ];

  return (
    <aside className="aegis-spine">
      <div>
        {/* Brand Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-sm bg-[var(--color-legitimate)] inline-block shadow-[0_0_8px_rgba(134,184,164,0.5)]" />
            <span className="font-serif text-2xl tracking-wide text-[var(--text-primary)] font-normal">
              AEGIS
            </span>
          </div>
          <p className="font-mono text-[9px] tracking-[0.2em] text-[var(--text-muted)] uppercase mt-1">
            BRANDSHIELD · PERIMETER
          </p>
        </div>

        {/* THE SPINE Navigation Rail */}
        <div className="spine-rail">
          {/* Vertical hairline thread */}
          <div className="spine-line" />

          {navItems.map((item) => {
            const isActive =
              item.path === "/"
                ? location.pathname === "/"
                : location.pathname.startsWith(item.path);

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`spine-item ${isActive ? "active" : ""}`}
              >
                <div className="spine-node">
                  <div className="spine-node-dot" />
                </div>
                <span className="font-sans text-[13px] tracking-wide">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </div>

      <div className="mt-auto pt-6 border-t border-[var(--border-subtle)]">
        <StatusIndicator label="PERIMETER ACTIVE" active={true} />
      </div>
    </aside>
  );
};

