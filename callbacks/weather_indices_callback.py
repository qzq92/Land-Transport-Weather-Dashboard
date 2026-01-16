"""
Callbacks for fetching and displaying realtime exposure indexes data.
Handles UV Index, WBGT, and other exposure indexes.

Uses ThreadPoolExecutor for async API fetching to improve performance.
"""
import math
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import plotly.graph_objects as go
import dash_leaflet as dl
import requests
from dash import html, dcc, Input, Output, State
from utils.async_fetcher import get_default_headers, fetch_url_2min_cached, _executor
from callbacks.transport_callback import fetch_taxi_availability
from components.metric_card import create_metric_value_display

# Thread pool for async exposure index fetching
_exposure_executor = ThreadPoolExecutor(max_workers=5)

# API URLs
PSI_URL = "https://api-open.data.gov.sg/v2/real-time/api/psi"
UV_URL = "https://api-open.data.gov.sg/v2/real-time/api/uv"
WBGT_URL = "https://api-open.data.gov.sg/v2/real-time/api/weather?api=wbgt"
ZIKA_DATASET_ID = "d_a3c783f11d79ff7feb8856f762ccf2c5"
ZIKA_POLL_DOWNLOAD_URL = f"https://api-open.data.gov.sg/v1/public/api/datasets/{ZIKA_DATASET_ID}/poll-download"
DENGUE_DATASET_ID = "d_dbfabf16158d1b0e1c420627c0819168"
DENGUE_POLL_DOWNLOAD_URL = f"https://api-open.data.gov.sg/v1/public/api/datasets/{DENGUE_DATASET_ID}/poll-download"

# Cache for PSI data to avoid redundant API calls
# Structure: {'data': <api_response>, 'timestamp': <time.time()>}
_psi_cache = {'data': None, 'timestamp': 0}
PSI_CACHE_TTL = 60  # Cache time-to-live in seconds


# PSI (Pollutant Standards Index) categories
PSI_CATEGORIES = [
    (0, 50, "#3ea72d", "Good"),
    (51, 100, "#fff300", "Moderate"),
    (101, 200, "#f18b00", "Unhealthy"),
    (201, 300, "#e53210", "Very Unhealthy"),
    (301, 999, "#b567a4", "Hazardous"),
]



# WBGT Heat Stress color coding
WBGT_CATEGORIES = [
    (0, 28, "#3ea72d", "Low"),           # Green - Low risk
    (28, 30, "#fff300", "Moderate"),     # Yellow - Moderate risk
    (30, 32, "#f18b00", "High"),         # Orange - High risk
    (32, 34, "#e53210", "Very High"),    # Red - Very high risk
    (34, 999, "#1a1a1a", "Extreme"),       # Black - Extreme risk
]

# Pollutant category thresholds (based on WHO/EPA standards)
# PM2.5 (24h average, µg/m³)
PM25_CATEGORIES = [
    (0, 15, "#3ea72d", "Good"),
    (15, 35, "#fff300", "Moderate"),
    (35, 55, "#f18b00", "Unhealthy"),
    (55, 150, "#e53210", "Very Unhealthy"),
    (150, 9999, "#b567a4", "Hazardous"),
]

# PM10 (24h average, µg/m³)
PM10_CATEGORIES = [
    (0, 45, "#3ea72d", "Good"),
    (45, 100, "#fff300", "Moderate"),
    (100, 200, "#f18b00", "Unhealthy"),
    (200, 300, "#e53210", "Very Unhealthy"),
    (300, 9999, "#b567a4", "Hazardous"),
]

# SO2 (24h average, µg/m³)
SO2_CATEGORIES = [
    (0, 20, "#3ea72d", "Good"),
    (20, 50, "#fff300", "Moderate"),
    (50, 125, "#f18b00", "Unhealthy"),
    (125, 250, "#e53210", "Very Unhealthy"),
    (250, 9999, "#b567a4", "Hazardous"),
]

# CO (8h average, mg/m³)
CO_CATEGORIES = [
    (0, 4, "#3ea72d", "Good"),
    (4, 9, "#fff300", "Moderate"),
    (9, 15, "#f18b00", "Unhealthy"),
    (15, 30, "#e53210", "Very Unhealthy"),
    (30, 9999, "#b567a4", "Hazardous"),
]

# O3 (8h average, µg/m³)
O3_CATEGORIES = [
    (0, 100, "#3ea72d", "Good"),
    (100, 160, "#fff300", "Moderate"),
    (160, 240, "#f18b00", "Unhealthy"),
    (240, 300, "#e53210", "Very Unhealthy"),
    (300, 9999, "#b567a4", "Hazardous"),
]

# NO2 (1h average, µg/m³)
NO2_CATEGORIES = [
    (0, 200, "#3ea72d", "Good"),
    (200, 400, "#fff300", "Moderate"),
    (400, 1000, "#f18b00", "Unhealthy"),
    (1000, 2000, "#e53210", "Very Unhealthy"),
    (2000, 9999, "#b567a4", "Hazardous"),
]




def get_psi_category(value):
    """Get PSI category info (color and label) based on value."""
    if value is None:
        return "#888", "Unknown"
    try:
        val = float(value)
    except (ValueError, TypeError):
        return "#888", "Unknown"
    for min_val, max_val, color, label in PSI_CATEGORIES:
        if min_val <= val <= max_val:
            return color, label
    return "#888", "Unknown"


def get_wbgt_category(value):
    """Get WBGT category info (color and label) based on value."""
    if value is None:
        return "#888", "Unknown"
    try:
        val = float(value)
    except (ValueError, TypeError):
        return "#888", "Unknown"
    for min_val, max_val, color, label in WBGT_CATEGORIES:
        if min_val <= val < max_val:
            return color, label
    # Check last category (extreme)
    if val >= 34:
        return "#b567a4", "Extreme"
    return "#888", "Unknown"


def get_pollutant_category(pollutant_key, value):
    """Get pollutant category info (color and label) based on value and pollutant type."""
    if value is None:
        return "#888", "Unknown"
    try:
        val = float(value)
    except (ValueError, TypeError):
        return "#888", "Unknown"

    # Select appropriate category thresholds based on pollutant type
    if pollutant_key == "pm25_twenty_four_hourly":
        categories = PM25_CATEGORIES
    elif pollutant_key == "pm10_twenty_four_hourly":
        categories = PM10_CATEGORIES
    elif pollutant_key == "so2_twenty_four_hourly":
        categories = SO2_CATEGORIES
    elif pollutant_key == "co_eight_hour_max":
        categories = CO_CATEGORIES
    elif pollutant_key == "o3_eight_hour_max":
        categories = O3_CATEGORIES
    elif pollutant_key == "no2_one_hour_max":
        categories = NO2_CATEGORIES
    else:
        return "#888", "Unknown"

    # Find matching category
    for min_val, max_val, color, label in categories:
        if min_val <= val <= max_val:
            return color, label
    return "#888", "Unknown"


# Pollutant units mapping
# SO₂, PM2.5, PM10, O₃, NO₂ are measured in µg/m³
# CO is measured in mg/m³
# PSI is an index (no unit)
POLLUTANT_UNITS = {
    "so2_twenty_four_hourly": "µg/m³",
    "pm25_twenty_four_hourly": "µg/m³",
    "pm10_twenty_four_hourly": "µg/m³",
    "o3_eight_hour_max": "µg/m³",
    "no2_one_hour_max": "µg/m³",
    "co_eight_hour_max": "mg/m³",
    "psi_twenty_four_hourly": "",  # PSI is an index, no unit
}


def _get_pollutant_unit(pollutant_key):
    """Get the unit of measurement for a pollutant."""
    return POLLUTANT_UNITS.get(pollutant_key, "")


def fetch_psi_data():
    """
    Fetch PSI data from Data.gov.sg API.
    Uses 2-minute in-memory caching aligned to system clock.
    """
    return fetch_url_2min_cached(PSI_URL, get_default_headers())


