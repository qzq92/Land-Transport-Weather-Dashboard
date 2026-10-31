import { NavLink } from "react-router-dom";

/** Renders navigation between realtime crowding, forecast, and bus views. */
export function TransitSubnav() {
  return (
    <div className="subnav" aria-label="Transit views">
      <NavLink to="/transit/crowding" end>
        Station Crowd Realtime
      </NavLink>
      <NavLink to="/transit/crowding/forecast">Station Crowd Forecast</NavLink>
      <NavLink to="/transit/buses">Bus Arrivals & Services</NavLink>
    </div>
  );
}
