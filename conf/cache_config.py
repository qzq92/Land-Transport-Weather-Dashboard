"""
Centralised cache and UI refresh configuration.

The primary names below are organised by the callback/page/domain that uses
them. Private base durations keep the arithmetic in one place, while the
public names make call sites read like product behaviour rather than raw
numbers.
"""

# ---------------------------------------------------------------------------
# Private base durations
# ---------------------------------------------------------------------------

_SECONDS_1_MIN: int = 60
_SECONDS_2_MIN: int = 2 * _SECONDS_1_MIN
_SECONDS_3_MIN: int = 3 * _SECONDS_1_MIN
_SECONDS_5_MIN: int = 5 * _SECONDS_1_MIN
_SECONDS_10_MIN: int = 10 * _SECONDS_1_MIN
_SECONDS_24_HOURS: int = 24 * 60 * 60
_MILLISECONDS: int = 1000

# ---------------------------------------------------------------------------
# Callback/domain cache TTLs  (seconds)
# ---------------------------------------------------------------------------

# Main dashboard live-data callbacks:
# checkpoint cameras, weather forecast, lightning/flood cards, traffic
# incidents, train service alerts, taxi count, PSI and disease summaries.
TTL_MAIN_DASHBOARD_API: int = _SECONDS_2_MIN

# Realtime Weather tab callbacks:
# temperature, rainfall, humidity, wind, lightning, flood and WBGT readings.
TTL_REALTIME_WEATHER_CALLBACKS: int = _SECONDS_2_MIN

# Daily Health and Environmental Watch tab callbacks:
# PSI, UV and WBGT API responses.
TTL_WEATHER_INDICES_CALLBACKS: int = _SECONDS_2_MIN

# Road & Transport Metrics tab callbacks:
# taxi, CCTV metadata, traffic incidents, faulty lights, ERP, VMS and similar
# transport feeds that use the shared URL cache.
TTL_TRANSPORT_CALLBACKS: int = _SECONDS_2_MIN

# Traffic Conditions tab callbacks:
# all-LTA-camera metadata and displayed camera grid refreshes.
TTL_TRAFFIC_CONDITIONS_CALLBACKS: int = _SECONDS_2_MIN

# Nearby facilities geospatial overlays:
# Parks@SG and SportsFields@SG poll-download datasets.
TTL_NEARBY_FACILITIES_CALLBACKS: int = _SECONDS_24_HOURS

# MRT/LRT station crowd callbacks:
# realtime per-line crowd levels and the combined all-lines crowd cache.
TTL_MRT_CROWD_CALLBACKS: int = _SECONDS_10_MIN

# Disease cluster callbacks:
# Zika and Dengue GeoJSON poll-download responses.
# These datasets are relatively slow-moving and poll-download endpoints can
# rate-limit aggressively, so keep refresh to once daily.
TTL_DISEASE_CLUSTER_CALLBACKS: int = _SECONDS_24_HOURS
TTL_DISEASE_CLUSTER_RETRY_SECONDS: int = _SECONDS_5_MIN

# Analytics Forecast tab callbacks:
# LTA PCDForecast per train line.
TTL_ANALYTICS_FORECAST_CALLBACKS: int = _SECONDS_24_HOURS

# Data.gov.sg initiate-download datasets:
# ERP gantries, HDB carpark, speed camera and PUB CCTV batch datasets.
TTL_INITIATE_DOWNLOAD_DATASETS: int = _SECONDS_24_HOURS

# ---------------------------------------------------------------------------
# UI refresh cadences  (milliseconds, for dcc.Interval)
# ---------------------------------------------------------------------------

INTERVAL_MAIN_MS: int = TTL_MAIN_DASHBOARD_API * _MILLISECONDS
INTERVAL_FLOOD_MS: int = _SECONDS_3_MIN * _MILLISECONDS

INTERVAL_REALTIME_WEATHER_MS: int = (
    TTL_REALTIME_WEATHER_CALLBACKS * _MILLISECONDS
)
INTERVAL_WEATHER_INDICES_MS: int = TTL_WEATHER_INDICES_CALLBACKS * _MILLISECONDS
INTERVAL_TRANSPORT_MS: int = TTL_TRANSPORT_CALLBACKS * _MILLISECONDS
INTERVAL_BUS_ARRIVAL_MS: int = _SECONDS_1_MIN * _MILLISECONDS
INTERVAL_TRAVEL_TIMES_MS: int = TTL_MAIN_DASHBOARD_API * _MILLISECONDS
INTERVAL_TRAFFIC_CONDITIONS_MS: int = (
    TTL_TRAFFIC_CONDITIONS_CALLBACKS * _MILLISECONDS
)
INTERVAL_NEARBY_TRANSPORT_MS: int = TTL_TRANSPORT_CALLBACKS * _MILLISECONDS
INTERVAL_EV_CHARGING_MS: int = _SECONDS_5_MIN * _MILLISECONDS

# ---------------------------------------------------------------------------
# Backwards-compatible aliases
# ---------------------------------------------------------------------------

# Generic shared URL bucket helpers still need compact names because they are
# used by multiple callback domains through utils/async_fetcher.py.
CACHE_TTL_2MIN: int = TTL_MAIN_DASHBOARD_API
CACHE_TTL_10MIN: int = TTL_MRT_CROWD_CALLBACKS

# Legacy names retained for existing imports; prefer the callback/domain names
# above in new code.
CACHE_TTL_CLUSTER: int = TTL_DISEASE_CLUSTER_CALLBACKS
CACHE_TTL_FORECAST: int = TTL_ANALYTICS_FORECAST_CALLBACKS
CACHE_TTL_DATASET: int = TTL_INITIATE_DOWNLOAD_DATASETS
