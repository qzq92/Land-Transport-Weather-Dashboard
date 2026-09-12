"""
Component for the Daily Health and Environmental Watch page.
Displays various exposure indexes across Singapore.
"""
from dash import html, dcc
from conf.cache_config import INTERVAL_WEATHER_INDICES_MS
import dash_leaflet as dl
from utils.map_utils import (
    get_onemap_attribution,
    SG_MAP_CENTER,
    SG_MAP_DEFAULT_ZOOM,
    SG_MAP_BOUNDS,
    ONEMAP_TILES_URL
)
from conf.page_layout_config import PAGE_PADDING, PAGE_HEIGHT, get_content_container_style, STANDARD_GAP
from components.air_quality_legend import build_air_quality_legend_column


def weather_indices_page():
    """
    Create the Daily Health and Environmental Watch page layout.
    Features: UV Index, WBGT, and other exposure indexes.

    Returns:
        HTML Div containing the Daily Health and Environmental Watch section
    """
    # Use standardized map configuration
    sg_center = SG_MAP_CENTER
    onemap_tiles_url = ONEMAP_TILES_URL
    fixed_zoom = SG_MAP_DEFAULT_ZOOM
    onemap_attribution = get_onemap_attribution()
    sg_bounds = SG_MAP_BOUNDS

    return html.Div(
        id="weather-indices-page",
        style={
            "display": "none",  # Hidden by default
            "padding": PAGE_PADDING,
            "height": PAGE_HEIGHT,
            "width": "100%",
        },
        children=[
            # Store for active marker type on map
            dcc.Store(id="exposure-marker-type", data={'type': None, 'ts': 0}),
            # Store for Zika clusters toggle state
            dcc.Store(id="zika-clusters-toggle-state", data=False),
            # Store for Dengue clusters toggle state
            dcc.Store(id="dengue-clusters-toggle-state", data=False),
            # Store for PSI display mode toggle state (False = map text boxes, True = table)
            dcc.Store(id="psi-display-mode-toggle-state", data=False),
            # Main content container: map on left, indices on right
            html.Div(
                id="weather-indices-content",
                style={
                    **get_content_container_style(gap=STANDARD_GAP),
                    "padding": "0 0.3125rem",
                },
                children=[
                    # Left side: Indices panels
                    html.Div(
                        id="weather-indices-panel",
                        style={
                            "flex": "1",
                            "minWidth": "18.75rem",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0.625rem",
                            "overflowY": "auto",
                        },
                        children=[
                            # UV Index card
                            html.Div(
                                id="uv-index-card",
                                style={
                                    "backgroundColor": "#4a5a6a",
                                    "borderRadius": "0.5rem",
                                    "padding": "0.625rem",
                                    "display": "flex",
                                    "flexDirection": "column",
                                },
                                children=[
                                    # Header with toggle button
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "justifyContent": "space-between",
                                            "alignItems": "center",
                                            "borderBottom": "0.0625rem solid #5a6a7a",
                                            "paddingBottom": "0.375rem",
                                            "marginBottom": "0.5rem",
                                        },
                                        children=[
                                            html.H5(
                                                "☀️ UV Index Today (Daylight hourly trend)",
                                                style={
                                                    "margin": "0",
                                                    "color": "#fff",
                                                    "fontWeight": "600",
                                                }
                                            ),
                                            # Note: UV doesn't have station locations
                                        ]
                                    ),
                                    html.Div(
                                        id="uv-index-content",
                                        style={
                                            "flex": "1",
                                            "overflowY": "auto",
                                        },
                                        children=[
                                            html.P(
                                                "Loading UV data...",
                                                style={
                                                    "color": "#ccc",
                                                    "textAlign": "center",
                                                    "padding": "0.75rem",
                                                }
                                            )
                                        ]
                                    ),
                                ]
                            ),
                            # Zika Clusters card
                            html.Div(
                                id="zika-clusters-card",
                                style={
                                    "backgroundColor": "#4a5a6a",
                                    "borderRadius": "0.5rem",
                                    "padding": "0.625rem",
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "gap": "0.5rem",
                                },
                                children=[
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "justifyContent": "space-between",
                                            "alignItems": "center",
                                            "borderBottom": "0.0625rem solid #5a6a7a",
                                            "paddingBottom": "0.375rem",
                                            "marginBottom": "0.5rem",
                                        },
                                        children=[
                                            html.H5(
                                                "🦟 Zika Clusters",
                                                style={
                                                    "margin": "0",
                                                    "color": "#fff",
                                                    "fontWeight": "600",
                                                }
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="zika-clusters-content",
                                        style={
                                            "flex": "1",
                                            "overflowY": "auto",
                                            "overflowX": "hidden",
                                            "minHeight": "0",
                                        },
                                        children=[
                                            html.P("Loading Zika cluster data...", style={
                                                "color": "#ccc",
                                                "textAlign": "center",
                                                "padding": "0.75rem",
                                            })
                                        ],
                                    ),
                                ]
                            ),
                            # Dengue Clusters card
                            html.Div(
                                id="dengue-clusters-card",
                                style={
                                    "backgroundColor": "#4a5a6a",
                                    "borderRadius": "0.5rem",
                                    "padding": "0.625rem",
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "gap": "0.5rem",
                                },
                                children=[
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "justifyContent": "space-between",
                                            "alignItems": "center",
                                            "borderBottom": "0.0625rem solid #5a6a7a",
                                            "paddingBottom": "0.375rem",
                                            "marginBottom": "0.5rem",
                                        },
                                        children=[
                                            html.H5(
                                                "🦟 Dengue Clusters",
                                                style={
                                                    "margin": "0",
                                                    "color": "#fff",
                                                    "fontWeight": "600",
                                                }
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="dengue-clusters-content",
                                        style={
                                            "flex": "1",
                                            "overflowY": "auto",
                                            "overflowX": "hidden",
                                            "minHeight": "0",
                                        },
                                        children=[
                                            html.P("Loading Dengue cluster data...", style={
                                                "color": "#ccc",
                                                "textAlign": "center",
                                                "padding": "0.75rem",
                                            })
                                        ],
                                    ),
                                ]
                            ),
                        ]
                    ),
                    # Map container
                    html.Div(
                        id="weather-indices-map-panel",
                        style={
                            "flex": "3",
                            "minWidth": "25rem",
                            "backgroundColor": "#1a2a3a",
                            "borderRadius": "0.5rem",
                            "overflow": "hidden",
                            "display": "flex",
                            "flexDirection": "column",
                        },
                        children=[
                            # Toggle buttons above map
                            html.Div(
                                style={
                                    "display": "flex",
                                    "justifyContent": "flex-start",
                                    "gap": "0.5rem",
                                    "padding": "0.5rem",
                                    "backgroundColor": "#2a3a4a",
                                    "borderRadius": "0.5rem 0.5rem 0 0",
                                },
                                children=[
                                    html.Button(
                                        "📊 PSI Table View",
                                        id="toggle-psi-display-mode",
                                        n_clicks=0,
                                        style={
                                            "padding": "0.375rem 0.75rem",
                                            "borderRadius": "0.375rem",
                                            "border": "0.125rem solid #60a5fa",
                                            "backgroundColor": "transparent",
                                            "color": "#60a5fa",
                                            "cursor": "pointer",
                                            "fontSize": "0.75rem",
                                            "fontWeight": "600",
                                        },
                                        title="Toggle between table view and map text boxes"
                                    ),
                                    html.Button(
                                        "Show Zika Cluster(s)",
                                        id="toggle-zika-clusters",
                                        n_clicks=0,
                                        style={
                                            "padding": "0.375rem 0.75rem",
                                            "borderRadius": "0.375rem",
                                            "border": "0.125rem solid #ff4444",
                                            "backgroundColor": "transparent",
                                            "color": "#ff4444",
                                            "cursor": "pointer",
                                            "fontSize": "0.75rem",
                                            "fontWeight": "600",
                                        },
                                        title="Toggle Zika clusters on map"
                                    ),
                                    html.Button(
                                        "Show Dengue Cluster(s)",
                                        id="toggle-dengue-clusters",
                                        n_clicks=0,
                                        style={
                                            "padding": "0.375rem 0.75rem",
                                            "borderRadius": "0.375rem",
                                            "border": "0.125rem solid #ff8800",
                                            "backgroundColor": "transparent",
                                            "color": "#ff8800",
                                            "cursor": "pointer",
                                            "fontSize": "0.75rem",
                                            "fontWeight": "600",
                                        },
                                        title="Toggle Dengue clusters on map"
                                    ),
                                ]
                            ),
                            # Map
                            html.Div(
                                style={
                                    "flex": "1",
                                    "minHeight": "0",
                                },
                                children=[
                                    dl.Map(
                                        id="weather-indices-map",
                                        center=sg_center,
                                        zoom=fixed_zoom,
                                        minZoom=fixed_zoom,
                                        maxZoom=fixed_zoom,
                                        maxBounds=sg_bounds,
                                        maxBoundsViscosity=1.0,
                                        style={
                                            "width": "100%",
                                            "height": "100%",
                                            "minHeight": "25rem",
                                            "backgroundColor": "#1a2a3a",
                                        },
                                        children=[
                                            dl.TileLayer(
                                                url=onemap_tiles_url,
                                                attribution=onemap_attribution,
                                                maxNativeZoom=18,
                                            ),
                                            dl.LayerGroup(
                                                id="weather-indices-markers"
                                            ),
                                            dl.LayerGroup(
                                                id="psi-markers"
                                            ),
                                            dl.LayerGroup(
                                                id="zika-clusters"
                                            ),
                                            dl.LayerGroup(
                                                id="dengue-clusters"
                                            ),
                                        ],
                                        zoomControl=False,
                                        dragging=False,
                                        scrollWheelZoom=False,
                                        touchZoom=False,
                                        doubleClickZoom=False,
                                        boxZoom=False,
                                        keyboard=False,
                                    ),
                                ]
                            ),
                        ]
                    ),
                    build_air_quality_legend_column(),
                ]
            ),
            # Interval for auto-refresh
            dcc.Interval(
                id='weather-indices-interval',
                interval=INTERVAL_WEATHER_INDICES_MS,
                n_intervals=0
            ),
        ]
    )
