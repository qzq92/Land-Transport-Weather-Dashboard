import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useRailStatus } from "../api/queries";
import type { RailStatus } from "../api/schema";
import { RailStatusBanner } from "./RailStatusBanner";

const navigation = [
  { to: "/", label: "Main Dashboard", end: true },
  { to: "/weather/realtime", label: "Weather Metrics" },
  { to: "/environment", label: "Daily Health & Environment" },
  { to: "/healthcare", label: "Healthcare Wait Times" },
  { to: "/transport", label: "Road & Transport" },
  { to: "/transit/crowding", label: "Transit" },
  { to: "/nearby", label: "Nearby Facilities" },
] as const;

const UNAVAILABLE_RAIL_STATUS: RailStatus = {
  state: "unknown",
  summary: "Rail service status is unavailable",
};

/** Renders the application shell, navigation, and rail-status banner. */
export function Layout() {
  const location = useLocation();
  const rail = useRailStatus();
  const railStatus = rail.data?.data ?? {
    ...UNAVAILABLE_RAIL_STATUS,
    summary: rail.isPending
      ? "Checking rail services…"
      : UNAVAILABLE_RAIL_STATUS.summary,
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink className="brand" to="/" aria-label="Dashboard home">
          <span className="brand-mark" aria-hidden="true">SG</span>
          <span>
            <strong>Land Transport, Weather and Healthcare Dashboard</strong>
            <small>Singapore near real-time public services</small>
          </span>
        </NavLink>
        <span className="live-indicator">
          <span aria-hidden="true" /> Live data
        </span>
      </header>

      <nav className="primary-nav" aria-label="Dashboard sections">
        {navigation.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={"end" in item ? item.end : false}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <main id="main-content" className="main-content" tabIndex={-1}>
        <RailStatusBanner status={railStatus} />
        <Outlet key={location.pathname} />
      </main>

      <footer>
        Data updates may be delayed. Confirm critical travel decisions with
        official LTA and NEA channels.
      </footer>
    </div>
  );
}
