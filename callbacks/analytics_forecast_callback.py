"""
Callback functions for MRT/LRT Station Crowd Forecast page.
Handles MRT/LRT crowd forecast data visualization with async data fetching.
"""
import os
import csv
import re
import time
import threading
from typing import Optional, Dict, Any
from datetime import datetime
from dash import Input, Output, html, dcc
import plotly.graph_objects as go
from utils.async_fetcher import fetch_url, run_in_thread
from conf.cache_config import TTL_ANALYTICS_FORECAST_CALLBACKS
from conf.api_urls import PCD_FORECAST_URL

# 24-hour cache for forecast data (updated daily)
_FORECAST_CACHE: Dict[str, Dict[str, Any]] = {}
_FORECAST_CACHE_LOCK = threading.Lock()
FORECAST_CACHE_TTL: int = TTL_ANALYTICS_FORECAST_CALLBACKS

# Train line display names
TRAIN_LINE_NAMES = {
    'CCL': 'Circle Line (CCL)',
    'CEL': 'Circle Line Extension (CEL)',
    'CGL': 'Changi Airport Line (CGL)',
    'DTL': 'Downtown Line (DTL)',
    'EWL': 'East-West Line (EWL)',
    'NEL': 'North-East Line (NEL)',
    'NSL': 'North-South Line (NSL)',
    'BPL': 'Bukit Panjang LRT (BPL)',
    'SLRT': 'Sengkang LRT (SLRT)',
    'PLRT': 'Punggol LRT (PLRT)',
    'TEL': 'Thomson-East Coast Line (TEL)',
}


def _load_station_mapping() -> Dict[str, str]:
    """
    Load station codes to station names mapping from CSV file.
    Returns a dictionary mapping station codes to station names.
    """
    station_map = {}
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'MRTLRTStations.csv')

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stn_no = row.get('STN_NO', '').strip()
                stn_name = row.get('STN_NAME', '').strip()
                if stn_no and stn_name:
                    # Handle multi-line stations (e.g., "EW8/CC9")
                    if '/' in stn_no:
                        for code in stn_no.split('/'):
                            station_map[code.strip()] = stn_name
                    else:
                        station_map[stn_no] = stn_name
    except (FileNotFoundError, IOError) as e:
        print(f"Error loading station mapping: {e}")

    return station_map


