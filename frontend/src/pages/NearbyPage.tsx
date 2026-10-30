import { type FormEvent, useState } from "react";
import { useNearby, usePlaceSearch } from "../api/queries";
import type { NearbyPlace } from "../api/schema";
import { MapView } from "../components/MapView";
import { QueryState } from "../components/QueryState";

const SINGAPORE_CENTRE = { latitude: 1.3521, longitude: 103.8198 };
const NEARBY_RADIUS_M = 2000;

const FACILITY_TABS = [
  {
    value: "getting-around",
    label: "Getting around",
    layers: [
      {
        id: "bus-stops",
        show: "Show Bus Stops",
        hide: "Hide Bus Stops",
        list: "Nearby bus stops (Top 5)",
      },
      {
        id: "taxi-stands",
        show: "Show Taxi Stands",
        hide: "Hide Taxi Stands",
        list: "Nearby taxi stands (Top 5)",
      },
      {
        id: "mrt-stations",
        show: "Show MRT/LRT",
        hide: "Hide MRT/LRT",
        list: "Nearby MRT and LRT (Top 5)",
      },
    ],
  },
  {
    value: "park-and-charge",
    label: "Park and charge",
    layers: [
      {
        id: "carparks",
        show: "Show Carparks",
        hide: "Hide Carparks",
        list: "Nearby carparks (Top 5)",
      },
      {
        id: "bicycle-parking",
        show: "Show Bicycle Parking",
        hide: "Hide Bicycle Parking",
        list: "Nearby bicycle parking (Top 5)",
      },
      {
        id: "ev-charging",
        show: "Show EV Charging",
        hide: "Hide EV Charging",
        list: "Nearby EV charging (Top 5)",
      },
    ],
  },
  {
    value: "food-amenities",
    label: "Food & Amenities",
    layers: [
      {
        id: "hawker-centres",
        show: "Show Hawker Centres",
        hide: "Hide Hawker Centres",
        list: "Food places",
        note: "Hawker-centre locations near the selected place.",
      },
      {
        id: "parks",
        show: "Show Parks@SG",
        hide: "Hide Parks@SG",
        list: "Nearby Parks (Top 5)",
      },
      {
        id: "sports-fields",
        show: "Show SportsFields@SG",
        hide: "Hide SportsFields@SG",
        list: "Nearby Sports Fields (Top 5)",
      },
      {
        id: "recycling-bins",
        show: "Show Recycling Bins",
        hide: "Hide Recycling Bins",
        list: "Nearby Recycling Bins (Top 5)",
      },
    ],
  },
] as const;

const LEGEND = [
  { id: "bus-stops", label: "Bus Stop" },
  { id: "taxi-stands", label: "Taxi Stand" },
  { id: "mrt-stations", label: "MRT/LRT Station" },
  { id: "carparks", label: "Carpark" },
  { id: "bicycle-parking", label: "Bicycle Parking" },
  { id: "ev-charging", label: "EV Charging Point" },
  { id: "parks", label: "Parks@SG" },
  { id: "sports-fields", label: "SportsFields@SG" },
  { id: "recycling-bins", label: "Recycling Bins" },
  { id: "hawker-centres", label: "Hawker Centres" },
] as const;

function formatDistance(distanceM: number): string {
  return distanceM < 1000
    ? `${Math.round(distanceM)} m`
    : `${(distanceM / 1000).toFixed(1)} km`;
}

function closestPlaces(places: NearbyPlace[], category: string): NearbyPlace[] {
  return places
    .filter((place) => place.category === category)
    .slice()
    .sort((left, right) => left.distance_m - right.distance_m)
    .slice(0, 5);
}

