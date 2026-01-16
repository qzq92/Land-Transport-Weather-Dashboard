"""
Component for the 2-hour weather forecast page.
"""
from dash import html
import dash_leaflet as dl
from utils.map_utils import (
    get_onemap_attribution,
    SG_MAP_CENTER,
    SG_MAP_DEFAULT_ZOOM,
    SG_MAP_BOUNDS,
    ONEMAP_TILES_URL
)


def weather_forecast_page():
    """
    Create the 2-hour weather forecast page layout.
    Features side-by-side layout: weather info on left, static map with icons on right.

    Returns:
        HTML Div containing the weather forecast section with map
    """
    # Use standardized map configuration
    sg_center = SG_MAP_CENTER
    onemap_tiles_url = ONEMAP_TILES_URL
    fixed_zoom = SG_MAP_DEFAULT_ZOOM
    sg_bounds = SG_MAP_BOUNDS
    onemap_attribution = get_onemap_attribution()

    return html.Div(
        id="weather-forecast-page",
        style={
            "display": "none",  # Hidden by default, shown when weather tab is selected
            "padding": "0.5rem",
            "height": "calc(100vh - 11.25rem)",
            "width": "100%",
        },
        children=[
            # Main content: side-by-side layout
            html.Div(
                id="weather-forecast-section",
                style={
                    "display": "flex",
                    "gap": "10px",
                    "height": "calc(100% - 50px)",
                    "margin": "0 auto",
                },
                children=[
                    # Left side: Weather info grid (4 columns x 12+ rows)
                    html.Div(
                        id="weather-info-panel",
                        style={
                            "flex": "1.2",
                            "backgroundColor": "#4a5a6a",
                            "borderRadius": "5px",
                            "padding": "6px",
                            "display": "flex",
                            "flexDirection": "column",
                            "minWidth": "500px",
                        },
                        children=[
                            html.H5(
                                "Area Forecasts",
                                style={
                                    "textAlign": "center",
                                    "margin": "3px 0 6px 0",
                                    "color": "#fff",
                                    "fontWeight": "600",
                                    "fontSize": "14px"
                                }
                            ),
                            html.Div(
                                id="weather-2h-content",
                                children=[
                                    html.P("Loading...", style={"textAlign": "center", "padding": "20px", "color": "#999"})
                                ],
                                style={
                                    "padding": "3px",
                                    "overflowY": "auto",
                                    "flex": "1",
                                }
                            ),
                        ]
                    ),
                    # Right side: Static map with weather icons
                    html.Div(
                        id="weather-map-panel",
                        style={
                            "flex": "1.5",
                            "backgroundColor": "#4a5a6a",
                            "borderRadius": "5px",
                            "padding": "6px",
                            "display": "flex",
                            "flexDirection": "column",
                            "minWidth": "400px",
                        },
                        children=[
                            html.H5(
                                "Weather Map",
                                style={
                                    "textAlign": "center",
                                    "margin": "3px 0 6px 0",
                                    "color": "#fff",
                                    "fontWeight": "600",
                                    "fontSize": "14px"
                                }
                            ),
                            html.Div(
                                style={
                                    "flex": "1",
                                    "borderRadius": "5px",
                                    "overflow": "hidden",
                                    "minHeight": "400px",
                                },
                                children=[
                                    dl.Map(
                                        id="weather-2h-map",
                                        center=sg_center,
                                        zoom=fixed_zoom,
                                        minZoom=fixed_zoom,
                                        maxZoom=fixed_zoom,
                                        maxBounds=sg_bounds,
                                        maxBoundsViscosity=1.0,
                                        style={
                                            "width": "100%",
                                            "height": "calc(100vh - 280px)",
                                            "minHeight": "400px",
                                            "backgroundColor": "#1a2a3a",  # Match dark theme/sea color
                                        },
                                        dragging=True,
                                        touchZoom=False,
                                        scrollWheelZoom=True,
                                        doubleClickZoom=False,
                                        boxZoom=False,
                                        keyboard=False,
                                        zoomControl=True,
                                        children=[
                                            dl.TileLayer(
                                                url=onemap_tiles_url,
                                                attribution=onemap_attribution,
                                                maxNativeZoom=18,
                                            ),
                                            dl.LayerGroup(id="weather-markers-layer"),
                                        ],
                                    )
                                ]
                            ),
                        ]
                    ),
                ]
            ),
        ]
    )
