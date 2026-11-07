import { useEffect, useRef } from "react";
import {
  CircleMarker,
  MapContainer,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";
import type { LatLngExpression } from "leaflet";
import type { GeoPoint } from "../api/schema";
import { resolveMapCentre } from "../utils/map";

/** A polyline path rendered on the Leaflet map. */
export interface MapPath {
  id: string;
  color: string;
  positions: [number, number][];
}

interface MapViewProps {
  points: GeoPoint[];
  paths?: MapPath[];
  centre?: [number, number];
  zoom?: number;
  height?: number;
  ariaLabel?: string;
  onSelect?: (point: GeoPoint) => void;
}

const categoryColours: Record<string, string> = {
  weather: "#35c9ff",
  "air-temperature": "#3dd68c",
  rainfall: "#f0a05a",
  "relative-humidity": "#5dcaa5",
  "wind-speed": "#6cb6ff",
  lightning: "#f5d76e",
  flood: "#ff6b6b",
  wbgt: "#ff9f43",
  psi: "#f5d76e",
  zika: "#c69cff",
  dengue: "#ff6b6b",
  incident: "#ff6b6b",
  camera: "#c69cff",
  transit: "#52e0a1",
  environment: "#f5d76e",
  taxi: "#ffd166",
  vms: "#d1d5db",
  search: "#f8fafc",
  "bus-stops": "#35c9ff",
  "taxi-stands": "#ffd166",
  "mrt-stations": "#ff6b6b",
  carparks: "#f5d76e",
  "bicycle-parking": "#52e0a1",
  "ev-charging": "#c69cff",
  parks: "#3dd68c",
  "sports-fields": "#8dff6a",
  "recycling-bins": "#6cb6ff",
  "hawker-centres": "#d946ef",
};

/** Normalizes a Leaflet centre to a `[latitude, longitude]` tuple. */
function latLngTuple(centre: LatLngExpression): [number, number] {
  if (Array.isArray(centre)) {
    return [centre[0], centre[1]];
  }
  return [centre.lat, centre.lng];
}

/** Pans the map when the parent `centre` prop changes without resetting wheel zoom. */
function MapViewport({
  centre,
  zoom,
}: {
  centre: LatLngExpression;
  zoom: number;
}) {
  const map = useMap();
  const [latitude, longitude] = latLngTuple(centre);
  const programmedCentre = useRef<[number, number] | null>(null);
  useEffect(() => {
    map.invalidateSize();
    const previous = programmedCentre.current;
    const centreChanged =
      previous === null
      || previous[0] !== latitude
      || previous[1] !== longitude;
    programmedCentre.current = [latitude, longitude];
    if (!centreChanged) {
      return;
    }
    map.setView([latitude, longitude], zoom);
  }, [latitude, longitude, map, zoom]);
  return null;
}

/**
 * Renders geographic points, optional paths, and an optional map viewport.
 * The mouse wheel zooms the map; programmatic recentring only runs when the
 * `centre` prop changes so layer toggles and data refreshes keep the view.
 */
export function MapView({
  points,
  paths = [],
  centre,
  zoom = 13,
  height = 440,
  ariaLabel = "Interactive Singapore map",
  onSelect,
}: MapViewProps) {
  const validPoints = points.filter(
    (point) =>
      Number.isFinite(point.latitude) && Number.isFinite(point.longitude),
  );
  const mapCentre: LatLngExpression = resolveMapCentre(centre);

  return (
    <div
      className="map-frame"
      style={{ height }}
      role="region"
      aria-label={ariaLabel}
    >
      <MapContainer
        center={mapCentre}
        zoom={zoom}
        scrollWheelZoom={true}
        className="map"
      >
        <MapViewport centre={mapCentre} zoom={zoom} />
        <TileLayer
          attribution='Map data © <a href="https://www.onemap.gov.sg/">OneMap</a>, Singapore Land Authority'
          url="https://www.onemap.gov.sg/maps/tiles/Night/{z}/{x}/{y}.png"
        />
        {paths.map((path) => (
          <Polyline
            key={path.id}
            positions={path.positions}
            pathOptions={{ color: path.color, weight: 4, opacity: 0.9 }}
          />
        ))}
        {validPoints.map((point) => (
          <CircleMarker
            key={point.id}
            center={[point.latitude, point.longitude]}
            radius={7}
            pathOptions={{
              color: categoryColours[point.category ?? ""] ?? "#35c9ff",
              fillOpacity: 0.75,
              weight: 2,
            }}
            eventHandlers={
              onSelect
                ? { click: () => onSelect(point) }
                : undefined
            }
          >
            <Popup>
              <strong>{point.name}</strong>
              {point.value !== undefined && <p>{point.value}</p>}
              {point.detail && <p>{point.detail}</p>}
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
