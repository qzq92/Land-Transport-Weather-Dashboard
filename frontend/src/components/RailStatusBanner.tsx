import type { RailStatus } from "../api/schema";

const RAIL_LINES = [
  ["BPL", "Bukit Panjang LRT", "#748477"],
  ["CCL", "Circle Line", "#f99d1c"],
  ["DTL", "Downtown Line", "#0055b8"],
  ["EWL", "East-West Line", "#009645"],
  ["NEL", "North East Line", "#9900aa"],
  ["NSL", "North-South Line", "#d42e12"],
  ["PLRT", "Punggol LRT", "#748477"],
  ["SLRT", "Sengkang LRT", "#748477"],
  ["TEL", "Thomson-East Coast Line", "#9d5b25"],
] as const;

/** Props for the aggregate rail-status banner. */
interface RailStatusBannerProps {
  status: RailStatus;
}

/** Renders rail status and the affected-line summary when available. */
export function RailStatusBanner({ status }: RailStatusBannerProps) {
  const updatedAt = status.updated_at
    ? new Date(status.updated_at).toLocaleString()
    : undefined;

  return (
    <section
      className={`rail-status-banner rail-status-${status.state}`}
      aria-label="Rail service status"
    >
      <div>
        <strong>Rail service</strong>
        <span>{status.summary}</span>
      </div>
      <div className="rail-status-actions">
        {updatedAt && <time dateTime={status.updated_at}>Updated {updatedAt}</time>}
        <details>
          <summary>View all lines</summary>
          <ul>
            {RAIL_LINES.map(([code, name, colour]) => (
              <li key={code}>
                <span>
                  <i
                    className="rail-line-colour"
                    style={{ backgroundColor: colour }}
                    aria-hidden="true"
                  />
                  {name} ({code})
                </span>
                <b className={status.state === "normal" ? "is-normal" : ""}>
                  {status.state === "normal" ? "Operational" : "Check status"}
                </b>
              </li>
            ))}
          </ul>
        </details>
      </div>
    </section>
  );
}