def fetch_psi_data_async():
    """
    Fetch PSI data asynchronously (returns Future).
    """
    return _executor.submit(fetch_url_2min_cached, PSI_URL, get_default_headers())


def fetch_uv_data():
    """
    Fetch UV index data from Data.gov.sg API.
    Uses 2-minute in-memory caching aligned to system clock.
    """
    return fetch_url_2min_cached(UV_URL, get_default_headers())


def fetch_uv_data_async():
    """
    Fetch UV data asynchronously (returns Future).
    """
    return _executor.submit(fetch_url_2min_cached, UV_URL, get_default_headers())


def fetch_wbgt_data():
    """
    Fetch WBGT data from Data.gov.sg API.
    Uses 2-minute in-memory caching aligned to system clock.
    """
    return fetch_url_2min_cached(WBGT_URL, get_default_headers())


def fetch_wbgt_data_async():
    """
    Fetch WBGT data asynchronously (returns Future).
    """
    return _executor.submit(fetch_url_2min_cached, WBGT_URL, get_default_headers())


def fetch_zika_cluster_data():
    """
    Fetch Zika cluster data from Data.gov.sg poll-download API.
    
    This function:
    1. Calls poll-download endpoint to get a URL
    2. Uses that URL to fetch the actual FeatureCollection data
    3. Returns the FeatureCollection data
    
    Returns:
        FeatureCollection data (dict) or None if error
    """
    try:
        # Step 1: Call poll-download to get the URL
        response = requests.get(ZIKA_POLL_DOWNLOAD_URL, timeout=30)
        response.raise_for_status()
        poll_response = response.json()
        
        # Step 2: Extract URL from response
        # The response structure may be: {"url": "..."} or {"data": {"url": "..."}}
        download_url = None
        if isinstance(poll_response, dict):
            if 'url' in poll_response:
                download_url = poll_response['url']
            elif 'data' in poll_response and isinstance(poll_response['data'], dict):
                download_url = poll_response['data'].get('url')
        
        if not download_url:
            print(f"No URL found in poll-download response: {poll_response}")
            return None
        
        # Step 3: Fetch the actual data from the URL
        data_response = requests.get(download_url, timeout=30)
        data_response.raise_for_status()
        return data_response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Zika cluster data: {e}")
        return None


def fetch_dengue_cluster_data():
    """
    Fetch Dengue cluster data from Data.gov.sg poll-download API.
    
    This function:
    1. Calls poll-download endpoint to get a URL
    2. Uses that URL to fetch the actual FeatureCollection data
    3. Returns the FeatureCollection data
    
    Returns:
        FeatureCollection data (dict) or None if error
    """
    try:
        # Step 1: Call poll-download to get the URL
        response = requests.get(DENGUE_POLL_DOWNLOAD_URL, timeout=30)
        response.raise_for_status()
        poll_response = response.json()
        
        # Step 2: Extract URL from response
        # The response structure may be: {"url": "..."} or {"data": {"url": "..."}}
        download_url = None
        if isinstance(poll_response, dict):
            if 'url' in poll_response:
                download_url = poll_response['url']
            elif 'data' in poll_response and isinstance(poll_response['data'], dict):
                download_url = poll_response['data'].get('url')
        
        if not download_url:
            print(f"No URL found in poll-download response: {poll_response}")
            return None
        
        # Step 3: Fetch the actual data from the URL
        data_response = requests.get(download_url, timeout=30)
        data_response.raise_for_status()
        return data_response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Dengue cluster data: {e}")
        return None


def fetch_zika_cluster_data_async():
    """
    Fetch Zika cluster data asynchronously (returns Future).
    Call .result() to get the data when needed.
    """
    return _exposure_executor.submit(fetch_zika_cluster_data)


def fetch_dengue_cluster_data_async():
    """
    Fetch Dengue cluster data asynchronously (returns Future).
    Call .result() to get the data when needed.
    """
    return _exposure_executor.submit(fetch_dengue_cluster_data)


def _parse_timestamp(timestamp_str):
    """Parse ISO timestamp string to formatted string."""
    if not timestamp_str:
        return ""
    try:
        if "." in timestamp_str:
            parsed = datetime.fromisoformat(
                timestamp_str.replace("Z", "+00:00")
            )
        else:
            parsed = datetime.fromisoformat(timestamp_str)
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return timestamp_str




def _create_uv_chart(index_data):
    """Create UV index line chart using numpy and plotly."""
    times = []
    values = []

    # Sort chronologically
    sorted_data = sorted(index_data, key=lambda x: x.get('hour', ''))

    for item in sorted_data:
        ts_str = item.get('hour', '')
        val = item.get('value', 0)
        if ts_str:
            try:
                if "." in ts_str:
                    date_obj = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                else:
                    date_obj = datetime.fromisoformat(ts_str)
                times.append(date_obj)
                values.append(val)
            except (ValueError, TypeError):
                continue

    # Convert to numpy arrays as requested
    x_data = np.array(times)
    y_data = np.array(values)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode='lines+markers',
        name='UV Index',
        line=dict(color='#f18b00', width=2),
        marker=dict(size=6, color='#fff300', line=dict(width=1, color='#333')),
        hovertemplate='%{x|%H:%M}<br>UV Index: %{y}<extra></extra>'
    ))

    fig.update_layout(
        margin=dict(l=30, r=20, t=20, b=20),
        height=220,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ccc', size=10),
        xaxis=dict(
            showgrid=False,
            tickformat='%H:%M',
            linecolor='#555',
            showline=True
        ),
        yaxis=dict(
            title='UV Index',
            showgrid=True,
            gridcolor='#444',
            zeroline=False,
            rangemode='tozero'
        )
    )

    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False},
        style={'width': '100%'}
    )




def format_uv_display(data):
    """Format UV data for display."""
    if not data or data.get("code") != 0:
        return html.P(
            "Error retrieving UV data",
            style={"color": "#ff6b6b", "textAlign": "center"}
        )

    records = data.get("data", {}).get("records", [])
    if not records:
        return html.P(
            "No UV data available",
            style={"color": "#ccc", "textAlign": "center"}
        )

    record = records[0]
    index_data = record.get("index", [])
    update_time_str = _parse_timestamp(record.get("updatedTimestamp", ""))

    if not index_data:
        return html.P(
            "No UV readings available",
            style={"color": "#ccc", "textAlign": "center"}
        )

    uv_chart = _create_uv_chart(index_data)

    return html.Div(
        children=[
            html.Div(
                style={
                    "backgroundColor": "#3a4a5a",
                    "borderRadius": "6px",
                    "padding": "5px",
                    "overflow": "hidden",
                },
                children=[uv_chart]
            ),
            html.Div(
                f"Updated: {update_time_str}",
                style={
                    "textAlign": "center",
                    "color": "#888",
                    "fontSize": "11px",
                    "marginTop": "10px",
                    "fontStyle": "italic",
                }
            ),
        ]
    )


def _build_pollutant_row_html(pollutant_key, pollutant_name, value):
    """Build HTML for a single pollutant row with unit."""
    unit = _get_pollutant_unit(pollutant_key)
    value_with_unit = f"{value} {unit}" if unit else str(value)

    if pollutant_key == "psi_twenty_four_hourly":
        color, category = get_psi_category(value)
        return (
            f'<div style="margin: 2px 0;">'
            f'{pollutant_name}: '
            f'<span style="color:{color};font-weight:bold;">{value}</span> '
            f'({category})'
            f'</div>'
        )
    return f'<div style="margin: 2px 0;">{pollutant_name}: {value_with_unit}</div>'


