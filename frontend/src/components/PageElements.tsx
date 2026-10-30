import type { Alert, Metric } from "../api/schema";
import { MetricCard } from "./MetricCard";
import { EmptyState } from "./QueryState";

export function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <header className="page-header">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      <p>{description}</p>
    </header>
  );
}

export function MetricGrid({ metrics }: { metrics: Metric[] }) {
  if (!metrics.length) return <EmptyState>No metrics reported.</EmptyState>;
  return (
    <div className="metric-grid">
      {metrics.map((metric) => (
        <MetricCard key={metric.id} {...metric} />
      ))}
    </div>
  );
}

export function AlertList({ alerts }: { alerts: Alert[] }) {
  if (!alerts.length) return <EmptyState>No active alerts.</EmptyState>;
  return (
    <ul className="alert-list">
      {alerts.map((alert) => (
        <li key={alert.id} className={`alert-${alert.severity ?? "info"}`}>
          <span aria-hidden="true" />
          <div>
            <strong>{alert.title}</strong>
            {alert.detail && <p>{alert.detail}</p>}
            {alert.updated_at && (
              <time dateTime={alert.updated_at}>
                {new Date(alert.updated_at).toLocaleString()}
              </time>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
