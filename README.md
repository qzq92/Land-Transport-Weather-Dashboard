# Land Transport, Weather and Healthcare Dashboard

A React and FastAPI application for Singapore that presents near real-time weather, health, and land-transport data on interactive maps. Redis shares queried results across API workers so browser refreshes do not multiply requests to Data.gov.sg, LTA DataMall, or OneMap.

## How it works

The TypeScript client in `frontend/` calls versioned JSON endpoints under `/api/v1`. The FastAPI service in `backend/` validates query parameters, normalizes provider responses, and uses Redis for cache-aside reads, distributed refresh locks, TTL jitter, and bounded stale fallback. Provider credentials remain in the API container and are never sent to the browser.

Nginx serves the built React application and proxies `/api` to FastAPI from
the same origin. `compose.yaml` starts Nginx, the API, and Redis together.
The React presentation preserves the original dashboard's compact Open Sans
styling, gradient banner, glossy six-tab navigation, slate panels, and OneMap
night map while keeping route-level code splitting and typed data fetching.

## Architecture

The production stack has three services:

- **Web (`web`)**: Nginx serves the compiled React files and forwards `/api/*`
  requests to the API service. It is the only service exposed to the host on
  port `8080`.
- **API (`api`)**: FastAPI owns input validation, provider authentication,
  response normalization, cache policy, and the versioned `/api/v1` contract.
  It is reachable only inside the Compose network on port `8000`.
- **Cache (`redis`)**: Redis stores shared, expiring JSON query results and
  short-lived refresh locks. It is reachable only by the API service.

### Request flow

1. A React page loads its typed query through TanStack Query. Browser state
   covers navigation and UI controls; it never contains provider credentials or
   connects to Redis.
2. The browser requests the same-origin URL, for example
   `/api/v1/weather/realtime`. Nginx forwards that request to FastAPI.
3. FastAPI validates parameters, builds a versioned Redis key from normalized
   request parameters, and checks for a fresh cached result.
4. On a cache hit, FastAPI returns the normalized response immediately. On a
   miss, one request acquires a short Redis lock and queries Data.gov.sg, LTA
   DataMall, or OneMap through the HTTP client. Concurrent requests wait for
   the cached result rather than duplicating the upstream call.
5. FastAPI transforms provider payloads into stable view models in
   `backend/presenters.py`, stores the result with its TTL and stale fallback
   period, then returns JSON plus cache metadata to React.
6. React renders the result and shows loading, refresh, stale, empty, or error
   states based on the typed API response.

### Data ownership and resilience

- **React** owns presentation and short-lived browser query state. TanStack
  Query reduces unnecessary refetches but Redis remains the cross-user and
  cross-worker cache.
- **FastAPI** is the only layer allowed to call external providers or access
  `BACKEND_*` credentials. It exposes provider-independent API responses, so
  provider field changes stay isolated from UI components.
- **Redis** is a cache, not the system of record. It contains no credentials,
  no browser sessions, and no traffic-camera image bytes. The `redis-data`
  Docker volume preserves cache contents across normal container restarts.
- If an upstream provider fails after a successful request, FastAPI can return
  a bounded stale cached response with `meta.stale=true`. If Redis is optional
  and unavailable, the API degrades to uncached provider reads and reports the
  degraded state in response metadata.

## Tech stack