def _create_single_psi_marker(region_info, readings, pollutants):
    """Create a single PSI text box for a region."""
    region_name = region_info.get("name", "")
    label_location = region_info.get("labelLocation", {})
    lat = label_location.get("latitude")
    lon = label_location.get("longitude")

    if not lat or not lon or not region_name:
        return None

    # Get 24H PSI value and category for the title
    psi_value = readings.get("psi_twenty_four_hourly", {}).get(region_name)
    psi_color = "#60a5fa"  # Default blue color
    if psi_value is not None:
        psi_color, psi_category = get_psi_category(psi_value)
        psi_title = (f"{region_name.upper()} (24H Avg PSI: "
                    f'<span style="color: {psi_color};">{psi_value}</span> '
                    f"({psi_category}))")
    else:
        psi_title = region_name.upper()

    # Separate pollutants into PM (left) and others (right)
    pm_pollutants = []  # PM2.5, PM10
    other_pollutants = []  # SO2, CO, O3, NO2 (PSI excluded, shown in title)

    for pollutant_key, pollutant_name in pollutants:
        # Skip PSI as it's shown in the title
        if pollutant_key == "psi_twenty_four_hourly":
            continue

        value = readings.get(pollutant_key, {}).get(region_name)
        if value is not None:
            unit = _get_pollutant_unit(pollutant_key)

            # Get color category for pollutant
            color, _ = get_pollutant_category(pollutant_key, value)

            # Categorize pollutants (store value and unit separately for color coding)
            if pollutant_key in ["pm25_twenty_four_hourly", "pm10_twenty_four_hourly"]:
                pm_pollutants.append((pollutant_name, value, unit, color))
            else:
                other_pollutants.append((pollutant_name, value, unit, color))

    # Build left column (PM pollutants) as bulleted list
    # Only color-code the numeric value, not the entire line
    pm_list_items = "".join([
        f'<li style="margin: 2px 0; font-size: 10px; color: #fff;">'
        f'{name}: <span style="color: {color if color else "#fff"}; '
        f'font-weight: bold;">{val}</span>'
        f'{f" {unit}" if unit else ""}</li>'
        for name, val, unit, color in pm_pollutants
    ])
    ul_style = 'margin: 0; padding-left: 18px; list-style-type: disc;'
    pm_column = (f'<ul style="{ul_style}">{pm_list_items}</ul>'
                 if pm_pollutants else f'<ul style="{ul_style}"></ul>')

    # Build right column (other pollutants) as bulleted list
    # Only color-code the numeric value, not the entire line
    other_list_items = "".join([
        f'<li style="margin: 2px 0; font-size: 10px; color: #fff;">'
        f'{name}: <span style="color: {color if color else "#fff"}; '
        f'font-weight: bold;">{val}</span>'
        f'{f" {unit}" if unit else ""}</li>'
        for name, val, unit, color in other_pollutants
    ])
    other_column = (f'<ul style="{ul_style}">{other_list_items}</ul>'
                    if other_pollutants else f'<ul style="{ul_style}"></ul>')

    # Create text box HTML with two columns
    text_box_html = f'''
        <div style="
            background-color: rgba(74, 90, 106, 0.95);
            border: 2px solid #60a5fa;
            border-radius: 8px;
            padding: 8px 10px;
            min-width: 200px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        ">
            <div style="
                font-weight: bold;
                font-size: 11px;
                color: #60a5fa;
                margin-bottom: 6px;
                text-align: center;
                border-bottom: 1px solid #60a5fa;
                padding-bottom: 3px;
            ">{psi_title}</div>
            <div style="
                display: flex;
                gap: 12px;
                font-size: 10px;
                color: #fff;
                line-height: 1.4;
            ">
                <div style="flex: 1;">{pm_column}</div>
                <div style="flex: 1;">{other_column}</div>
            </div>
        </div>
    '''

    return dl.DivMarker(
        id=f"psi-{region_name}",
        position=[lat, lon],
        iconOptions={
            'className': 'psi-textbox',
            'html': text_box_html,
            'iconSize': [220, 180],
            'iconAnchor': [110, 90],
        }
    )


def create_simple_psi_marker(region_info, readings):
    """Create a simplified PSI marker showing only 24h PSI value."""
    region_name = region_info.get("name", "")
    label_location = region_info.get("labelLocation", {})
    lat = label_location.get("latitude")
    lon = label_location.get("longitude")

    if not lat or not lon or not region_name:
        return None

    # Get 24H PSI value and category
    psi_value = readings.get("psi_twenty_four_hourly", {}).get(region_name)
    psi_color = "#60a5fa"  # Default blue color
    if psi_value is not None:
        psi_color, psi_category = get_psi_category(psi_value)
        psi_text = f"{region_name.upper()}<br/>24H PSI: <span style='color: {psi_color}; font-weight: bold;'>{psi_value}</span><br/>({psi_category})"
    else:
        psi_text = f"{region_name.upper()}<br/>24H PSI: N/A"

    # Create simplified text box HTML with only PSI value
    text_box_html = f'''
        <div style="
            background-color: rgba(74, 90, 106, 0.95);
            border: 2px solid {psi_color};
            border-radius: 8px;
            padding: 8px 10px;
            min-width: 120px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            text-align: center;
        ">
            <div style="
                font-weight: bold;
                font-size: 12px;
                color: #fff;
                line-height: 1.4;
            ">{psi_text}</div>
        </div>
    '''

    return dl.DivMarker(
        id=f"main-psi-{region_name}",
        position=[lat, lon],
        iconOptions={
            'className': 'main-psi-textbox',
            'html': text_box_html,
            'iconSize': [140, 80],
            'iconAnchor': [70, 40],
        }
    )


def create_main_psi_markers(data):
    """Create simplified PSI markers for main page showing only 24h PSI."""
    if not data or data.get("code") != 0:
        return []

    items = data.get("data", {}).get("items", [])
    region_metadata = data.get("data", {}).get("regionMetadata", [])

    if not items or not region_metadata:
        return []

    readings = items[0].get("readings", {})

    markers = [
        create_simple_psi_marker(region_info, readings)
        for region_info in region_metadata
    ]
    return [m for m in markers if m is not None]


def create_psi_markers(data):
    """Create map markers for PSI regions with pollutant data in tooltips."""
    if not data or data.get("code") != 0:
        return []

    items = data.get("data", {}).get("items", [])
    region_metadata = data.get("data", {}).get("regionMetadata", [])

    if not items or not region_metadata:
        return []

    readings = items[0].get("readings", {})
    pollutants = [
        ("psi_twenty_four_hourly", "PSI (24H Avg)"),
        ("pm25_twenty_four_hourly", "PM2.5 (24H Avg)"),
        ("pm10_twenty_four_hourly", "PM10 (24H Avg)"),
        ("so2_twenty_four_hourly", "SO₂ (Max 24H Avg)"),
        ("co_eight_hour_max", "CO (Max 8H Avg)"),
        ("o3_eight_hour_max", "O₃ (Max 8H Avg)"),
        ("no2_one_hour_max", "NO₂ (Max 1H)")
    ]

    markers = [
        _create_single_psi_marker(region_info, readings, pollutants)
        for region_info in region_metadata
    ]
    return [m for m in markers if m is not None]


