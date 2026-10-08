import React from "react";

interface EmptyStateProps {
  title?: string;
  message?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = "No data recorded",
  message = "No matching records were found for this query.",
}) => {
  return (
    <div className="aegis-card p-12 text-center flex flex-col items-center justify-center">
      <p className="font-mono text-xs text-[var(--text-muted)] tracking-wider uppercase mb-1">
        {title}
      </p>
      <p className="text-sm text-[var(--text-secondary)] max-w-md">
        {message}
      </p>
    </div>
  );
};