| Layer | Choice |
| --- | --- |
| Web | React, TypeScript, Vite, React Router, TanStack Query |
| Maps / charts | React Leaflet, Plotly React |
| API | Python **≥ 3.12**, FastAPI, Pydantic, HTTPX |
| Shared cache | Redis 7 |
| Package managers | [uv](https://docs.astral.sh/uv/) and npm |
| Tests | pytest, Vitest, Testing Library |
| Deploy | Docker Compose and Nginx (see [DEPLOYMENT.md](DEPLOYMENT.md)) |

## Routes

React Router lazy-loads each view:

- `/` — operational overview. Checkpoint cameras (Woodlands Causeway and
  Tuas Second Link) sit beside a map that starts empty; taxi, camera, incident,
  and variable-message-sign layers are opt-in. The rail banner stays above
  every tab and reports only whether train services are operational, with an
  update time and a line list.
  The right rail shows flood and lightning counts, average PSI, the next
  24-hour forecast, incident and faulty-light counts, and dengue/Zika cluster
  counts.
- `/weather/realtime` — averaged temperature, rainfall, humidity, wind,
  lightning, flood, and WBGT readings beside a map. Each sensor type has its
  own location toggle, and markers stay hidden until that toggle is selected.
- `/environment` — PSI, UV, and WBGT summaries, an air-quality legend, and
  dengue and Zika cluster lists. Map toggles control PSI and cluster markers;
  the cluster lists stay visible.
- `/healthcare` — official emergency-department queue estimates in a
  hospital-by-row table. Each hospital name links to its official source
  page, the Updated column is the date and time after "Last updated at"
  on that page, and data limitations are shown in a status banner.
- `/transport` — an operations map with the same opt-in taxi, camera,
  road-incident, and variable-message-sign layers. Network metrics and road
  advisories sit to the left of the map; rail advisories sit to the right.
- `/transport/travel-times` — expressway travel times.
- `/transport/cameras` — a dense gallery of traffic-camera images. Names come
  from `data/lta_camera_id_mapping.csv`.
- `/transit/crowding` — MRT/LRT realtime station crowding as a station list
  with one colour indicator per station. The shared reporting period is
  centred above the grid. Station names come from `data/MRTLRTStations.csv`.
  CE1 is Bayfront (CC34) and CE2 is Marina Bay (CC33).
- `/transit/crowding/forecast` — the same station colour-indicator grid as
  realtime crowding, extended across LTA's 30-minute forecast intervals
  from 00:00 to 23:30.
- `/transit/buses` — bus arrival timings for a five-digit stop code, with
  soonest or service-number sorting, a service filter, and a service-route
  search. Bus stop locations stay off the map until "Show Bus Stop Locations"
  is turned on.
- `/nearby` — address search and Use my location stay visible. The map pans
  to a suggested address after it is selected. Getting around, Park and
  charge, and Food & Amenities lists, plus map markers, appear only after a
  postal address or location is selected. Bus stops, taxi stands, carparks,
  bicycle parking, and EV chargers come from LTA DataMall. MRT/LRT points
  come from `data/MRTLRTStations.csv`. Nearby bus stops also show every
  reported bus service with its next arrival times and load/accessibility
  status. Each facility type has a show/hide toggle, and its points appear
  on the map only while that toggle is on.
  The map legend lists the same layers as the visible toggles for the
  selected tab.

Every route has typed loading, error, refreshing, stale-data, and empty states.
Maps use OneMap tiles through React Leaflet and can be zoomed with the mouse
wheel. Charts use a lazy route-level
Plotly basic bundle rather than loading the full chart library on every page.

## Project layout

```
backend/               # FastAPI routes, services, provider clients, Redis cache
frontend/              # Strict TypeScript React application
docker/                # API/web images and Nginx configuration
compose.yaml           # Web, API, and Redis development/production stack
conf/
  api_urls.py          # Provider bases, endpoints, and dataset IDs
data/
  lta_camera_id_mapping.csv  # Traffic-camera ID to location name
  MRTLRTStations.csv         # MRT/LRT station code to name
tests/
  api/                 # FastAPI route and presenter tests
  integration/         # Provider-backed route tests
  contract/            # OpenAPI contract tests
  fixtures/            # Sanitized provider responses
```

## Data sources

Provider URLs and dataset IDs remain centralized in `conf/api_urls.py`.

- **Data.gov.sg**: realtime temperature, rainfall, humidity, wind, lightning,
  flood alerts, PSI, UV, WBGT, 2-hour/24-hour forecasts, taxi availability,
  traffic cameras, dengue/Zika clusters, and public amenities (parks, sports
  fields, recycling bins, and hawker centres).
- **LTA DataMall**: traffic incidents, faulty traffic lights, variable message
  signs, travel times, carpark availability, taxi stands, bicycle parking,
  EV chargers (EVCBatch), bus stops/services/arrivals, train status,
  crowding, and crowd forecasts.
- **OneMap**: address search, authentication, and night map tiles. Every map
  opens at zoom 13. Marker layers stay off until a page toggle is selected.

Provider payloads are converted to stable frontend view models in
`backend/presenters.py`; React does not depend on provider-specific field names.

## Cache behavior

Redis keys are versioned and parameter-aware. Live arrivals use a short TTL,
most realtime feeds use two minutes, crowd data uses longer TTLs, and reference
or dataset responses use hourly/daily TTLs. Fresh values receive TTL jitter to
avoid synchronized expiry. A short distributed lock coalesces concurrent cache
misses, while a bounded stale copy is returned when a provider fails. Responses
include cache state, fetch time, age, stale state, and Redis degradation metadata.

## Requirements

Recommended: Docker Desktop with Compose. For native development, install
Python 3.12+, [uv](https://docs.astral.sh/uv/getting-started/installation/),
Node.js 22+, and Redis 7.

```bash
git clone https://github.com/qzq92/Land-Transport-Weather-Dashboard.git
cd Land-Transport-Weather-Dashboard
copy .env.example .env
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080). Compose persists Redis
data in the named `redis-data` volume and waits for API/Redis health checks.
FastAPI port 8000 is internal to the Compose network; use
`http://localhost:8080/api/v1/docs` for API documentation.

`uv.lock` and `frontend/package-lock.json` are committed intentionally.
Containers isolate the runtime but do not pin transitive dependency versions;
the API image installs with `uv sync --frozen --no-dev`, and the web image
uses `npm ci`.

`compose.yaml` is the standard Docker Compose entry point. It builds and
networks the web and API images, starts Redis, applies health checks, and
provides the named cache volume.

### Environment variables

```env
BACKEND_DATA_GOV_API_KEY=your_data_gov_api_key_here
BACKEND_LTA_API_KEY=your_lta_api_key_here
BACKEND_ONEMAP_EMAIL=your_onemap_email_here
BACKEND_ONEMAP_EMAIL_PASSWORD=your_onemap_password_here
# Alternatively: BACKEND_ONEMAP_API_KEY=your_onemap_token_here
BACKEND_REDIS_URL=redis://localhost:6379/0
BACKEND_REDIS_REQUIRED=false
```

| Variable | Where to get it | Used for |
| --- | --- | --- |
| `BACKEND_DATA_GOV_API_KEY` | [Request a key](https://guide.data.gov.sg/developer-guide/api-overview/how-to-request-an-api-key) | Weather, environment, taxis, cameras, and datasets |
| `BACKEND_ONEMAP_EMAIL` / `BACKEND_ONEMAP_EMAIL_PASSWORD` | [OneMap register](https://www.onemap.gov.sg/apidocs/register) | Address search |
| `BACKEND_ONEMAP_API_KEY` | OneMap | Optional pre-issued token instead of email/password |
| `BACKEND_LTA_API_KEY` | [DataMall request form](https://datamall.lta.gov.sg/content/datamall/en/request-for-api.html) | Road, bus, and rail feeds |
| `BACKEND_REDIS_URL` | Local or managed Redis | Shared expiring query cache |

## Run locally

Use `docker compose up --build` for the complete stack. Native development:

```bash
uv sync --all-groups
uv run uvicorn backend.main:app --reload --port 8000
cd frontend
npm ci
npm run dev
```

The Vite server runs at `http://localhost:5173` and proxies API requests to
FastAPI. Start a local Redis instance or set `BACKEND_REDIS_URL`; the API can
degrade to uncached provider reads when Redis is optional.

### Tests and lint

```bash
uv run pytest
uv run ruff check backend
uv run mypy backend
cd frontend
npm run lint
npm test
npm run build
```

CI runs Python and strict TypeScript checks, Redis integration tests, and
production container builds on `main`.

## How development is structured

- Keep provider URLs centralized in `conf/api_urls.py`.
- Keep route handlers thin; provider access belongs in backend clients and
  normalization/caching belongs in services.
- Keep React server state in TanStack Query and local interaction state inside
  the smallest relevant component.
- Keep TypeScript strict and do not use `any` to bypass API contracts.
- Keep script files at or under 700 lines.
- Add or update a unit test with each behaviour change.
- Never connect the browser directly to Redis or expose provider credentials.

## Known limitations

- Live bus arrivals require a bus stop code. The service box looks up the
  route, and the filter on the arrival board only narrows services already
  calling at that stop.
- Healthcare wait times are scraped from official hospital pages on the
  server, cached for 30 minutes, and marked with source links. The Updated
  field is the date and time after "Last updated at" on each source page,
  without surrounding copy. Hospital coverage and fields vary by page;
  estimates are informational and should not be used to delay emergency
  care.
- Some LTA traffic-camera images may be unavailable as feeds are retired.
  Unmapped camera IDs fall back to the provider ID when
  `data/lta_camera_id_mapping.csv` has no name.
- The rail banner uses LTA's aggregate train-status value. "View all lines"
  lists each line, but a disruption is not attributed to a specific line.
- Crowd realtime and forecast grids stay empty when LTA DataMall returns
  HTTP 403 for the configured key. The station-by-time grid renders once
  that feed is authorized.
- Road and nearby pages do not yet include ERP gantries or speed cameras.
- Cache refresh is request-driven. A dedicated refresh worker should be added
  only if production measurements show unacceptable cold-cache latency.

## Deployment

Container deployment, health checks, Redis persistence, and rollback guidance
are in [DEPLOYMENT.md](DEPLOYMENT.md).