export default function NearbyPage() {
  const [draft, setDraft] = useState("");
  const [searchText, setSearchText] = useState("");
  const [location, setLocation] = useState(SINGAPORE_CENTRE);
  const [selectedLabel, setSelectedLabel] = useState("");
  const [locationError, setLocationError] = useState("");
  const [facilityTab, setFacilityTab] = useState("food-amenities");
  const [activeLayers, setActiveLayers] = useState<Set<string>>(() => new Set());
  const search = usePlaceSearch(searchText);
  const nearby = useNearby(location.latitude, location.longitude);
  const places = nearby.data?.data.places ?? [];
  const selectedTab = FACILITY_TABS.find((tab) => tab.value === facilityTab)
    ?? FACILITY_TABS[0];
  const mapPoints = [
    ...(selectedLabel
      ? [{
          id: "selected-location",
          name: selectedLabel,
          latitude: location.latitude,
          longitude: location.longitude,
          category: "search",
          value: "Selected place",
        }]
      : []),
    ...places
      .filter(
        (place) =>
          activeLayers.has(place.category ?? "")
          && place.distance_m <= NEARBY_RADIUS_M,
      )
      .map((place) => ({
        ...place,
        value: formatDistance(place.distance_m),
      })),
  ];

  function submit(event: FormEvent) {
    event.preventDefault();
    if (draft.trim().length >= 3) setSearchText(draft.trim());
  }

  function toggleLayer(category: string) {
    setActiveLayers((current) => {
      const next = new Set(current);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  }

  function useDeviceLocation() {
    if (!navigator.geolocation) {
      setLocationError("Location is not supported by this browser.");
      return;
    }
    setLocationError("");
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setLocation({
          latitude: coords.latitude,
          longitude: coords.longitude,
        });
        setSelectedLabel("Current location");
      },
      () => setLocationError("Location permission was denied or unavailable."),
      { enableHighAccuracy: true, timeout: 10_000 },
    );
  }

  return (
    <QueryState
      loading={nearby.isPending}
      error={nearby.error}
      fetching={nearby.isFetching}
      meta={nearby.data?.meta}
      onRetry={() => void nearby.refetch()}
    >
      <div className="nearby-operations-layout">
        <aside className="nearby-operations-rail">
          <h1>Nearby Facilities</h1>
          <div className="nearby-controls">
            <form className="search-form" onSubmit={submit}>
              <label className="search-grow">
                <span className="sr-only">Address or landmark</span>
                <input
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder="Postal code or address"
                  minLength={3}
                />
              </label>
              <button type="submit" disabled={draft.trim().length < 3}>
                Search
              </button>
            </form>
            <button
              type="button"
              className="button-secondary"
              onClick={useDeviceLocation}
            >
              Use my location
            </button>
            {selectedLabel && (
              <p className="nearby-selected-place">{selectedLabel}</p>
            )}
            {locationError && (
              <p className="form-error" role="alert">{locationError}</p>
            )}
            {search.isFetching && (
              <p className="freshness-note">Searching addresses…</p>
            )}
            {search.error && (
              <p className="form-error" role="alert">{search.error.message}</p>
            )}
            {(search.data?.data.length ?? 0) > 0 && (
              <div
                className="search-results"
                role="listbox"
                aria-label="Address matches"
              >
                {search.data?.data.map((result) => (
                  <button
                    key={result.id}
                    type="button"
                    role="option"
                    aria-selected="false"
                    onClick={() => {
                      setLocation({
                        latitude: result.latitude,
                        longitude: result.longitude,
                      });
                      setSelectedLabel(result.label);
                      setSearchText("");
                      setDraft(result.label);
                    }}
                  >
                    {result.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="nearby-filter-tabs" aria-label="Facility types">
            {FACILITY_TABS.map((tab) => (
              <button
                type="button"
                className={facilityTab === tab.value ? "is-active" : ""}
                key={tab.value}
                onClick={() => setFacilityTab(tab.value)}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="nearby-layer-toggles" aria-label="Map layers">
            {selectedTab.layers.map((layer) => {
              const isActive = activeLayers.has(layer.id);
              return (
                <button
                  aria-pressed={isActive}
                  className={`layer-${layer.id}${isActive ? " is-active" : ""}`}
                  key={layer.id}
                  onClick={() => toggleLayer(layer.id)}
                  type="button"
                >
                  {isActive ? layer.hide : layer.show}
                </button>
              );
            })}
          </div>
          <div className="nearby-facility-groups">
            {selectedTab.layers.map((layer) => {
              const items = closestPlaces(places, layer.id);
              return (
                <section key={layer.id}>
                  <h2>{layer.list}</h2>
                  {"note" in layer && layer.note && <p>{layer.note}</p>}
                  {items.length ? (
                    <ul className="place-list">
                      {items.map((place) => (
                        <li key={place.id}>
                          <strong>{place.name}</strong>
                          <b>{formatDistance(place.distance_m)}</b>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="nearby-empty">No data available</p>
                  )}
                </section>
              );
            })}
          </div>
        </aside>
        <section className="nearby-map-panel">
          <MapView
            points={mapPoints}
            centre={[location.latitude, location.longitude]}
            height={650}
            ariaLabel="Nearby facilities map"
          />
          <ul className="nearby-map-legend" aria-label="Map legend">
            {LEGEND.map((item) => (
              <li className={`layer-${item.id}`} key={item.id}>
                <span aria-hidden="true" />
                {item.label}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </QueryState>
  );
}