def format_psi_display(data):
    """Format PSI data as a table with regions as rows and pollutants as columns."""
    if not data or data.get("code") != 0:
        return html.P(
            "Error retrieving PSI data",
            style={"color": "#ff6b6b", "textAlign": "center"}
        )

    items = data.get("data", {}).get("items", [])
    if not items:
        return html.P(
            "No PSI data available",
            style={"color": "#ccc", "textAlign": "center"}
        )

    readings = items[0].get("readings", {})
    update_time_str = _parse_timestamp(items[0].get("updatedTimestamp", ""))

    # Define pollutants and regions
    pollutants = [
        ("psi_twenty_four_hourly", "24H Mean PSI"),
        ("pm25_twenty_four_hourly", "24H Mean PM2.5 Particulate Matter"),
        ("pm10_twenty_four_hourly", "24H Mean PM10 Particulate Matter"),
        ("so2_twenty_four_hourly", "24H Mean Sulphur Dioxide"),
        ("co_eight_hour_max", "8H Mean Carbon Monoxide"),
        ("o3_eight_hour_max", "8H Mean Ozone"),
        ("no2_one_hour_max", "1H Max Nitrogen Dioxide")
    ]
    regions = ["north", "south", "east", "west", "central"]

    # Create table header
    header_row = html.Div(
        style={
            "display": "grid",
            "gridTemplateColumns": "70px repeat(7, 1fr)",
            "gap": "0",
            "padding": "0.5rem",
            "backgroundColor": "#2a3a4a",
            "borderRadius": "0.25rem 0.25rem 0 0",
            "fontWeight": "bold",
            "border": "0.0625rem solid #5a6a7a",
            "borderBottom": "0.125rem solid #60a5fa",
        },
        children=[
            html.Div("Region", style={
                "fontSize": "0.5625rem",
                "color": "#60a5fa",
                "textAlign": "center",
                "borderRight": "0.0625rem solid #5a6a7a",
                "paddingRight": "0.25rem",
            })
        ] + [
            html.Div(name, style={
                "fontSize": "0.5625rem",
                "color": "#60a5fa",
                "textAlign": "center",
                "borderRight": "0.0625rem solid #5a6a7a" if i < len(pollutants) - 1 else "none",
                "paddingRight": "0.25rem" if i < len(pollutants) - 1 else "0",
            })
            for i, (_, name) in enumerate(pollutants)
        ]
    )

    # Create table rows for each region
    table_rows = []
    for region in regions:
        cells = [
            html.Div(
                region.capitalize(),
                style={
                    "fontSize": "10px",
                    "color": "#ccc",
                    "textAlign": "center",
                    "fontWeight": "600"
                }
            )
        ]

        # Add cell for each pollutant
        for pollutant_key, _ in pollutants:
            pollutant_data = readings.get(pollutant_key, {})
            value = pollutant_data.get(region)

            if value is not None:
                # Color code PSI values, use blue for others
                if pollutant_key == "psi_twenty_four_hourly":
                    color, _ = get_psi_category(value)
                else:
                    color = "#60a5fa"

                # Get unit for pollutant
                unit = _get_pollutant_unit(pollutant_key)
                display_value = f"{value} {unit}" if unit else str(value)

                cells.append(
                    html.Div(
                        display_value,
                        style={
                            "fontSize": "10px",
                            "color": color,
                            "textAlign": "center",
                            "fontWeight": "bold"
                        }
                    )
                )
            else:
                cells.append(
                    html.Div(
                        "-",
                        style={
                            "fontSize": "10px",
                            "color": "#666",
                            "textAlign": "center"
                        }
                    )
                )

        # Add border styles to each cell
        styled_cells = []
        for i, cell in enumerate(cells):
            # Get existing styles from cell if it's a Div
            if isinstance(cell, html.Div):
                existing_style = cell.style if hasattr(cell, 'style') else {}
                existing_style.update({
                    "borderRight": "0.0625rem solid #5a6a7a" if i < len(cells) - 1 else "none",
                    "paddingRight": "0.25rem" if i < len(cells) - 1 else "0",
                })
                # Create new Div with updated styles
                styled_cells.append(
                    html.Div(
                        cell.children if hasattr(cell, 'children') else cell,
                        style=existing_style
                    )
                )
            else:
                # If it's a string, create a Div
                styled_cells.append(
                    html.Div(
                        cell,
                        style={
                            "fontSize": "0.625rem",
                            "color": "#ccc",
                            "textAlign": "center",
                            "fontWeight": "600",
                            "borderRight": "0.0625rem solid #5a6a7a" if i < len(cells) - 1 else "none",
                            "paddingRight": "0.25rem" if i < len(cells) - 1 else "0",
                        }
                    )
                )
        
        table_rows.append(
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "70px repeat(7, 1fr)",
                    "gap": "0",
                    "padding": "0.5rem",
                    "backgroundColor": "#3a4a5a",
                    "borderBottom": "0.0625rem solid #5a6a7a",
                    "borderLeft": "0.0625rem solid #5a6a7a",
                    "borderRight": "0.0625rem solid #5a6a7a",
                },
                children=styled_cells
            )
        )

    return html.Div(
        style={
            "padding": "2rem",
        },
        children=[
            html.Div(
                style={
                    "backgroundColor": "#3a4a5a",
                    "borderRadius": "0.375rem",
                    "overflow": "hidden",
                    "border": "0.0625rem solid #5a6a7a",
                },
                children=[header_row] + table_rows
            ),
            html.Div(
                f"Updated: {update_time_str}",
                style={
                    "textAlign": "center",
                    "color": "#888",
                    "fontSize": "0.6875rem",
                    "marginTop": "0.625rem",
                    "fontStyle": "italic",
                }
            )
        ]
    )


def _create_wbgt_row(name, wbgt, heat_stress):
    """Create a single WBGT reading row."""
    color, _ = get_wbgt_category(wbgt)

    return html.Div(
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "4px 8px",
            "backgroundColor": "#3a4a5a",
            "borderRadius": "4px",
            "marginBottom": "4px",
        },
        children=[
            html.Span(
                name,
                style={
                    "fontSize": "11px",
                    "color": "#ccc",
                    "flex": "1",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "whiteSpace": "nowrap",
                    "marginRight": "10px",
                }
            ),
            html.Span(
                style={"display": "flex", "alignItems": "center", "gap": "8px"},
                children=[
                    html.Span(
                        heat_stress,
                        style={
                            "color": color,
                            "fontSize": "11px",
                            "fontWeight": "500",
                        }
                    ),
                    html.Span(
                        f"{wbgt}°C",
                        style={
                            "color": "#fff",
                            "fontWeight": "600",
                            "fontSize": "12px",
                            "minWidth": "50px",
                            "textAlign": "right",
                        }
                    ),
                ]
            ),
        ]
    )


def format_wbgt_display(data):
    """Format WBGT data for display."""
    # Check if data is None or empty dict
    if not data:
        return html.P(
            "Error retrieving WBGT data",
            style={"color": "#ff6b6b", "textAlign": "center"}
        )

    # Handle case where code might be missing or different
    if data.get("code") not in [0, 1]:
        print(f"WBGT API Error Code: {data.get('code')}")
        return html.P(
            f"Error retrieving WBGT data (Code: {data.get('code')})",
            style={"color": "#ff6b6b", "textAlign": "center"}
        )

    records = data.get("data", {}).get("records", [])
    if not records:
        return html.P(
            "No WBGT data available",
            style={"color": "#ccc", "textAlign": "center"}
        )

    record = records[0]
    item = record.get("item", {})
    readings = item.get("readings", [])
    update_time_str = _parse_timestamp(record.get("updatedTimestamp", ""))

    if not readings:
        return html.P(
            "No WBGT readings available",
            style={"color": "#ccc", "textAlign": "center"}
        )

    # Sort readings alphabetically by station name
    sorted_readings = sorted(
        readings,
        key=lambda x: x.get("station", {}).get("name", "")
    )

    wbgt_rows = [
        _create_wbgt_row(
            r.get("station", {}).get("name", "Unknown"),
            r.get("wbgt", "N/A"),
            r.get("heatStress", "Unknown")
        )
        for r in sorted_readings
    ]

    return html.Div(
        children=[
            html.Div(
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "flex": "1",
                    "overflowY": "auto",
                    "overflowX": "hidden",
                    "minHeight": "0",
                },
                children=wbgt_rows
            ),
            html.Div(
                f"Updated: {update_time_str}",
                style={
                    "textAlign": "center",
                    "color": "#888",
                    "fontSize": "11px",
                    "marginTop": "10px",
                    "fontStyle": "italic",
                    "flexShrink": "0",
                }
            ),
        ],
        style={
            "display": "flex",
            "flexDirection": "column",
            "height": "100%",
            "overflow": "hidden",
        }
    )


