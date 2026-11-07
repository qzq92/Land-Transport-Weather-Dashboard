"""HTTP endpoints and dataset IDs used by the dashboard.

This is the only place that should define information-source URLs.
"""

# Data.gov.sg
DATA_GOV_REALTIME_API_BASE = "https://api-open.data.gov.sg/v2/real-time/api"
DATA_GOV_DATASET_API_BASE = "https://api-open.data.gov.sg/v1/public/api/datasets"
DATA_GOV_V1_API_BASE = "https://api.data.gov.sg/v1"

TAXI_API_URL = f"{DATA_GOV_V1_API_BASE}/transport/taxi-availability"
TRAFFIC_IMAGES_API_URL = f"{DATA_GOV_V1_API_BASE}/transport/traffic-images"
WEATHER_2H_FORECAST_URL = f"{DATA_GOV_V1_API_BASE}/environment/2-hour-weather-forecast"
WEATHER_24H_FORECAST_URL = f"{DATA_GOV_REALTIME_API_BASE}/twenty-four-hr-forecast"
FLOOD_ALERTS_URL = f"{DATA_GOV_REALTIME_API_BASE}/weather/flood-alerts"
LIGHTNING_URL = f"{DATA_GOV_REALTIME_API_BASE}/weather?api=lightning"
PSI_URL = f"{DATA_GOV_REALTIME_API_BASE}/psi"
UV_URL = f"{DATA_GOV_REALTIME_API_BASE}/uv"
WBGT_URL = f"{DATA_GOV_REALTIME_API_BASE}/weather?api=wbgt"

# LTA DataMall
LTA_DATAMALL_BASE = "https://datamall2.mytransport.sg/ltaodataservice"

TRAFFIC_INCIDENTS_URL = f"{LTA_DATAMALL_BASE}/TrafficIncidents"
FAULTY_TRAFFIC_LIGHTS_URL = f"{LTA_DATAMALL_BASE}/FaultyTrafficLights"
VMS_URL = f"{LTA_DATAMALL_BASE}/VMS"
EV_CHARGING_URL = f"{LTA_DATAMALL_BASE}/EVChargingPoints"
EV_CHARGING_BATCH_URL = f"{LTA_DATAMALL_BASE}/EVCBatch"
BUS_STOPS_URL = f"{LTA_DATAMALL_BASE}/BusStops"
TAXI_STANDS_URL = f"{LTA_DATAMALL_BASE}/TaxiStands"
BICYCLE_PARKING_URL = f"{LTA_DATAMALL_BASE}/v3/BicycleParking"
BUS_SERVICES_URL = f"{LTA_DATAMALL_BASE}/BusServices"
BUS_ROUTES_URL = f"{LTA_DATAMALL_BASE}/BusRoutes"
BUS_ARRIVAL_URL = f"{LTA_DATAMALL_BASE}/v3/BusArrival"
CARPARK_AVAILABILITY_URL = f"{LTA_DATAMALL_BASE}/CarParkAvailabilityv2"
EST_TRAVEL_TIMES_URL = f"{LTA_DATAMALL_BASE}/EstTravelTimes"
PCD_FORECAST_URL = f"{LTA_DATAMALL_BASE}/PCDForecast"
PCD_REALTIME_URL = f"{LTA_DATAMALL_BASE}/PCDRealTime"
TRAIN_SERVICE_ALERTS_URL = f"{LTA_DATAMALL_BASE}/TrainServiceAlerts"

# Official hospital emergency queue pages
TTSH_EMERGENCY_WAIT_URL = (
    "https://www.nhghealth.com.sg/ttsh/ed-queue-status"
)
WOODLANDS_EMERGENCY_WAIT_URL = (
    "https://www.nhghealth.com.sg/wh/for-patients-visitors/emergency-care"
)
KTPH_EMERGENCY_WAIT_URL = (
    "https://www.nhghealth.com.sg/ktph/i-want-to/visit-a-e"
)
NUHS_EMERGENCY_WAIT_URL = (
    "https://www.nuhs.edu.sg/patient-care/emergency-department-wait-times"
)

# OneMap
ONEMAP_BASE = "https://www.onemap.gov.sg"
ONEMAP_TOKEN_URL = f"{ONEMAP_BASE}/api/auth/post/getToken"
ONEMAP_SEARCH_URL = f"{ONEMAP_BASE}/api/common/elastic/search"
ONEMAP_NEAREST_BUS_STOPS_URL = f"{ONEMAP_BASE}/api/public/nearbysvc/getNearestBusStops"
ONEMAP_NEAREST_MRT_STOPS_URL = f"{ONEMAP_BASE}/api/public/nearbysvc/getNearestMrtStops"

# Dataset IDs used to build Data.gov.sg download URLs
PARKS_DATASET_ID = "d_99b71f5d34cf57a3a592fbfdef1f42b6"
SPORTS_FIELDS_DATASET_ID = "d_f71b449b4b43a69b5ecfe411b440d249"
RECYCLING_BINS_DATASET_ID = "d_4dde14826642f49eefff48b7832b90db"
HAWKER_CENTRES_DATASET_ID = "d_4a086da0a5553be1d89383cd90d07ecd"
ZIKA_DATASET_ID = "d_a3c783f11d79ff7feb8856f762ccf2c5"
DENGUE_DATASET_ID = "d_dbfabf16158d1b0e1c420627c0819168"


def poll_download_url(dataset_id: str) -> str:
    """Build a Data.gov.sg poll-download URL for a dataset."""
    return f"{DATA_GOV_DATASET_API_BASE}/{dataset_id}/poll-download"


PARKS_POLL_DOWNLOAD_URL = poll_download_url(PARKS_DATASET_ID)
SPORTS_FIELDS_POLL_DOWNLOAD_URL = poll_download_url(SPORTS_FIELDS_DATASET_ID)
RECYCLING_BINS_POLL_DOWNLOAD_URL = poll_download_url(RECYCLING_BINS_DATASET_ID)
HAWKER_CENTRES_POLL_DOWNLOAD_URL = poll_download_url(HAWKER_CENTRES_DATASET_ID)
ZIKA_POLL_DOWNLOAD_URL = poll_download_url(ZIKA_DATASET_ID)
DENGUE_POLL_DOWNLOAD_URL = poll_download_url(DENGUE_DATASET_ID)
