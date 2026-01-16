"""
Callback functions for handling weather forecast API integration.
References:
- 2-hour forecast:
  https://data.gov.sg/datasets?query=weather&resultId=d_3f9e064e25005b0e42969944ccaf2e7a
- 24-hour forecast:
  https://data.gov.sg/datasets?query=weather&resultId=d_ce2eb1e307bda31993c533285834ef2b
"""
import os
import requests
from dash import Input, Output, State, html
from dotenv import load_dotenv
import dash_leaflet as dl
from conf.weather_icons import get_weather_icon

load_dotenv(override=True)


def create_weather_markers(data):
    """
    Create weather icon markers for the 2-hour forecast map.

    Args:
        data: JSON response from 2-hour weather forecast API containing
              area_metadata (lat/lon) and items with forecasts

    Returns:
        List of dash_leaflet DivMarker components with weather icons
    """
    if not data or 'items' not in data or not data['items']:
        return []

    if 'area_metadata' not in data:
        return []

    # Build area name to lat/lon lookup from area_metadata
    area_coords = {}
    for area in data.get('area_metadata', []):
        name = area.get('name', '')
        loc = area.get('label_location', {})
        if name and loc:
            area_coords[name] = {
                'lat': loc.get('latitude'),
                'lon': loc.get('longitude')
            }

    forecast_item = data['items'][0]
    forecasts = forecast_item.get('forecasts', [])

    markers = []
    for forecast in forecasts:
        area_name = forecast.get('area', '')
        forecast_text = forecast.get('forecast', 'N/A')

        # Get coordinates for this area
        coords = area_coords.get(area_name)
        if not coords or not coords['lat'] or not coords['lon']:
            continue

        weather_icon = get_weather_icon(forecast_text)

        # Create a DivMarker with the weather icon
        icon_style = "font-size: 20px; text-shadow: 0 0 3px #000, 0 0 5px #000;"
        icon_html = f'<div style="{icon_style}">{weather_icon}</div>'
        marker = dl.DivMarker(
            position=[coords['lat'], coords['lon']],
            iconOptions={
                'className': 'weather-icon-marker',
                'html': icon_html,
                'iconSize': [30, 30],
                'iconAnchor': [15, 15],
            },
            children=[
                dl.Tooltip(
                    f"{area_name}: {forecast_text}",
                    permanent=False,
                    direction="top"
                )
            ]
        )
        markers.append(marker)

    return markers


def fetch_weather_forecast_2h():
    """
    Fetch 2-hour weather forecast from data.gov.sg API.
    Reference:
    https://data.gov.sg/datasets?query=weather&resultId=d_3f9e064e25005b0e42969944ccaf2e7a

    Returns:
        Dictionary containing forecast data or None if error
    """
    api_key = os.getenv('DATA_GOV_API')
    if not api_key:
        print("DATA_GOV_API environment variable not set")
        return None

    url = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
    headers = {
        "X-API-Key": api_key,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()
        print(f"2-hour weather forecast API failed: status={res.status_code}")
    except (requests.exceptions.RequestException, ValueError) as error:
        print(f"Error calling 2-hour weather forecast API: {error}")
    return None




def format_weather_2h(data):
    """
    Format 2-hour weather forecast data for display.
    Arranges towns in a grid layout with 4 columns and at least 12 rows.

    Args:
        data: JSON response from 2-hour weather forecast API

    Returns:
        HTML Div containing grid of town forecast divs (4 columns x 12+ rows)
    """
    if not data or 'items' not in data or not data['items']:
        return html.P("No data available", style={"padding": "10px", "color": "#999"})

    forecast_item = data['items'][0]

    # Get forecasts
    forecasts = forecast_item.get('forecasts', [])

    if not forecasts:
        return html.P("No forecast data available", style={"padding": "10px", "color": "#999"})

    # Create compact town divs for grid layout
    town_divs = []
    for forecast in forecasts:
        area_name = forecast.get('area', 'Unknown')
        forecast_text = forecast.get('forecast', 'N/A')
        weather_icon = get_weather_icon(forecast_text)

        town_divs.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                weather_icon,
                                style={"fontSize": "16px", "marginRight": "4px"}
                            ),
                            html.Span(
                                area_name,
                                style={
                                    "fontWeight": "600",
                                    "fontSize": "11px",
                                    "color": "#4CAF50",
                                }
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "marginBottom": "2px"
                        }
                    ),
                    html.Div(
                        forecast_text,
                        style={
                            "color": "#bbb",
                            "fontSize": "10px",
                            "lineHeight": "1.2",
                            "whiteSpace": "nowrap",
                            "overflow": "hidden",
                            "textOverflow": "ellipsis"
                        }
                    )
                ],
                style={
                    "padding": "6px 8px",
                    "borderRadius": "4px",
                    "backgroundColor": "#3a4a5a",
                    "border": "1px solid #555",
                }
            )
        )

    # Return grid container with 4 columns
    return html.Div(
        town_divs,
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(4, 1fr)",
            "gap": "6px",
            "width": "100%",
            "overflowY": "auto",
            "overflowX": "hidden",
            "padding": "5px",
        }
    )