def _create_single_wbgt_marker(reading):
    """Create a single WBGT map marker from reading data."""
    location = reading.get("location", {})
    # API response uses 'latitude' and 'longtitude' (typo in API)
    lat = location.get("latitude")
    lon = location.get("longtitude")  # Handle API typo

    # If not found, try correct spelling just in case API gets fixed
    if lon is None:
        lon = location.get("longitude")

    if not lat or not lon:
        return None

    try:
        lat, lon = float(lat), float(lon)
    except (ValueError, TypeError):
        return None

    station = reading.get("station", {})
    name = station.get("name", "Unknown")
    wbgt = reading.get("wbgt", "N/A")
    heat_stress = reading.get("heatStress", "Unknown")
    color, _ = get_wbgt_category(wbgt)

    return dl.DivMarker(
        id=f"wbgt-{station.get('id', 'unknown')}",
        position=[lat, lon],
        iconOptions={
            "className": "wbgt-marker",
            "html": f'''
                <div style="
                    background-color: {color};
                    width: 14px;
                    height: 14px;
                    border-radius: 50%;
                    border: 2px solid white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                "></div>
            ''',
            "iconSize": [14, 14],
            "iconAnchor": [7, 7],
        },
        children=[
            dl.Tooltip(
                f"{name}: {wbgt}°C ({heat_stress})",
                permanent=False,
                direction="top"
            )
        ]
    )


def create_wbgt_markers(data):
    """Create map markers for WBGT stations."""
    if not data or data.get("code") != 0:
        return []

    records = data.get("data", {}).get("records", [])
    if not records:
        return []

    readings = records[0].get("item", {}).get("readings", [])
    markers = [_create_single_wbgt_marker(r) for r in readings]
    return [m for m in markers if m is not None]


def _parse_zika_description(description_html):
    """
    Parse Zika cluster Description HTML to extract attributes.
    
    Args:
        description_html: HTML string containing table with attributes
    
    Returns:
        Dictionary with extracted attributes (CASE_SIZE, CLUSTER_ID, LOCALITY, etc.)
    """
    if not description_html:
        return {}
    
    result = {}
    
    # Extract CASE_SIZE
    case_size_match = re.search(r'<th>CASE_SIZE</th>\s*<td>(\d+)</td>', description_html)
    if case_size_match:
        result['CASE_SIZE'] = int(case_size_match.group(1))
    
    # Extract CLUSTER_ID
    cluster_id_match = re.search(r'<th>CLUSTER_ID</th>\s*<td>([^<]+)</td>', description_html)
    if cluster_id_match:
        result['CLUSTER_ID'] = cluster_id_match.group(1).strip()
    
    # Extract LOCALITY
    locality_match = re.search(r'<th>LOCALITY</th>\s*<td>([^<]+)</td>', description_html)
    if locality_match:
        result['LOCALITY'] = locality_match.group(1).strip()
    
    # Extract NAME
    name_match = re.search(r'<th>NAME</th>\s*<td>([^<]+)</td>', description_html)
    if name_match:
        name = name_match.group(1).strip()
        if name:  # Only add if not empty
            result['NAME'] = name
    
    return result


def _process_single_zika_feature(feature):
    """
    Process a single Zika feature to create a polygon.
    This function is designed to be called in parallel.
    
    Args:
        feature: Single feature from FeatureCollection
    
    Returns:
        dl.Polygon object or None if invalid
    """
    try:
        # Handle FeatureCollection format (GeoJSON)
        if feature.get('type') == 'Feature':
            geometry = feature.get('geometry', {})
            properties = feature.get('properties', {})
        else:
            # Fallback to old format
            geometry = feature.get('geometry', {})
            properties = feature
        
        # Extract polygon coordinates from geometry
        polygon_coords = None
        if geometry and 'coordinates' in geometry:
            polygon_coords = geometry['coordinates']
        elif 'coordinates' in feature:
            polygon_coords = feature['coordinates']
        elif 'polygon' in feature:
            polygon_coords = feature['polygon']
        
        if not polygon_coords:
            return None
        
        # Flatten nested arrays if needed
        if isinstance(polygon_coords[0][0], list):
            if isinstance(polygon_coords[0][0][0], list):
                coords = polygon_coords[0][0]
            else:
                coords = polygon_coords[0]
        else:
            coords = polygon_coords
        
        # Convert to [lat, lon] format for Leaflet using list comprehension
        # Handle 3D coordinates [lon, lat, 0] or 2D [lon, lat]
        leaflet_coords = []
        for coord in coords:
            if len(coord) >= 2:
                lon, lat = coord[0], coord[1]
                # Check if it's actually lat, lon by checking if lat is reasonable for Singapore
                if lat > 90 or lat < -90:
                    lat, lon = coord[0], coord[1]
                leaflet_coords.append([lat, lon])
        
        if len(leaflet_coords) < 3:
            return None  # Need at least 3 points for a polygon
        
        # Parse Description HTML to extract cluster information
        description_html = properties.get('Description', '')
        parsed_attrs = _parse_zika_description(description_html)
        
        # Get cluster information from parsed attributes or properties
        cluster_name = (
            parsed_attrs.get('LOCALITY') or
            parsed_attrs.get('NAME') or
            properties.get('LOCALITY') or
            properties.get('Name') or
            properties.get('cluster') or
            properties.get('name') or
            properties.get('location') or
            'Zika Cluster'
        )
        
        cases = (
            parsed_attrs.get('CASE_SIZE') or
            properties.get('CASE_SIZE') or
            properties.get('cases') or
            properties.get('case_count') or
            properties.get('num_cases') or
            ''
        )
        
        cluster_id = (
            parsed_attrs.get('CLUSTER_ID') or
            properties.get('CLUSTER_ID') or
            ''
        )
        
        # Create tooltip text
        tooltip_text = f"{cluster_name}"
        if cluster_id:
            tooltip_text += f" (ID: {cluster_id})"
        if cases:
            tooltip_text += f" - {cases} case{'s' if cases != 1 else ''}"
        
        # Create polygon with red color for Zika clusters
        return dl.Polygon(
            positions=leaflet_coords,
            color="#ff4444",
            fillColor="#ff6666",
            fillOpacity=0.3,
            weight=2,
            children=[
                dl.Tooltip(tooltip_text)
            ]
        )
    except (ValueError, TypeError, IndexError) as e:
        print(f"Error processing Zika feature: {e}")
        return None


def create_zika_cluster_polygons(data):
    """
    Create polygon markers for Zika clusters from poll-download API data.
    Uses parallel processing for better performance.
    """
    if not data:
        return []
    
    # Handle FeatureCollection format (GeoJSON)
    features = []
    if isinstance(data, dict):
        if 'features' in data:
            # FeatureCollection format
            features = data['features']
        elif 'data' in data and 'records' in data['data']:
            features = data['data']['records']
        elif 'records' in data:
            features = data['records']
        elif 'result' in data and 'records' in data['result']:
            features = data['result']['records']
    
    if not features:
        return []
    
    # Process features in parallel using ThreadPoolExecutor
    # For small datasets, sequential might be faster, but for large ones, parallel helps
    if len(features) > 10:
        # Use parallel processing for larger datasets
        futures = [_exposure_executor.submit(_process_single_zika_feature, feature) for feature in features]
        polygons = [future.result() for future in futures]
        # Filter out None values
        return [p for p in polygons if p is not None]
    
    # Sequential processing for small datasets (less overhead)
    polygons = []
    for feature in features:
        polygon = _process_single_zika_feature(feature)
        if polygon:
            polygons.append(polygon)
    return polygons


