/** Default Leaflet centre for Singapore overview maps. */
export const SINGAPORE_MAP_CENTRE: [number, number] = [1.3521, 103.8198];

/** Returns an explicit map centre, or Singapore when none is provided. */
export function resolveMapCentre(centre?: [number, number]): [number, number] {
  if (
    centre
    && Number.isFinite(centre[0])
    && Number.isFinite(centre[1])
  ) {
    return centre;
  }
  return SINGAPORE_MAP_CENTRE;
}
