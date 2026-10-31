import { NavLink } from "react-router-dom";

/** Renders navigation between transit status, crowding, and bus views. */
export function TransitSubnav() {
  return (
    <div className="subnav" aria-label="Transit views">
      <NavLink to="/transit/crowding">Station Crowd Forecast</NavLink>
      <NavLink to="/transit/buses">Bus Arrivals & Services</NavLink>
    </div>
  );
}