def format_zika_clusters_display(data):
    """Format Zika cluster data for display."""
    if not data:
        return html.P(
            "Error retrieving Zika cluster data",
            style={"color": "#ff6b6b", "textAlign": "center"}
        )
    
    # Handle FeatureCollection format (GeoJSON) or old format
    features = []
    if isinstance(data, dict):
        #print(f"Zika data: {data}")
        if 'features' in data:
            # FeatureCollection format
            features = data['features']
        elif 'data' in data and 'records' in data['data']:
            features = data['data']['records']
        elif 'records' in data:
            features = data['records']
        elif 'result' in data and 'records' in data['result']:
            features = data['result']['records']
    
    if not features:
        return html.P(
            "No Zika cluster data available",
            style={"color": "#ccc", "textAlign": "center"}
        )
    
    # Create list of clusters
    cluster_items = []
    for feature in features:
        # Handle FeatureCollection format
        if feature.get('type') == 'Feature':
            properties = feature.get('properties', {})
        else:
            properties = feature
        
        # Parse Description HTML to extract cluster information
        description_html = properties.get('Description', '')
        parsed_attrs = _parse_zika_description(description_html)
        
        # Get cluster information from parsed attributes or properties
        cluster_name = (
            parsed_attrs.get('LOCALITY') or
            parsed_attrs.get('NAME') or
            properties.get('LOCALITY') or
            properties.get('Name') or
            properties.get('cluster') or
            properties.get('name') or
            properties.get('location') or
            'Unknown'
        )
        
        cases = (
            parsed_attrs.get('CASE_SIZE') or
            properties.get('CASE_SIZE') or
            properties.get('cases') or
            properties.get('case_count') or
            properties.get('num_cases') or
            'N/A'
        )
        
        cluster_items.append(
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "padding": "0.25rem 0.5rem",
                    "backgroundColor": "#3a4a5a",
                    "borderRadius": "0.25rem",
                    "marginBottom": "0.25rem",
                },
                children=[
                    html.Span(
                        cluster_name,
                        style={
                            "fontSize": "0.6875rem",
                            "color": "#ccc",
                            "flex": "1",
                        }
                    ),
                    html.Span(
                        f"{cases} case{'s' if cases != 1 else ''}" if cases != 'N/A' else "N/A",
                        style={
                            "fontSize": "0.6875rem",
                            "color": "#ff6666",
                            "fontWeight": "600",
                        }
                    ),
                ]
            )
        )
    
    return html.Div(
        children=cluster_items,
        style={
            "display": "flex",
            "flexDirection": "column",
            "flex": "1",
            "overflowY": "auto",
            "overflowX": "hidden",
            "minHeight": "0",
        }
    )


def _process_single_dengue_feature(feature):
    """
    Process a single Dengue feature to create a polygon.
    This function is designed to be called in parallel.
    
    Args:
        feature: Single feature from FeatureCollection
    
    Returns:
        dl.Polygon object or None if invalid
    """
    try:
        # Handle FeatureCollection format (GeoJSON)
        if feature.get('type') == 'Feature':
            geometry = feature.get('geometry', {})
            properties = feature.get('properties', {})
        else:
            # Fallback to old format
            geometry = feature.get('geometry', {})
            properties = feature
        
        # Extract polygon coordinates from geometry
        polygon_coords = None
        if geometry and 'coordinates' in geometry:
            polygon_coords = geometry['coordinates']
        elif 'coordinates' in feature:
            polygon_coords = feature['coordinates']
        elif 'polygon' in feature:
            polygon_coords = feature['polygon']
        
        if not polygon_coords:
            return None
        
        # Flatten nested arrays if needed
        if isinstance(polygon_coords[0][0], list):
            if isinstance(polygon_coords[0][0][0], list):
                coords = polygon_coords[0][0]
            else:
                coords = polygon_coords[0]
        else:
            coords = polygon_coords
        
        # Convert to [lat, lon] format for Leaflet using list comprehension
        leaflet_coords = []
        for coord in coords:
            if len(coord) >= 2:
                # GeoJSON uses [lon, lat] format
                lon, lat = coord[0], coord[1]
                # Check if it's actually lat, lon by checking if lat is reasonable for Singapore
                if lat > 90 or lat < -90:
                    lat, lon = coord[0], coord[1]
                leaflet_coords.append([lat, lon])
        
        if len(leaflet_coords) < 3:
            return None  # Need at least 3 points for a polygon
        
        # Get cluster information from properties
        cluster_name = properties.get('LOCALITY', properties.get('cluster', properties.get('name', properties.get('location', 'Dengue Cluster'))))
        cases = properties.get('CASE_SIZE', properties.get('cases', properties.get('case_count', properties.get('num_cases', ''))))
        
        # Create tooltip text
        tooltip_text = f"{cluster_name}"
        if cases:
            tooltip_text += f" ({cases} case{'s' if cases != 1 else ''})"
        
        # Create polygon with orange color for Dengue clusters
        return dl.Polygon(
            positions=leaflet_coords,
            color="#ff8800",
            fillColor="#ffaa33",
            fillOpacity=0.3,
            weight=2,
            children=[
                dl.Tooltip(tooltip_text)
            ]
        )
    except (ValueError, TypeError, IndexError) as e:
        print(f"Error processing Dengue feature: {e}")
        return None


def create_dengue_cluster_polygons(data):
    """
    Create polygon markers for Dengue clusters from poll-download API data.
    Uses parallel processing for better performance.
    """
    if not data:
        return []
    
    # Handle FeatureCollection format (GeoJSON)
    features = []
    if isinstance(data, dict):
        if 'features' in data:
            # FeatureCollection format
            features = data['features']
        elif 'data' in data and 'records' in data['data']:
            features = data['data']['records']
        elif 'records' in data:
            features = data['records']
        elif 'result' in data and 'records' in data['result']:
            features = data['result']['records']
    
    if not features:
        return []
    
    # Process features in parallel using ThreadPoolExecutor
    # For small datasets, sequential might be faster, but for large ones, parallel helps
    if len(features) > 10:
        # Use parallel processing for larger datasets
        futures = [_exposure_executor.submit(_process_single_dengue_feature, feature) for feature in features]
        polygons = [future.result() for future in futures]
        # Filter out None values
        return [p for p in polygons if p is not None]
    
    # Sequential processing for small datasets (less overhead)
    polygons = []
    for feature in features:
        polygon = _process_single_dengue_feature(feature)
        if polygon:
            polygons.append(polygon)
    return polygons


def format_dengue_clusters_display(data):
    """Format Dengue cluster data for display."""
    if not data:
        return html.P(
            "Error retrieving Dengue cluster data",
            style={"color": "#ff6b6b", "textAlign": "center"}
        )
    
    # Handle FeatureCollection format (GeoJSON) or old format
    features = []
    if isinstance(data, dict):
        #print(f"Dengue data: {data}")
        if 'features' in data:
            # FeatureCollection format
            features = data['features']
        elif 'data' in data and 'records' in data['data']:
            features = data['data']['records']
        elif 'records' in data:
            features = data['records']
        elif 'result' in data and 'records' in data['result']:
            features = data['result']['records']
    
    if not features:
        return html.P(
            "No Dengue cluster data available",
            style={"color": "#ccc", "textAlign": "center"}
        )
    
    # Create list of clusters
    cluster_items = []
    for feature in features:
        # Handle FeatureCollection format
        if feature.get('type') == 'Feature':
            properties = feature.get('properties', {})
        else:
            properties = feature
        
        cluster_name = properties.get('LOCALITY', properties.get('cluster', properties.get('name', properties.get('location', 'Unknown'))))
        cases = properties.get('CASE_SIZE', properties.get('cases', properties.get('case_count', properties.get('num_cases', 'N/A'))))
        
        cluster_items.append(
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "padding": "0.25rem 0.5rem",
                    "backgroundColor": "#3a4a5a",
                    "borderRadius": "0.25rem",
                    "marginBottom": "0.25rem",
                },
                children=[
                    html.Span(
                        cluster_name,
                        style={
                            "fontSize": "0.6875rem",
                            "color": "#ccc",
                            "flex": "1",
                        }
                    ),
                    html.Span(
                        f"{cases} case{'s' if cases != 1 else ''}" if cases != 'N/A' else "N/A",
                        style={
                            "fontSize": "0.6875rem",
                            "color": "#ff8800",
                            "fontWeight": "600",
                        }
                    ),
                ]
            )
        )
    
    return html.Div(
        children=cluster_items,
        style={
            "display": "flex",
            "flexDirection": "column",
            "flex": "1",
            "overflowY": "auto",
            "overflowX": "hidden",
            "minHeight": "0",
        }
    )


