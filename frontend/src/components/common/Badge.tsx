import React from "react";

interface BadgeProps {
  value: string;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ value, className = "" }) => {
  const norm = value.toLowerCase().replace(/[\s-]/g, "_");
  return (
    <span className={`badge ${norm} ${className}`}>
      {value.replaceAll("_", " ")}
    </span>
  );
};