@run_in_thread
def fetch_crowd_forecast(train_line: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch crowd forecast data from LTA DataMall API for a specific train line (async).
    Uses 24-hour cache since forecast data is updated daily.
    
    Args:
        train_line: Train line code (e.g., "NSL", "EWL")
    
    Returns:
        Dictionary containing crowd forecast data or None on error
    """
    if not train_line:
        return None
    
    api_key = os.getenv("LTA_API_KEY")
    if not api_key:
        print("Warning: LTA_API_KEY not found in environment variables")
        return None
    
    headers = {
        "AccountKey": api_key,
        "accept": "application/json"
    }
    
    # Build URL with TrainLine parameter
    url = f"{PCD_FORECAST_URL}?TrainLine={train_line}"
    
    # Check cache first
    with _FORECAST_CACHE_LOCK:
        cache_key = train_line
        if cache_key in _FORECAST_CACHE:
            cached_data = _FORECAST_CACHE[cache_key]
            cache_age = time.time() - cached_data.get('timestamp', 0)
            
            # Return cached data if less than 24 hours old
            if cache_age < FORECAST_CACHE_TTL and cached_data.get('data') is not None:
                print(f"Forecast data for {train_line} served from cache (age: {cache_age/3600:.1f}h)")
                return cached_data['data']
    
    # Cache expired or missing, fetch fresh data
    try:
        data = fetch_url(url, headers=headers)
        
        # Cache the result
        if data is not None:
            with _FORECAST_CACHE_LOCK:
                _FORECAST_CACHE[cache_key] = {
                    'data': data,
                    'timestamp': time.time()
                }
            print(f"Forecast data for {train_line} fetched and cached")
        
        return data
    except (ConnectionError, TimeoutError) as e:
        print(f"Error fetching crowd forecast: {e}")
        return None


@run_in_thread
def _process_forecast_data(forecasts: list) -> tuple:
    """
    Process forecast data and group by station (runs in thread for heavy processing).

    Args:
        forecasts: List of forecast dictionaries from the API 'value' field

    Returns:
        Tuple of (station_data dict, forecast_date string)
    """
    station_data = {}
    forecast_date = None
    
    # Crowd level mapping
    crowd_level_map = {
        'l': {'height': 1, 'color': '#32CD32', 'label': 'Low'},
        'm': {'height': 2, 'color': '#FFD700', 'label': 'Moderate'},
        'h': {'height': 3, 'color': '#FF4500', 'label': 'High'},
    }
    
    for forecast_day in forecasts:
        stations = forecast_day.get('Stations', [])
        
        # Get the date from the first forecast day
        if forecast_date is None and forecast_day.get('Date'):
            try:
                date_obj = datetime.fromisoformat(forecast_day.get('Date').replace('+08:00', ''))
                forecast_date = date_obj.strftime('%d %B %Y')  # e.g., "31 January 2026"
            except (ValueError, AttributeError):
                forecast_date = "Unknown Date"
        
        for station_entry in stations:
            station = station_entry.get('Station', '')
            intervals = station_entry.get('Interval', [])

            if not station:
                continue

            if station not in station_data:
                station_data[station] = {'times': [], 'levels': [], 'colors': [], 'heights': []}

            for interval in intervals:
                time_str = interval.get('Start', '')
                crowd = interval.get('CrowdLevel', 'NA')

                # Skip NA values
                if crowd == 'NA' or crowd not in crowd_level_map:
                    continue

                # Extract just the time from the datetime string
                try:
                    time_obj = datetime.fromisoformat(time_str.replace('+08:00', ''))
                    formatted_time = time_obj.strftime('%H:%M')  # e.g., "14:30"
                except (ValueError, AttributeError):
                    formatted_time = time_str  # Fallback to original

                station_data[station]['times'].append(formatted_time)
                station_data[station]['levels'].append(crowd_level_map[crowd]['label'])
                station_data[station]['colors'].append(crowd_level_map[crowd]['color'])
                station_data[station]['heights'].append(crowd_level_map[crowd]['height'])
    
    return station_data, forecast_date


def _station_code_sort_key(code: str):
    """Sort station codes numerically (e.g. NS1, NS2, ..., NS28)."""
    match = re.match(r"([a-zA-Z]+)(\d+)", code)
    if match:
        return (match.group(1).upper(), int(match.group(2)))
    return (code.upper(), 0)


def create_crowd_forecast_heatmap(train_line: Optional[str] = None):
    """
    Create a single colour-coded heatmap of crowd forecast for every station
    on the selected line.

    Rows = stations (sorted by code), Columns = time intervals,
    Cells = crowd level (Low / Moderate / High).

    Args:
        train_line: Train line code to display (e.g., "NSL")

    Returns:
        HTML Div containing a legend header and a Plotly Heatmap
    """
    # --- fetch & validate ------------------------------------------------
    forecast_future = fetch_crowd_forecast(train_line)
    forecast_data = (
        forecast_future.result()
        if hasattr(forecast_future, "result")
        else forecast_future
    )

    if not isinstance(forecast_data, dict) or "value" not in forecast_data:
        return html.Div(
            "No forecast data available",
            style={
                "textAlign": "center",
                "color": "#999",
                "padding": "2rem",
                "fontSize": "1rem",
            },
        )

    forecasts = forecast_data.get("value", [])
    if not forecasts:
        line_name = (
            TRAIN_LINE_NAMES.get(train_line, train_line) if train_line else "a train line"
        )
        return html.Div(
            f"No forecast data available for {line_name}",
            style={
                "textAlign": "center",
                "color": "#999",
                "padding": "2rem",
                "fontSize": "1rem",
            },
        )

    # --- process data ----------------------------------------------------
    station_map = _load_station_mapping()
    process_result_future = _process_forecast_data(forecasts)
    process_result = (
        process_result_future.result()
        if hasattr(process_result_future, "result")
        else process_result_future
    )

    if isinstance(process_result, tuple) and len(process_result) == 2:
        station_data, forecast_date = process_result
    else:
        station_data = process_result if process_result else {}
        forecast_date = "Unknown Date"

    if not station_data:
        return html.Div(
            "No station data to display",
            style={"textAlign": "center", "color": "#999", "padding": "2rem"},
        )

    # --- build heatmap matrix --------------------------------------------
    # Collect the superset of all time slots across stations
    all_times_set: set = set()
    for data in station_data.values():
        all_times_set.update(data["times"])
    sorted_times = sorted(all_times_set)

    # Sort stations by code (NS1, NS2, ...)
    sorted_codes = sorted(station_data.keys(), key=_station_code_sort_key)

    # Build labels (reversed so the first station is at the top of the heatmap)
    y_labels = [
        f"{code} {station_map.get(code, '')}" for code in reversed(sorted_codes)
    ]

    # Numeric mapping for z-values: 0 = N/A gap, 1 = Low, 2 = Moderate, 3 = High
    level_to_z = {"Low": 1, "Moderate": 2, "High": 3}
    # Matching text matrix for hover
    z_matrix = []
    text_matrix = []

    for code in reversed(sorted_codes):
        data = station_data[code]
        time_to_info = {}
        for t, lvl in zip(data["times"], data["levels"]):
            time_to_info[t] = lvl

        z_row = []
        text_row = []
        for t in sorted_times:
            lvl = time_to_info.get(t)
            z_row.append(level_to_z.get(lvl, 0))
            text_row.append(lvl if lvl else "N/A")
        z_matrix.append(z_row)
        text_matrix.append(text_row)

    # --- discrete colorscale (0=bg, 1=Low, 2=Mod, 3=High) ---------------
    colorscale = [
        [0.0, "#1a2a3a"],
        [0.33, "#32CD32"],
        [0.66, "#FFD700"],
        [1.0, "#FF4500"],
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=z_matrix,
            x=sorted_times,
            y=y_labels,
            text=text_matrix,
            texttemplate="%{text}",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Time: %{x}<br>"
                "Crowd: %{text}<extra></extra>"
            ),
            colorscale=colorscale,
            zmin=0,
            zmax=3,
            showscale=False,
            xgap=2,
            ygap=2,
        )
    )

    # Dynamic height: 28 px per station row, with min 400 and max 1200
    chart_height = max(400, min(1200, len(sorted_codes) * 28 + 100))

    fig.update_layout(
        xaxis=dict(
            side="top",
            tickfont=dict(color="#ccc", size=10),
            tickangle=-45,
            dtick=1,
        ),
        yaxis=dict(
            tickfont=dict(color="#ccc", size=11),
            autorange="reversed",
        ),
        template="plotly_dark",
        paper_bgcolor="#1a2a3a",
        plot_bgcolor="#1a2a3a",
        margin=dict(l=10, r=10, t=60, b=10),
        height=chart_height,
        showlegend=False,
    )

    # --- assemble layout -------------------------------------------------
    legend_bar = html.Div(
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "gap": "1.5rem",
            "padding": "0.5rem 0",
        },
        children=[
            html.Span(
                f"Forecast for {forecast_date}",
                style={
                    "color": "#ccc",
                    "fontSize": "0.8rem",
                    "marginRight": "1rem",
                },
            ),
            _legend_chip("#32CD32", "Low"),
            _legend_chip("#FFD700", "Moderate"),
            _legend_chip("#FF4500", "High"),
        ],
    )

    return html.Div(
        children=[
            legend_bar,
            dcc.Graph(
                figure=fig,
                config={"displayModeBar": False},
                style={"height": f"{chart_height}px"},
            ),
        ]
    )


def _legend_chip(color: str, label: str):
    """Return a small coloured dot + label for the legend bar."""
    return html.Div(
        style={"display": "flex", "alignItems": "center", "gap": "0.375rem"},
        children=[
            html.Div(
                style={
                    "width": "0.75rem",
                    "height": "0.75rem",
                    "borderRadius": "50%",
                    "backgroundColor": color,
                }
            ),
            html.Span(
                label,
                style={"color": "#fff", "fontSize": "0.8rem"},
            ),
        ],
    )


def register_analytics_forecast_callbacks(app):
    """
    Register callbacks for MRT/LRT Station Crowd Forecast page.
    
    Args:
        app: Dash app instance
    """
    @app.callback(
        Output('analytics-forecast-content', 'children'),
        Input('trainline-selector', 'value')
    )
    def update_forecast_chart(selected_trainline):
        """
        Update crowd forecast cards based on selected train line.
        
        Args:
            selected_trainline: Selected train line code
        
        Returns:
            HTML Div with station cards or prompt message
        """
        if not selected_trainline:
            return html.Div(
                "Please select a train line to view crowd forecast",
                style={
                    "textAlign": "center",
                    "color": "#999",
                    "padding": "2rem",
                    "fontSize": "1rem",
                }
            )
        
        return create_crowd_forecast_heatmap(selected_trainline)