def register_weather_indices_callbacks(app):
    """
    Register callbacks for realtime exposure indexes page.

    Args:
        app: Dash app instance
    """
    @app.callback(
        Output('uv-index-content', 'children'),
        Input('weather-indices-interval', 'n_intervals')
    )
    def update_uv_index(_n_intervals):
        """Update UV index display."""
        data = fetch_uv_data()
        return format_uv_display(data)


    @app.callback(
        [Output('psi-markers', 'children'),
         Output('psi-metrics-table-content', 'children'),
         Output('psi-metrics-table-container', 'style')],
        [Input('weather-indices-interval', 'n_intervals'),
         Input('psi-display-mode-toggle-state', 'data')]
    )
    def update_psi_markers(_n_intervals, show_table):
        """Update PSI markers on map or table based on toggle state."""
        data = fetch_psi_data()
        
        # If table mode is enabled, show table and hide map markers
        if show_table:
            table_content = format_psi_display(data)
            return [], table_content, {"display": "block", "marginBottom": "0.5rem", "flexShrink": "0"}
        
        # Map mode: show markers and hide table
        markers = create_psi_markers(data)
        return markers, html.P("", style={"display": "none"}), {"display": "none"}

    @app.callback(
        [Output('psi-display-mode-toggle-state', 'data'),
         Output('toggle-psi-display-mode', 'style')],
        Input('toggle-psi-display-mode', 'n_clicks'),
        State('psi-display-mode-toggle-state', 'data'),
        prevent_initial_call=True
    )
    def toggle_psi_display_mode(_n_clicks, current_state):
        """Toggle PSI display mode between table and map text boxes."""
        if current_state is None:
            current_state = False
        
        new_state = not current_state
        return new_state, _get_toggle_style(new_state)

    @app.callback(
        Output('toggle-psi-display-mode', 'children'),
        Input('psi-display-mode-toggle-state', 'data')
    )
    def update_psi_display_mode_button(is_table_mode):
        """Update PSI display mode button label."""
        if is_table_mode:
            return "📍 PSI Map View"
        return "📊 PSI Table View"

    @app.callback(
        Output('zika-clusters-content', 'children'),
        Input('weather-indices-interval', 'n_intervals')
    )
    def update_zika_clusters_display(_n_intervals):
        """Update Zika clusters display."""
        future = fetch_zika_cluster_data_async()
        data = future.result()
        return format_zika_clusters_display(data)

    @app.callback(
        [Output('zika-clusters-toggle-state', 'data'),
         Output('toggle-zika-clusters', 'style')],
        Input('toggle-zika-clusters', 'n_clicks'),
        State('zika-clusters-toggle-state', 'data'),
        prevent_initial_call=True
    )
    def toggle_zika_clusters(_n_clicks, current_state):
        """Toggle Zika cluster polygons on map."""
        if current_state is None:
            current_state = False
        
        new_state = not current_state
        return new_state, _get_toggle_style(new_state)

    @app.callback(
        Output('toggle-zika-clusters', 'children'),
        Input('zika-clusters-toggle-state', 'data')
    )
    def update_zika_clusters_button_label(is_visible):
        """Update Zika clusters button label based on toggle state."""
        if is_visible:
            return "Don't Show Zika Cluster(s)"
        return "Show Zika Cluster(s)"

    @app.callback(
        Output('zika-clusters', 'children'),
        Input('zika-clusters-toggle-state', 'data')
    )
    def update_zika_cluster_polygons(is_visible):
        """Update Zika cluster polygons on map."""
        if not is_visible:
            return []
        
        future = fetch_zika_cluster_data_async()
        data = future.result()
        return create_zika_cluster_polygons(data)

    @app.callback(
        Output('dengue-clusters-content', 'children'),
        Input('weather-indices-interval', 'n_intervals')
    )
    def update_dengue_clusters_display(_n_intervals):
        """Update Dengue clusters display."""
        future = fetch_dengue_cluster_data_async()
        data = future.result()
        return format_dengue_clusters_display(data)

    @app.callback(
        [Output('dengue-clusters-toggle-state', 'data'),
         Output('toggle-dengue-clusters', 'style')],
        Input('toggle-dengue-clusters', 'n_clicks'),
        State('dengue-clusters-toggle-state', 'data'),
        prevent_initial_call=True
    )
    def toggle_dengue_clusters(_n_clicks, current_state):
        """Toggle Dengue cluster polygons on map."""
        if current_state is None:
            current_state = False
        
        new_state = not current_state
        return new_state, _get_toggle_style(new_state)

    @app.callback(
        Output('toggle-dengue-clusters', 'children'),
        Input('dengue-clusters-toggle-state', 'data')
    )
    def update_dengue_clusters_button_label(is_visible):
        """Update Dengue clusters button label based on toggle state."""
        if is_visible:
            return "Don't Show Dengue Cluster(s)"
        return "Show Dengue Cluster(s)"

    @app.callback(
        Output('dengue-clusters', 'children'),
        Input('dengue-clusters-toggle-state', 'data')
    )
    def update_dengue_cluster_polygons(is_visible):
        """Update Dengue cluster polygons on map."""
        if not is_visible:
            return []
        
        future = fetch_dengue_cluster_data_async()
        data = future.result()
        return create_dengue_cluster_polygons(data)

    @app.callback(
        Output('taxi-count-content', 'children'),
        Input('interval-component', 'n_intervals')
    )
    def update_main_page_taxi_count(_n_intervals):
        """Update taxi count display on main page."""
        data = fetch_taxi_availability()
        return format_main_page_taxi_count(data)

    @app.callback(
        Output('dengue-count-content', 'children'),
        Input('interval-component', 'n_intervals')
    )
    def update_main_page_dengue_count(_n_intervals):
        """Update Dengue cluster count display on main page."""
        future = fetch_dengue_cluster_data_async()
        data = future.result(timeout=30)
        return format_main_page_dengue_count(data)

    @app.callback(
        Output('zika-count-content', 'children'),
        Input('interval-component', 'n_intervals')
    )
    def update_main_page_zika_count(_n_intervals):
        """Update Zika cluster count display on main page."""
        future = fetch_zika_cluster_data_async()
        data = future.result(timeout=30)
        return format_main_page_zika_count(data)

    @app.callback(
        Output('main-psi-markers', 'children'),
        [Input('interval-component', 'n_intervals'),
         Input('psi-locations-toggle-state', 'data')]
    )
    def update_main_psi_markers(_n_intervals, is_visible):
        """Update PSI markers on main page map (showing only 24h PSI)."""
        # Only show markers if toggle is enabled
        if not is_visible:
            return []
        data = fetch_psi_data()
        return create_main_psi_markers(data)

    @app.callback(
        Output('psi-locations-toggle-state', 'data'),
        Input('toggle-psi-locations', 'n_clicks'),
        State('psi-locations-toggle-state', 'data')
    )
    def update_psi_locations_toggle_state(n_clicks, current_state):
        """Update Regional PSI Info toggle state in store."""
        if n_clicks is None or n_clicks == 0:
            return False
        return not current_state if current_state else True

    @app.callback(
        Output('toggle-psi-locations', 'children'),
        Input('toggle-psi-locations', 'n_clicks'),
        State('psi-locations-toggle-state', 'data')
    )
    def toggle_psi_locations_button(n_clicks, current_state):
        """
        Toggle Regional PSI Info button label.

        Args:
            n_clicks: Number of button clicks
            current_state: Current toggle state from store

        Returns:
            Button label
        """
        if n_clicks is None or n_clicks == 0:
            # Default state: hidden
            return "📍 Regional PSI Info"

        # Toggle state
        is_visible = not current_state if current_state else True

        if is_visible:
            return "📍 Hide Regional PSI Info"
        return "📍 Regional PSI Info"

    @app.callback(
        Output('main-psi-24h-value', 'children'),
        Input('interval-component', 'n_intervals')
    )
    def update_main_psi_24h_value(_n_intervals):
        """Update average 24h PSI display on main page with category."""
        data = fetch_psi_data()
        
        if not data or data.get("code") != 0:
            return create_metric_value_display("Error", color="#ff6b6b")

        items = data.get("data", {}).get("items", [])
        if not items:
            return create_metric_value_display("N/A", color="#999")

        readings = items[0].get("readings", {})

        # Get 24H PSI data and calculate average across regions
        psi_24h_data = readings.get("psi_twenty_four_hourly", {})
        psi_24h = _calc_regional_average(psi_24h_data)

        if psi_24h is None:
            return create_metric_value_display("N/A", color="#999")

        # Get color and category based on PSI value
        color, category = get_psi_category(psi_24h)

        # Create display with value and category
        return html.Div(
            [
                html.Span(
                    str(psi_24h),
                    style={"color": color, "fontWeight": "700"}
                ),
                html.Span(
                    f" ({category})",
                    style={"color": color, "fontSize": "0.875rem", "fontWeight": "600", "marginLeft": "0.25rem"}
                )
            ],
            style={
                "backgroundColor": "rgb(58, 74, 90)",
                "padding": "0.25rem 0.5rem",
                "borderRadius": "0.25rem",
                "display": "flex",
                "alignItems": "center",
            }
        )



