import type { ReactNode } from "react";
import type { ApiMeta } from "../api/schema";

/** Props for loading, error, stale-data, and successful query states. */
interface QueryStateProps {
  loading: boolean;
  error: Error | null;
  fetching?: boolean;
  meta?: ApiMeta;
  onRetry?: () => void;
  children: ReactNode;
}

/** Renders query status feedback around loaded child content. */
export function QueryState({
  loading,
  error,
  fetching,
  meta,
  onRetry,
  children,
}: QueryStateProps) {
  if (loading) {
    return (
      <div className="state-card" role="status">
        <span className="spinner" aria-hidden="true" />
        <strong>Loading live data</strong>
        <span>Contacting the dashboard service…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="state-card state-error" role="alert">
        <strong>Data is temporarily unavailable</strong>
        <span>{error.message}</span>
        {onRetry && (
          <button type="button" className="button-secondary" onClick={onRetry}>
            Try again
          </button>
        )}
      </div>
    );
  }

  return (
    <>
      {(meta?.stale || fetching) && (
        <div className="freshness-note" role="status">
          {meta?.stale
            ? "Showing the latest cached data while the source recovers."
            : "Refreshing data in the background…"}
        </div>
      )}
      {children}
    </>
  );
}

/** Renders a compact message when a panel has no records. */
export function EmptyState({ children }: { children: ReactNode }) {
  return <p className="empty-state">{children}</p>;
}