def _build_weather_grid(general):
    """
    Build weather info cards from general forecast data using standard metric cards.
    Returns 4 cards: Temperature, Humidity, Wind, and General Forecast.
    Values shown as ranges with units beside each value (e.g., "23 °C - 33 °C").
    """
    from components.metric_card import create_metric_card, create_metric_value_display
    
    grid_items = []

    # Temperature card: "23 °C - 33 °C"
    temp = general.get('temperature', {})
    if temp:
        temp_value = f"{temp.get('low', 'N/A')} °C - {temp.get('high', 'N/A')} °C"
        temp_card = create_metric_card(
            card_id="forecast-24h-temperature-card",
            label="🌡️ Temperature",
            value_id="forecast-24h-temperature-value",
            initial_value=temp_value
        )
        temp_card.children[0].children[1].children = [create_metric_value_display(temp_value, color="#FF9800")]
        grid_items.append(temp_card)

    # Humidity card: "65 % - 95 %"
    hum = general.get('relativeHumidity', {})
    if hum:
        hum_value = f"{hum.get('low', 'N/A')} % - {hum.get('high', 'N/A')} %"
        hum_card = create_metric_card(
            card_id="forecast-24h-humidity-card",
            label="💧 Humidity",
            value_id="forecast-24h-humidity-value",
            initial_value=hum_value
        )
        hum_card.children[0].children[1].children = [create_metric_value_display(hum_value, color="#2196F3")]
        grid_items.append(hum_card)

    # Wind card: "15 km/h - 35 km/h SW"
    wind = general.get('wind', {})
    if wind:
        spd = wind.get('speed', {})
        direction = wind.get('direction', '')
        dir_text = f" {direction}" if direction else ""
        wind_value = f"{spd.get('low', 'N/A')} - {spd.get('high', 'N/A')} km/h{dir_text}"
        wind_card = create_metric_card(
            card_id="forecast-24h-wind-card",
            label="🌬️ Wind",
            value_id="forecast-24h-wind-value",
            initial_value=wind_value
        )
        wind_card.children[0].children[1].children = [create_metric_value_display(wind_value, color="#9C27B0")]
        grid_items.append(wind_card)

    # General Forecast card
    forecast = general.get('forecast', {})
    if forecast:
        text = forecast.get('text', 'N/A')
        forecast_card = create_metric_card(
            card_id="forecast-24h-forecast-card",
            label=f"{get_weather_icon(text)} Rain Forecast",
            value_id="forecast-24h-forecast-value",
            initial_value=text
        )
        forecast_card.children[0].children[1].children = [create_metric_value_display(text, color="#4CAF50")]
        grid_items.append(forecast_card)

    return grid_items