def format_main_page_zika_count(data):
    """
    Format Zika cluster count for main page display using standard metric card.
    
    Args:
        data: API response with Zika cluster data (FeatureCollection format)
    
    Returns:
        HTML Div with Zika cluster count information using metric card
    """
    from components.metric_card import create_metric_card
    
    if not data:
        zika_card = create_metric_card(
            card_id="zika-cluster-card",
            label="🦠 Zika",
            value_id="zika-count-value",
            initial_value="Error"
        )
        zika_card.children[0].children[1].children = [create_metric_value_display("Error", color="#ff0000")]
        return zika_card
    
    # Handle FeatureCollection format (GeoJSON)
    features = []
    if isinstance(data, dict):
        if 'features' in data:
            # FeatureCollection format
            features = data['features']
        elif 'data' in data and 'records' in data['data']:
            features = data['data']['records']
        elif 'records' in data:
            features = data['records']
        elif 'result' in data and 'records' in data['result']:
            features = data['result']['records']
    
    # Count the number of features
    cluster_count = len(features) if features else 0
    
    zika_card = create_metric_card(
        card_id="zika-cluster-card",
        label="🦠 Zika",
        value_id="zika-count-value",
        initial_value=str(cluster_count)
    )
    zika_card.children[0].children[1].children = [create_metric_value_display(str(cluster_count), color="#ff0000")]
    return zika_card


def format_main_page_dengue_count(data):
    """
    Format Dengue cluster count for main page display using standard metric card.
    
    Args:
        data: API response with Dengue cluster data (FeatureCollection format)
    
    Returns:
        HTML Div with Dengue cluster count information using metric card
    """
    from components.metric_card import create_metric_card
    
    if not data:
        dengue_card = create_metric_card(
            card_id="dengue-cluster-card",
            label="🦟 Dengue",
            value_id="dengue-count-value",
            initial_value="Error"
        )
        dengue_card.children[0].children[1].children = [create_metric_value_display("Error", color="#ff0000")]
        return dengue_card
    
    # Handle FeatureCollection format (GeoJSON)
    features = []
    if isinstance(data, dict):
        if 'features' in data:
            # FeatureCollection format
            features = data['features']
        elif 'data' in data and 'records' in data['data']:
            features = data['data']['records']
        elif 'records' in data:
            features = data['records']
        elif 'result' in data and 'records' in data['result']:
            features = data['result']['records']
    
    # Count the number of features
    cluster_count = len(features) if features else 0
    
    dengue_card = create_metric_card(
        card_id="dengue-cluster-card",
        label="🦟 Dengue",
        value_id="dengue-count-value",
        initial_value=str(cluster_count)
    )
    dengue_card.children[0].children[1].children = [create_metric_value_display(str(cluster_count), color="#ff0000")]
    return dengue_card


def format_main_page_taxi_count(data):
    """
    Format taxi count for main page display.
    
    Args:
        data: API response with taxi data
    
    Returns:
        HTML Div with taxi count information
    """
    if not data or 'features' not in data:
        return html.P(
            "Error loading taxi data",
            style={
                "textAlign": "center",
                "color": "#ff6b6b",
                "fontSize": "12px"
            }
        )
    
    features = data.get('features', [])
    if not features:
        return html.P(
            "No taxi data available",
            style={
                "textAlign": "center",
                "color": "#999",
                "fontSize": "12px"
            }
        )
    
    # Get taxi count from properties
    first_feature = features[0]
    properties = first_feature.get('properties', {})
    taxi_count = properties.get('taxi_count', 0)
    
    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        "🚕",
                        style={"fontSize": "24px", "marginRight": "8px"}
                    ),
                    html.Span(
                        f"{taxi_count:,}",
                        style={
                            "fontSize": "28px",
                            "fontWeight": "bold",
                            "color": "#FFD700",
                        }
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "marginBottom": "4px",
                }
            ),
        ],
        style={
            "padding": "4px 0",
        }
    )


def _calc_regional_average(psi_data):
    """Calculate average PSI across all regions (rounded up)."""
    regions = ["north", "south", "east", "west", "central"]
    values = []
    for region in regions:
        val = psi_data.get(region)
        if val is not None:
            try:
                values.append(float(val))
            except (ValueError, TypeError):
                pass
    if values:
        return math.ceil(sum(values) / len(values))
    return None


def format_main_page_psi(data):
    """Format 24H average PSI data for compact display on main page."""
    if not data or data.get("code") != 0:
        return html.P(
            "Error loading PSI data",
            style={"color": "#ff6b6b", "textAlign": "center", "fontSize": "11px"}
        )

    items = data.get("data", {}).get("items", [])
    if not items:
        return html.P(
            "No PSI data available",
            style={"color": "#999", "textAlign": "center", "fontSize": "11px"}
        )

    readings = items[0].get("readings", {})

    # Get 24H PSI data and calculate average across regions
    psi_24h_data = readings.get("psi_twenty_four_hourly", {})
    psi_24h = _calc_regional_average(psi_24h_data)

    if psi_24h is None:
        return html.P(
            "PSI data not available",
            style={"color": "#999", "textAlign": "center", "fontSize": "11px"}
        )

    color, category = get_psi_category(psi_24h)

    return html.Div(
        [
            html.Div(
                str(psi_24h),
                style={
                    "fontSize": "36px",
                    "fontWeight": "bold",
                    "color": color,
                    "textAlign": "center",
                    "lineHeight": "1",
                }
            ),
            html.Div(
                category,
                style={
                    "fontSize": "14px",
                    "color": color,
                    "textAlign": "center",
                    "marginTop": "6px",
                    "fontWeight": "600",
                }
            ),
        ],
        style={
            "padding": "10px",
            "backgroundColor": "#1a2a3a",
            "borderRadius": "6px",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
        }
    )


def _get_toggle_style(active):
    """Get button style based on active state."""
    if active:
        return {
            "backgroundColor": "#f18b00",
            "border": "1px solid #f18b00",
            "borderRadius": "4px",
            "color": "#fff",
            "cursor": "pointer",
            "padding": "4px 8px",
            "fontSize": "14px",
        }
    return {
        "backgroundColor": "transparent",
        "border": "1px solid #6a7a8a",
        "borderRadius": "4px",
        "color": "#ccc",
        "cursor": "pointer",
        "padding": "4px 8px",
        "fontSize": "14px",
    }
