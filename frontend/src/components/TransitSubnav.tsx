import { NavLink } from "react-router-dom";

export function TransitSubnav() {
  return (
    <div className="subnav" aria-label="Transit views">
      <NavLink to="/transit/crowding">Station Crowd Forecast</NavLink>
      <NavLink to="/transit/buses">Bus Arrivals & Services</NavLink>
    </div>
  );
}
