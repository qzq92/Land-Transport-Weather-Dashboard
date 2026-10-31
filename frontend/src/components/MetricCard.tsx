import type { Metric } from "../api/schema";

/** Props for a metric card, including its stable DOM identifier. */
export interface MetricCardProps extends Metric {
  description?: string;
}

/** Renders one metric value with optional trend and status styling. */
export function MetricCard({
  label,
  value,
  unit,
  trend,
  status = "neutral",
  description,
}: MetricCardProps) {
  const trendLabel =
    trend === undefined
      ? undefined
      : `${trend > 0 ? "Up" : trend < 0 ? "Down" : "Unchanged"} ${Math.abs(trend)}%`;

  return (
    <article className={`metric-card metric-${status}`}>
      <p className="metric-label">{label}</p>
      <p className="metric-value">
        {value}
        {unit && <span>{unit}</span>}
      </p>
      {(trendLabel || description) && (
        <p className="metric-detail">
          {trendLabel && (
            <span
              className={trend && trend > 0 ? "trend-up" : "trend-down"}
              aria-label={trendLabel}
            >
              {trend && trend > 0 ? "↑" : trend && trend < 0 ? "↓" : "—"}{" "}
              {Math.abs(trend ?? 0)}%
            </span>
          )}
          {description}
        </p>
      )}
    </article>
  );
}
