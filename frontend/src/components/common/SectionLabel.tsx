import React from "react";

interface SectionLabelProps {
  children: React.ReactNode;
  action?: React.ReactNode;
}

export const SectionLabel: React.FC<SectionLabelProps> = ({ children, action }) => {
  return (
    <div className="flex items-center justify-between mb-3">
      <span className="font-mono text-[11px] tracking-widest text-[var(--text-muted)] uppercase font-semibold">
        {children}
      </span>
      {action && <div>{action}</div>}
    </div>
  );
};
