import React from "react";
import { RefreshCw } from "lucide-react";

interface LoadingStateProps {
  message?: string;
  error?: string;
  onRetry?: () => void;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading digital perimeter data...",
  error,
  onRetry,
}) => {
  if (error) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center p-8 text-center">
        <p className="font-mono text-xs text-[var(--color-critical)] uppercase tracking-wider mb-2">
          INTELLIGENCE FETCH ERROR
        </p>
        <p className="text-sm text-[var(--text-secondary)] mb-4 max-w-md">
          {error}
        </p>
        {onRetry && (
          <button className="btn" onClick={onRetry}>
            <RefreshCw size={14} /> Retry Request
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="min-h-[50vh] flex flex-col items-center justify-center p-8 text-center">
      <RefreshCw size={24} className="spin text-[var(--text-muted)] mb-3" />
      <span className="font-mono text-xs tracking-wider text-[var(--text-muted)] uppercase">
        {message}
      </span>
    </div>
  );
};
