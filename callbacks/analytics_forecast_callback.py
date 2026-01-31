"""
Callback functions for Analytics and Forecast page.
Handles MRT/LRT crowd forecast data visualization with async data fetching.
"""
import os
import csv
import time
import threading
from typing import Optional, Dict, Any
from datetime import datetime
from dash import Input, Output, html, dcc
import plotly.graph_objects as go
from utils.async_fetcher import fetch_url, run_in_thread


# API URL
PCD_FORECAST_URL = "https://datamall2.mytransport.sg/ltaodataservice/PCDForecast"

# 24-hour cache for forecast data (updated daily)
_FORECAST_CACHE: Dict[str, Dict[str, Any]] = {}
_FORECAST_CACHE_LOCK = threading.Lock()
FORECAST_CACHE_TTL = 24 * 60 * 60  # 24 hours in seconds


# API URL
PCD_FORECAST_URL = "https://datamall2.mytransport.sg/ltaodataservice/PCDForecast"

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


def create_crowd_forecast_chart(train_line: Optional[str] = None):
    """
    Create individual station cards with crowd forecast charts for a train line.
    
    Args:
        train_line: Train line code to display (e.g., "NSL")
    
    Returns:
        HTML Div with grid of station cards
    """
    # Fetch forecast data asynchronously for the specific train line
    forecast_future = fetch_crowd_forecast(train_line)
    if hasattr(forecast_future, "result"):
        forecast_data = forecast_future.result()
    else:
        forecast_data = forecast_future

    if not isinstance(forecast_data, dict) or 'value' not in forecast_data:
        # Return empty message
        return html.Div(
            "No forecast data available",
            style={
                "textAlign": "center",
                "color": "#999",
                "padding": "2rem",
                "fontSize": "1rem",
            }
        )
    
    # Get forecast data
    forecasts = forecast_data.get('value', [])
    
    if not forecasts:
        line_name = TRAIN_LINE_NAMES.get(train_line, train_line) if train_line else "a train line"
        return html.Div(
            f"No forecast data available for {line_name}",
            style={
                "textAlign": "center",
                "color": "#999",
                "padding": "2rem",
                "fontSize": "1rem",
            }
        )
    
    # Load station mapping and process data asynchronously
    station_map = _load_station_mapping()
    process_result_future = _process_forecast_data(forecasts)
    if hasattr(process_result_future, "result"):
        process_result = process_result_future.result()
    else:
        process_result = process_result_future
    
    # Unpack the result
    if isinstance(process_result, tuple) and len(process_result) == 2:
        station_data, forecast_date = process_result
    else:
        station_data = process_result if process_result else {}
        forecast_date = "Unknown Date"
    
    # Create station cards
    station_cards = []
    
    for station_code, data in sorted(station_data.items()):
        station_name = station_map.get(station_code, station_code)
        
        # Create individual chart for this station
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=data['times'],
            y=data['heights'],
            marker=dict(color=data['colors']),
            text=data['levels'],
            textposition='auto',
            hovertemplate='<b>Time:</b> %{x}<br><b>Crowd Level:</b> %{text}<extra></extra>',
        ))
        
        # Update layout for individual chart
        fig.update_layout(
            xaxis=dict(
                tickfont=dict(color="#ccc", size=10),
                gridcolor="#3a4a5a",
                showgrid=True,
            ),
            yaxis=dict(
                tickmode='array',
                tickvals=[1, 2, 3],
                ticktext=['Low', 'Moderate', 'High'],
                range=[0, 3.5],
                gridcolor="#3a4a5a",
                tickfont=dict(color="#ccc"),
                showgrid=True,
            ),
            template="plotly_dark",
            paper_bgcolor="#1a2a3a",
            plot_bgcolor="#1a2a3a",
            margin=dict(l=40, r=20, t=20, b=40),
            height=400,
            showlegend=False,
        )
        
        # Create card with station header and chart
        station_card = html.Div(
            className="station-card",
            style={
                "backgroundColor": "#1a2a3a",
                "borderRadius": "0.5rem",
                "padding": "1rem",
                "boxShadow": "0 0.125rem 0.5rem rgba(0, 0, 0, 0.3)",
            },
            children=[
                html.Div(
                    style={
                        "textAlign": "center",
                        "marginBottom": "0.75rem",
                    },
                    children=[
                        html.H5(
                            f"{station_name} ({station_code})",
                            style={
                                "margin": "0",
                                "color": "#fff",
                                "fontWeight": "600",
                                "fontSize": "1rem",
                            }
                        ),
                        html.Span(
                            f"{forecast_date}",
                            style={
                                "color": "#999",
                                "fontSize": "0.75rem",
                                "display": "block",
                                "marginTop": "0.25rem",
                            }
                        ),
                    ]
                ),
                dcc.Graph(
                    figure=fig,
                    config={'displayModeBar': False},
                    style={"height": "25rem"}  # 25rem = 400px at default font size
                ),
            ]
        )
        
        station_cards.append(station_card)
    
    # Return grid container with all station cards
    return html.Div(
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(3, 1fr)",
            "gap": "1rem",
            "width": "100%",
        },
        children=station_cards
    )


def register_analytics_forecast_callbacks(app):
    """
    Register callbacks for analytics and forecast page.
    
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
        
        return create_crowd_forecast_chart(selected_trainline)
