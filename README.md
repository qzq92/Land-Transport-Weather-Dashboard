# Simple analytics enabled dashboard with (near) real-time information on weather, carpark and traffic conditions.

## Overview
This app is a multi-tab dashboard for Singapore that brings together weather, transport, and environmental data in one place.
It focuses on quick, readable summaries and interactive maps to explore nearby facilities and live conditions.

## Acknowledgement

### Data sources

All data are retrieved via API calls to data.gov.sg accessible [here](https://beta.data.gov.sg/). Key data sources involved are as follows:
1. **Weather Metrics**: Temperature, rainfall, relative humidity, and wind speed (V2 APIs)
2. **Environmental Alerts**: Lightning observations and flood alerts
3. **Exposure Indexes**: UV Index, WBGT (Wet-Bulb Globe Temperature), and PSI (Pollutant Standards Index) with multiple pollutants (PM2.5, PM10, SO₂, CO, O₃, NO₂)
4. **Health Clusters**: 
   - Zika cluster information (Data.gov.sg poll-download API)
   - Dengue cluster information (Data.gov.sg poll-download API)
5. **Transportation**: 
   - Bus stop locations (OneMap API)
   - Carpark availability (LTA DataMall CarParkAvailabilityv2 API)
   - HDB carpark information (Data.gov.sg initiate-download API)
   - Speed camera locations (Data.gov.sg initiate-download API)
   - Taxi availability (Data.gov.sg Taxi Availability API)
   - Traffic cameras (Data.gov.sg Traffic Images API)
   - ERP gantry locations (LTA Gantry GeoJSON dataset via Data.gov.sg initiate-download API)
   - Taxi stands (LTA DataMall TaxiStands API)
   - MRT/LRT service alerts (LTA DataMall TrainServiceAlerts API)
   - Faulty traffic lights (LTA DataMall FaultyTrafficLights API)
6. **Traffic**: Live traffic camera feeds at key locations

For developers, please refer to the link [here](https://guide.data.gov.sg/developers) on possible deprecation and updates on API and other information.


## Introduction
If you want a quick overview, see the screenshots section below. A more detailed feature breakdown follows.

## What does this app show

This analytics dashboard provides real-time information on:

### Main Dashboard
- **Average PSI Reading**: 24-hour average Pollutant Standards Index across all regions (calculated from regional averages)
- **Meteorological Alerts Section**: 
  - **Number of latest flood alerts**: Flood alert count displayed in standardized metric card format (updates every 3 minutes)
  - **Lightning observations (past 5 mins)**: Lightning detection count displayed in standardized metric card format
  - **Next 24-Hour Forecast**: Temperature, humidity, wind, and rain forecast
- **Traffic incident/ traffic light issues**: Traffic incidents and faulty traffic lights displayed in a grid format
- **MRT/LRT service alerts**: Real-time train service status and disruptions
- **Active Disease Clusters**: 
  - **Dengue clusters**: Count displayed in red-themed container
  - **Zika clusters**: Count displayed in red-themed container
- **Interactive Map**: Search locations and view nearby facilities (search bar positioned above map)
- **Map Toggle Controls**: 
  - **📍 Regional PSI Info**: Toggle visibility of PSI markers on map
  - **🌦️ Show 2H Forecast**: Toggle 2-hour weather forecast markers on map
- **Nearby Facilities**: Top 5 nearest MRT stations, bus stops, and HDB carparks with availability
- **Traffic Cameras**: Live CCTV feeds from land checkpoints
- **Standardized Card Design**: All right panel containers use consistent card-like design with headers and collapsible content
- **Layout**: Optimized 3:5:2 column ratio (left panel : map : right panel) with minimal gaps

### Realtime Weather Metrics Page
- **Live Weather Readings**: Temperature, rainfall, humidity, and wind speed from stations across Singapore
  - Temperature displays average value in sub-div
  - Lightning and flood readings display counts in sub-divs
- **WBGT (Wet-Bulb Globe Temperature)**: Heat stress measurements across Singapore with color-coded risk levels
  - Average WBGT value displayed in sub-div
  - Separate card from flood readings
- **Interactive Map**: Toggle visibility of different weather marker types
- **Status Indicators**: Lightning and flood alert indicators with color-coded status
- **View Sensor Location Tab**: Toggle visibility of weather sensor locations on map
  - Separate toggles for Flood and WBGT sensor locations

### Daily Health and Environmental Watch Page
- **UV Index**: Hourly trend visualization with line graph
- **Regional PSI Data**: Comprehensive pollutant readings including:
  - 24H Mean PSI, PM2.5, PM10, Sulphur Dioxide
  - 8H Mean Carbon Monoxide and Ozone
  - 1H Max Nitrogen Dioxide
- **PSI Display Modes**: Toggle between map text boxes and detailed metrics table
  - **Map View**: Regional pollutant data displayed as text boxes on map
  - **Table View**: Comprehensive table showing all PSI metrics with grid lines
- **Zika Clusters**: 
  - Polygon visualization of active Zika clusters on map
  - Toggle button: "Show Zika Cluster(s)" / "Don't Show Zika Cluster(s)"
  - Cluster information extracted from GeoJSON properties
- **Dengue Clusters**: 
  - Polygon visualization of active Dengue clusters on map
  - Toggle button: "Show Dengue Cluster(s)" / "Don't Show Dengue Cluster(s)"
  - Cluster count displayed on main dashboard
- **Interactive Map**: 
  - Standardized zoom level and boundaries across all pages
  - Average PSI value and category in region title
  - Color-coded pollutant values (PM values on left, others on right)
  - Full pollutant legend with color categories and thresholds
  - PSI color legend showing all risk levels
- **Toggle Controls**: All toggle buttons (PSI display mode, Zika clusters, Dengue clusters) positioned above map
- **Layout**: Optimized 2:6:2 ratio (indices panel : map : legend)

### Road & Transport Page
- **Taxi Availability**: Real-time taxi locations (4,500+ taxis) displayed as yellow markers on map
- **Traffic Cameras**: CCTV camera locations with live feed popups showing traffic conditions
- **ERP Gantries**: Electronic Road Pricing gantry locations displayed as red polylines on map
- **Taxi Stands**: Taxi stand locations with detailed information (name, barrier-free access, ownership, type)
- **MRT/LRT Line Operational Status**: Real-time status for all MRT and LRT lines
  - MRT lines displayed with official colors (NSL-red, EWL-green, CCL-yellow, DTL-blue, NEL-purple, TEL-brown)
  - LRT lines (Punggol, Sengkang, Bukit Panjang) displayed in grey
  - Operational status and disruption details for each line
- **Bus Stops**: Interactive bus stop markers with arrival time information
  - Bus stops displayed as clickable markers (visible at zoom level 15+)
  - Clicking a bus stop displays arrival times in side panel and highlights the stop on map
  - Bus stop selection persists when navigating the map (no auto-selection on viewport changes)
  - Re-center button available to return to selected bus stop location
  - Viewport filtering for optimal performance (only renders visible bus stops)
- **Toggle Controls**: Show/hide each transport layer independently
- **Metrics Display**: Standardized metric cards for bus stops and bus services counts
- **Zoomable Map**: Map supports zoom levels 10-19 for detailed exploration

## Application Structure

The dashboard consists of 4 main pages accessible via tabs with glossy black-to-silver gradient styling:

1. **🏠 Main Dashboard**: Overview with average PSI, meteorological alerts, traffic incidents, MRT/LRT service alerts, disease clusters, nearby facilities, and interactive map
   - **2-Hour Weather Forecast**: Toggle button on main page to show/hide 2-hour weather predictions with map markers
   - **Regional PSI Info**: Toggle button to show/hide PSI markers on map
   - **Standardized Card Design**: All right panel sections use consistent card-like design
2. **📡 Realtime Weather Metrics**: Live temperature, rainfall, humidity, and wind speed readings across Singapore
   - **WBGT Readings**: Heat stress measurements with average value display
   - **View Sensor Location Tab**: Toggle visibility of Flood and WBGT sensor locations
3. **📊 Daily Health and Environmental Watch**: UV Index trends, comprehensive PSI pollutant data, Zika clusters, and Dengue clusters
   - **PSI Display Modes**: Toggle between map text boxes and detailed metrics table
   - **Zika/Dengue Clusters**: Toggle visibility of cluster polygons on map
4. **🚦 Road & Transport**: Taxi availability, traffic cameras, ERP gantries, taxi stands, bus stops, and MRT/LRT operational status
   - **Bus Stop Interaction**: Click bus stops to view arrival times (zoom level 15+ required)
   - **Selection Persistence**: Selected bus stops remain active during map navigation
   - **Zoomable Map**: Supports zoom levels 10-19 for detailed exploration
5. **📍 Nearby Facilities**: Nearby bus stops, MRT/LRT stations, taxi stands, carparks, bicycle parking, and EV charging points

## Key Features

### Performance Optimizations
- **Async API Fetching**: All API calls use `@run_in_thread` decorator with ThreadPoolExecutor for parallel, non-blocking API requests
  - All fetch functions are async-only, using the `run_in_thread` decorator pattern
  - Flood alerts, lightning observations, weather data, and transport data fetched asynchronously
  - Zika and Dengue cluster data fetched asynchronously
  - Parallel coordinate processing for large cluster datasets (>10 features)
  - Consistent async pattern across all API calls for improved responsiveness and scalability
- **Data Caching**: 
  - PSI data cached for 60 seconds to minimize redundant API requests
  - ERP gantry data cached for 24 hours (static dataset)
  - Bus stops and bus routes data cached with monthly refresh buckets
  - Dataset caches for initiate-download API endpoints
- **Efficient Map Rendering**: 
  - Automatic map resize handling when switching between tabs and toggling sections
  - Viewport filtering for bus stops (only renders markers visible in current view)
  - Conditional marker rendering based on zoom level
- **Conditional Data Fetching**: 2H weather forecast only fetches data when section is visible
- **Startup Data Downloads**: 
  - HDB carpark information downloaded on startup (only if file doesn't exist)
  - Speed camera locations downloaded on startup (only if file doesn't exist)
  - Data stored in `data/` directory as CSV files

### Interactive Maps
- **Multi-layer Support**: Toggle visibility of different data layers (weather markers, transport facilities, taxis, cameras, ERP gantries, health clusters)
- **Standardized Configuration**: Consistent zoom levels, center coordinates, and boundaries across all pages
- **Location Search**: Search for any address in Singapore with autocomplete (white text on dark background)
- **Real-time Updates**: Auto-refresh every 30-60 seconds for live data (flood alerts update every 3 minutes)
- **Custom Markers**: Color-coded markers and polylines for different data types
- **Polygon Visualization**: Zika and Dengue clusters displayed as colored polygons on map
- **User-Controlled Selection**: Bus stop selection only changes on explicit user clicks, not on map navigation
- **Persistent Selection**: Selected bus stops remain active when panning/zooming the map

### Data Visualization
- **UV Index Trends**: Line graph showing hourly UV index throughout the day
- **Regional PSI Display**: 
  - **Map View**: Text boxes on map showing pollutant readings for each region
    - Region title includes average PSI value and category
    - Pollutant values color-coded based on WHO/EPA air quality standards
    - Two-column layout: PM values (left) and other pollutants (right)
  - **Table View**: Comprehensive metrics table with grid lines showing all PSI values
    - Reduced padding (2rem) for compact display
    - All values displayed in organized grid format
- **Health Cluster Visualization**: 
  - Zika clusters displayed as polygons with cluster information
  - Dengue clusters displayed as polygons with cluster counts
  - Cluster data extracted from GeoJSON properties via HTML parsing
- **Color-coded Risk Levels**: Visual indicators for air quality, heat stress, and environmental alerts
  - PSI categories: Good (green), Moderate (yellow), Unhealthy (orange), Very Unhealthy (red), Hazardous (purple)
  - Pollutant thresholds: Color-coded values for PM2.5, PM10, SO₂, CO, O₃, NO₂
- **Comprehensive Legends**: 
  - PSI color categories legend with source attribution
  - Pollutant color categories table with thresholds and source attribution
  - Legends fill vertical space of parent containers using flexbox
- **Live Camera Feeds**: Embedded traffic camera images in map popups
- **Responsive Styling**: All measurements use `rem` units for scalability across different screen sizes
- **Modern UI Design**:
  - Glossy navigation tabs with black-to-silver linear gradient (top to bottom)
  - Active tabs feature vibrant gradient colors (purple-blue gradient)
  - Consistent styling across all interactive elements
  - White text on dark backgrounds for improved readability
- **Standardized Metric Cards**: Reusable metric card component used across main dashboard, weather metrics, and transport pages
  - Consistent design pattern for all metric displays
  - Unified styling for count/value displays
  - Supports additional children (e.g., disclaimers) for context-specific information

## Known Limitations and Restrictions
### Bus Stop Visualization
- **Bus stop markers require zoom level 15+**: Bus stops are only displayed when zoomed in to level 15 or higher to optimize map performance and reduce visual clutter
- **Viewport filtering**: Only bus stops visible in the current map viewport are rendered, improving performance when zoomed out
- **Bus stop marker deviation**: Bus stop markers may deviate from actual locations due to ongoing road construction works (disclaimer shown when bus stops are displayed)

## Screenshots of app
All sample screenshots are stored in `assets/img` with `.jpg` extensions for clarity.

### Main Dashboard Page
![Main Dashboard](assets/img/main_page.jpg)
*Overview of key alerts, PSI, and the interactive map.*

### Realtime Weather Metrics Page
![Realtime Weather Metrics](assets/img/weather_metrics.jpg)
*Live weather readings across stations and sensor locations.*

### Daily Health and Environmental Watch Page
![Daily Health and Environmental Watch](assets/img/daily_health_env_watch.jpg)
*UV index trends, PSI details, and cluster overlays.*

### Road & Transport Page
![Road and Transport](assets/img/road_transport.jpg)
*Traffic, taxi, and transport layers on the map.*

### Nearby Facilities Page
![Nearby Facilities](assets/img/nearby_facilities.jpg)
*Top nearby transport options and parking facilities.*

## Built with following:
* [Dash](https://dash.plot.ly/) - Main server and interactive components 
* [Plotly Python](https://plot.ly/python/) - Used to create the interactive plots
* [Dash Leaflet](https://github.com/thedirtyfew/dash-leaflet) - Interactive map components with Leaflet.js
* [Dash DAQ](https://dash.plot.ly/dash-daq) - Styled technical components for industrial applications
* **ThreadPoolExecutor** - Async API fetching for improved performance and parallel data retrieval
* **@run_in_thread decorator** - Consistent async pattern using `run_in_thread` decorator from `utils.async_fetcher` for all API calls

### Supported by following APIs/tokens (you will need to register an account to get access tokens for use):

Please refer to the provided link for more information
* [Data.gov.sg API](https://beta.data.gov.sg/) - Primary data source for:
  - Weather data (V2 APIs): Temperature, rainfall, humidity, wind speed
  - Environmental alerts: Lightning observations, flood alerts
  - Exposure indexes: UV Index, WBGT, PSI with pollutants
  - Transport data: Taxi availability, traffic camera images
  - Health clusters: Zika and Dengue cluster information via poll-download API
* [LTA DataMall API Access](https://datamall.lta.gov.sg/content/datamall/en.html) - Transportation related data
  - Carpark availability: CarParkAvailabilityv2 API endpoint
  - Taxi stands: TaxiStands API endpoint
  - Train service alerts: TrainServiceAlerts API endpoint
  - Faulty traffic lights: FaultyTrafficLights API endpoint
  - Requires LTA DataMall API key
* [OneMap API](https://www.onemap.gov.sg/apidocs/) - Geospatial services:
  - Location search and geocoding
  - Nearby transport facilities (bus stops, MRT stations)
  - Map tiles for visualization (Night theme)
* [Data.gov.sg Initiate-Download API](https://api-open.data.gov.sg/v1/public/api/datasets/) - Dataset downloads:
  - HDB Carpark Information: Dataset ID `d_23f946fa557947f93a8043bbef41dd09`
  - Speed Camera Locations: Dataset ID `d_983804de2bc016f53e44031d85d1ec8a`
  - ERP Gantry Locations: Dataset ID `d_753090823cc9920ac41efaa6530c5893`
* [Data.gov.sg Poll-Download API](https://api-open.data.gov.sg/v1/public/api/datasets/) - Health cluster data:
  - Zika Clusters: Dataset ID `d_a3c783f11d79ff7feb8856f762ccf2c5`
  - Dengue Clusters: Dataset ID `d_dbfabf16158d1b0e1c420627c0819168`

## Requirements

### Python Dependencies

We suggest you to create an Anaconda environment using the requirements.yml file provided, and install all of the required dependencies listed within. In your Terminal/Command Prompt:

```bash
git clone https://github.com/plotly/Dash-sample-analytics-dashboard-concept.git
cd Dash-sample-analytics-dashboard-concept
conda create -f requirements.txt
```

If you prefer to install all of the required packages in your own Anaconda environment, simply activate your own Anaconda environment and execute the following command with your activated environment:

```bash
pip install -r requirements.txt
```

### Key Dependencies

- **dash**: Web framework for building interactive dashboards
- **dash-leaflet**: Interactive map components
- **plotly**: Data visualization and graphing
- **requests**: HTTP library for API calls
- **python-dotenv**: Environment variable management
- **pyproj**: Coordinate system transformations (SVY21 to WGS84)
- **pandas**: Data manipulation for carpark locations
- **numpy**: Numerical operations for UV Index graphing
- **concurrent.futures**: ThreadPoolExecutor for async API fetching (via `@run_in_thread` decorator)
- **gunicorn**: WSGI HTTP server for Plotly Cloud deployment

All required packages will be installed, and the app will be able to run.


## Environment Setup

Create a `.env` file in the root directory with the following API keys:

```env
# Data.gov.sg API key (required for weather, PSI, taxi, traffic camera, and health cluster data)
DATA_GOV_API=your_data_gov_api_key_here

# OneMap API key (required for location search and nearby facilities)
ONEMAP_API_KEY=your_onemap_api_key_here

# LTA DataMall API key (required for carpark availability)
LTA_API_KEY=your_lta_api_key_here
```

### Getting API Keys

1. **Data.gov.sg API Key**: 
   - Sign up at [Data.gov.sg](https://beta.data.gov.sg/)
   - Navigate to your account settings to generate an API key
   - Required for: Weather data, PSI, UV Index, WBGT, taxi availability, traffic cameras, Zika/Dengue clusters

2. **OneMap API Key**:
   - Register at [OneMap](https://www.onemap.gov.sg/)
   - Generate an API key from your account dashboard
   - Required for: Location search, nearby bus stops, MRT stations

3. **LTA DataMall API Key**:
   - Register at [LTA DataMall](https://datamall.lta.gov.sg/content/datamall/en.html)
   - Generate an API key from your account dashboard
   - Required for: Real-time carpark availability (CarParkAvailabilityv2 API)

## Using this application

### Local Development

Run this app locally by:
```
python app.py
```
Open http://0.0.0.0:8050/ in your browser, you will see an interactive dashboard.

### Plotly Cloud Deployment

The application is fully configured for Plotly Cloud deployment. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

**Quick Start:**

1. **Prepare Repository:**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Connect to Plotly Cloud:**
   - Sign up at [Plotly Cloud](https://plotly.com/)
   - Create new app → Connect to Git Repository
   - Select your repository and branch

3. **Set Environment Variables** (in Plotly Cloud app settings):
   - `DATA_GOV_API` - Your Data.gov.sg API key
   - `ONEMAP_API_KEY` - Your OneMap API key
   - `LTA_API_KEY` - Your LTA DataMall API key

4. **Deploy:**
   - Plotly Cloud will auto-detect the Dash app
   - Monitor build logs for any issues
   - App will be live at `https://your-app-name.plotly.com`

**Configuration:**
- ✅ `gunicorn` included in `requirements.txt`
- ✅ `server = app.server` exposed for WSGI compatibility
- ✅ `app.run()` only executes locally (`if __name__ == "__main__"`)
- ✅ All API calls use async `@run_in_thread` pattern

**Startup Behavior:**
On first deployment, the app automatically:
- Creates `data/` directory
- Downloads HDB carpark information (if file doesn't exist)
- Downloads speed camera locations (if file doesn't exist)
- Initializes OneMap API authentication
- Fetches and caches data from APIs using async pattern
- Updates displays every 30-60 seconds

**For detailed deployment guide, see [DEPLOYMENT.md](DEPLOYMENT.md)**