def fetch_and_format_weather_24h():
    """
    Fetch and format 24-hour weather forecast data for main dashboard display.
    Shows temperature, relative humidity, general forecast and wind information.
    Reference:
    https://data.gov.sg/datasets?query=weather&resultId=d_ce2eb1e307bda31993c533285834ef2b

    API structure: data.records[0].general contains all forecast info:
    - temperature: {low, high, unit}
    - relativeHumidity: {low, high, unit}
    - forecast: {code, text}
    - validPeriod: {start, end, text}
    - wind: {speed: {low, high}, direction}

    Returns:
        HTML Div with structured forecast display
    """
    # Fetch data from API
    api_key = os.getenv('DATA_GOV_API')
    if not api_key:
        print("DATA_GOV_API environment variable not set")
        return html.P(
            "API key not configured",
            style={"padding": "10px", "color": "#999", "textAlign": "center"}
        )

    url = "https://api-open.data.gov.sg/v2/real-time/api/twenty-four-hr-forecast"
    headers = {
        "X-API-Key": api_key,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"24-hour weather forecast API failed: status={res.status_code}")
            return html.P(
                "Failed to fetch weather data",
                style={"padding": "10px", "color": "#999", "textAlign": "center"}
            )
        data = res.json()
    except (requests.exceptions.RequestException, ValueError) as error:
        print(f"Error calling 24-hour weather forecast API: {error}")
        return html.P(
            "Error fetching weather data",
            style={"padding": "10px", "color": "#999", "textAlign": "center"}
        )

    # Handle API structure: data.records[0].general
    records = data.get('data', {}).get('records', []) if data else []
    if not records:
        return html.P(
            "No data available",
            style={"padding": "10px", "color": "#999", "textAlign": "center"}
        )

    # Extract data from general key
    general = records[0].get('general', {})

    # Build weather info cards (4 cards: Temperature, Humidity, Wind, Forecast)
    grid_items = _build_weather_grid(general)

    if not grid_items:
        return html.P(
            "No forecast data available",
            style={"padding": "10px", "color": "#999", "textAlign": "center"}
        )

    # Return 1-column layout with standard metric cards
    return html.Div(
        grid_items,
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "0.5rem",
            "width": "100%",
        }
    )


def register_weather_callbacks(app):
    """
    Register weather forecast callbacks for the dashboard.

    Args:
        app: Dash app instance
    """
    # Toggle callback for 2H forecast section
    @app.callback(
        Output('toggle-2h-forecast', 'children'),
        Input('toggle-2h-forecast', 'n_clicks'),
        State('2h-forecast-toggle-state', 'data')
    )
    def toggle_2h_forecast(n_clicks, current_state):
        """
        Toggle 2H weather forecast markers visibility on main map.

        Args:
            n_clicks: Number of button clicks
            current_state: Current toggle state from store

        Returns:
            Button label
        """
        if n_clicks is None or n_clicks == 0:
            # Default state: hidden
            return "🌦️ Show 2H Weather Forecast"

        # Toggle state
        is_visible = not current_state if current_state else True

        if is_visible:
            return "🌦️ Hide 2H Weather Forecast"
        return "🌦️ Show 2H Weather Forecast"

    @app.callback(
        Output('2h-forecast-toggle-state', 'data'),
        Input('toggle-2h-forecast', 'n_clicks'),
        State('2h-forecast-toggle-state', 'data')
    )
    def update_toggle_state(n_clicks, current_state):
        """Update toggle state in store."""
        if n_clicks is None or n_clicks == 0:
            return False
        return not current_state if current_state else True

    @app.callback(
        Output('weather-2h-markers', 'children'),
        Input('interval-component', 'n_intervals'),
        State('2h-forecast-toggle-state', 'data')
    )
    def update_weather_forecast_2h(_n_intervals, is_visible):
        """
        Update 2-hour weather forecast markers on main map periodically.
        Only updates when toggle is enabled.

        Args:
            n_intervals: Number of intervals (from dcc.Interval component)
            is_visible: Whether the 2H forecast markers should be visible

        Returns:
            List of map markers
        """
        # Only fetch data if toggle is enabled
        if not is_visible:
            return []

        # Fetch 2-hour forecast
        weather_2h_data = fetch_weather_forecast_2h()

        # Create weather markers for the map
        weather_markers = create_weather_markers(weather_2h_data)

        return weather_markers


    @app.callback(
        Output('weather-24h-content', 'children'),
        Input('interval-component', 'n_intervals')
    )
    def update_weather_forecast_24h_main(n_intervals):
        """
        Update 24-hour weather forecast display on main dashboard periodically.

        Args:
            n_intervals: Number of intervals (from dcc.Interval component)

        Returns:
            HTML content for 24-hour forecast (temperature, humidity, forecast, wind)
        """
        # n_intervals is required by the callback but not used directly
        _ = n_intervals

        # Fetch and format 24-hour forecast
        return fetch_and_format_weather_24h()
