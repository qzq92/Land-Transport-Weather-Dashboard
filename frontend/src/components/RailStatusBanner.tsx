import type { RailStatus } from "../api/schema";

const RAIL_LINES = [
  ["BPL", "Bukit Panjang LRT"],
  ["CCL", "Circle Line"],
  ["DTL", "Downtown Line"],
  ["EWL", "East-West Line"],
  ["NEL", "North East Line"],
  ["NSL", "North-South Line"],
  ["PLRT", "Punggol LRT"],
  ["SLRT", "Sengkang LRT"],
  ["TEL", "Thomson-East Coast Line"],
] as const;

interface RailStatusBannerProps {
  status: RailStatus;
}

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
            {RAIL_LINES.map(([code, name]) => (
              <li key={code}>
                <span>{name} ({code})</span>
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
