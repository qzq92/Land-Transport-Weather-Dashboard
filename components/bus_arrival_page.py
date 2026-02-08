"""
Component for the Bus Arrival & Services Search page.
"""
from dash import html, dcc
import dash_leaflet as dl
from utils.map_utils import (
    get_onemap_attribution,
    SG_MAP_CENTER,
    SG_MAP_DEFAULT_ZOOM,
    SG_MAP_BOUNDS,
    ONEMAP_TILES_URL
)
from components.metric_card import create_metric_card
from conf.page_layout_config import PAGE_PADDING, PAGE_HEIGHT, get_content_container_style, STANDARD_GAP


def bus_arrival_page():
    """
    Create the Bus Arrival & Services Search page layout.
    Features: Bus stop search, bus arrival timings, and bus service route search with map.

    Returns:
        HTML Div containing the Bus Arrival & Services Search section
    """
    # Use standardized map configuration
    sg_center = SG_MAP_CENTER
    onemap_tiles_url = ONEMAP_TILES_URL
    fixed_zoom = SG_MAP_DEFAULT_ZOOM
    onemap_attribution = get_onemap_attribution()
    sg_bounds = SG_MAP_BOUNDS

    return html.Div(
        id="bus-arrival-page",
        style={
            "display": "none",  # Hidden by default
            "padding": PAGE_PADDING,
            "height": PAGE_HEIGHT,
            "width": "100%",
        },
        children=[
            # Main content container
            html.Div(
                id="bus-arrival-page-content",
                style=get_content_container_style(gap=STANDARD_GAP),
                children=[
                    # Left side: Bus search panel
                    html.Div(
                        id="bus-info-panel",
                        style={
                            "flex": "1",
                            "minWidth": "18.75rem",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0.75rem",
                        },
                        children=[
                            # Unified Header Section with both search inputs
                            html.Div(
                                id="bus-search-header",
                                style={
                                    "backgroundColor": "#1a2a3a",
                                    "borderRadius": "0.5rem",
                                    "padding": "1rem",
                                    "display": "flex",
                                    "flexDirection": "row",
                                    "gap": "1rem",
                                    "boxShadow": "0 0.125rem 0.5rem rgba(0, 0, 0, 0.3)",
                                    "border": "0.0625rem solid #4a5a6a",
                                },
                                children=[
                                    # Bus Arrival Search Section
                                    html.Div(
                                        style={
                                            "flex": "1",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "gap": "0.5rem",
                                        },
                                        children=[
                                            html.Label(
                                                "🚌 Bus Arrival Timings",
                                                style={
                                                    "color": "#fff",
                                                    "fontWeight": "600",
                                                    "fontSize": "0.875rem",
                                                    "marginBottom": "0.25rem",
                                                }
                                            ),
                                            html.Div(
                                                style={
                                                    "display": "flex",
                                                    "flexDirection": "row",
                                                    "gap": "0.5rem",
                                                    "alignItems": "center",
                                                },
                                                children=[
                                                    dcc.Input(
                                                        id="bus-stop-search-input",
                                                        type="text",
                                                        placeholder="Enter bus stop code or click on map",
                                                        style={
                                                            "flex": "1",
                                                            "padding": "0.5rem 0.75rem",
                                                            "borderRadius": "0.375rem",
                                                            "border": "0.0625rem solid #5a6a7a",
                                                            "backgroundColor": "rgb(58, 74, 90)",
                                                            "color": "#fff",
                                                            "fontSize": "0.8125rem",
                                                        },
                                                    ),
                                                    html.Button(
                                                        "🔍",
                                                        id="bus-stop-search-btn",
                                                        n_clicks=0,
                                                        style={
                                                            "padding": "0.5rem 0.875rem",
                                                            "backgroundColor": "#4169E1",
                                                            "color": "#fff",
                                                            "border": "none",
                                                            "borderRadius": "0.375rem",
                                                            "cursor": "pointer",
                                                            "fontSize": "0.875rem",
                                                            "fontWeight": "600",
                                                            "whiteSpace": "nowrap",
                                                            "transition": "background-color 0.2s",
                                                        },
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                    # Divider
                                    html.Div(
                                        style={
                                            "width": "0.0625rem",
                                            "backgroundColor": "#4a5a6a",
                                            "alignSelf": "stretch",
                                        }
                                    ),
                                    # Bus Service Search Section
                                    html.Div(
                                        style={
                                            "flex": "1",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "gap": "0.5rem",
                                        },
                                        children=[
                                            html.Label(
                                                "🔍 Bus Service Routes",
                                                style={
                                                    "color": "#fff",
                                                    "fontWeight": "600",
                                                    "fontSize": "0.875rem",
                                                    "marginBottom": "0.25rem",
                                                }
                                            ),
                                            html.Div(
                                                style={
                                                    "display": "flex",
                                                    "flexDirection": "row",
                                                    "gap": "0.5rem",
                                                    "alignItems": "center",
                                                },
                                                children=[
                                                    dcc.Input(
                                                        id="bus-service-search-input",
                                                        type="text",
                                                        placeholder="Enter service number (e.g., 21, 21A, CT8)",
                                                        style={
                                                            "flex": "1",
                                                            "padding": "0.5rem 0.75rem",
                                                            "borderRadius": "0.375rem",
                                                            "border": "0.0625rem solid #5a6a7a",
                                                            "backgroundColor": "rgb(58, 74, 90)",
                                                            "color": "#fff",
                                                            "fontSize": "0.8125rem",
                                                        },
                                                    ),
                                                    html.Button(
                                                        "🔍",
                                                        id="bus-service-search-btn",
                                                        n_clicks=0,
                                                        style={
                                                            "padding": "0.5rem 0.875rem",
                                                            "backgroundColor": "#4169E1",
                                                            "color": "#fff",
                                                            "border": "none",
                                                            "borderRadius": "0.375rem",
                                                            "cursor": "pointer",
                                                            "fontSize": "0.875rem",
                                                            "fontWeight": "600",
                                                            "whiteSpace": "nowrap",
                                                            "transition": "background-color 0.2s",
                                                        },
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            # Unified Results Area
                            html.Div(
                                id="bus-search-results",
                                style={
                                    "flex": "1",
                                    "backgroundColor": "#2a3a4a",
                                    "borderRadius": "0.5rem",
                                    "padding": "1rem",
                                    "overflowY": "auto",
                                    "minHeight": "0",
                                    "boxShadow": "0 0.125rem 0.5rem rgba(0, 0, 0, 0.3)",
                                    "border": "0.0625rem solid #4a5a6a",
                                },
                                children=[
                                    html.P(
                                        "Search for a bus stop or bus service to view information",
                                        style={
                                            "color": "#999",
                                            "textAlign": "center",
                                            "fontSize": "0.8125rem",
                                            "fontStyle": "italic",
                                            "margin": "2rem 0",
                                        }
                                    )
                                ]
                            ),
                        ]
                    ),
                    # Middle: Map
                    html.Div(
                        id="bus-map-panel",
                        style={
                            "flex": "2",
                            "minWidth": "31.25rem",
                            "backgroundColor": "#1a2a3a",
                            "borderRadius": "0.5rem",
                            "overflow": "hidden",
                            "display": "flex",
                            "flexDirection": "column",
                        },
                        children=[
                            # Toggle buttons container above map
                            html.Div(
                                id="bus-toggle-buttons-container",
                                style={
                                    "display": "flex",
                                    "flexDirection": "row",
                                    "gap": "0.625rem",
                                    "padding": "0.9375rem",
                                    "backgroundColor": "#2c3e50",
                                    "borderRadius": "0.5rem 0.5rem 0 0",
                                    "flexWrap": "wrap",
                                    "justifyContent": "flex-start",
                                    "alignItems": "center",
                                },
                                children=[
                                    html.Button(
                                        "Show Bus Stop Locations",
                                        id="bus-stops-toggle-btn",
                                        n_clicks=0,
                                        style={
                                            "backgroundColor": "transparent",
                                            "border": "0.125rem solid #4169E1",
                                            "borderRadius": "0.25rem",
                                            "color": "#4169E1",
                                            "cursor": "pointer",
                                            "padding": "0.25rem 0.625rem",
                                            "fontSize": "0.75rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                ]
                            ),
                            html.Div(
                                style={
                                    "position": "relative",
                                    "width": "100%",
                                    "height": "100%",
                                    "flex": "1",
                                    "minHeight": "25rem",
                                },
                                children=[
                                    dl.Map(
                                        id="bus-arrival-map",
                                        center=sg_center,
                                        zoom=fixed_zoom,
                                        minZoom=10,
                                        maxZoom=18,
                                        maxBounds=sg_bounds,
                                        maxBoundsViscosity=1.0,
                                        style={
                                            "width": "100%",
                                            "height": "100%",
                                            "backgroundColor": "#1a2a3a",
                                        },
                                        children=[
                                            dl.TileLayer(
                                                url=onemap_tiles_url,
                                                attribution=onemap_attribution,
                                                maxNativeZoom=18,
                                            ),
                                            dl.LayerGroup(id="bus-stops-markers"),
                                            dl.LayerGroup(id="bus-arrival-popup-layer"),
                                            dl.LayerGroup(id="bus-route-markers"),
                                        ],
                                        zoomControl=True,
                                        dragging=True,
                                        scrollWheelZoom=True,
                                    ),
                                    # Bus Stop Zoom Message Overlay
                                    html.Div(
                                        id="bus-stop-zoom-message",
                                        style={
                                            "position": "absolute",
                                            "top": "50%",
                                            "left": "50%",
                                            "transform": "translate(-50%, -50%)",
                                            "backgroundColor": "rgba(0, 0, 0, 0.8)",
                                            "color": "#fbbf24",
                                            "padding": "1rem 2rem",
                                            "borderRadius": "0.5rem",
                                            "zIndex": "1000",
                                            "textAlign": "center",
                                            "display": "none",
                                            "fontWeight": "600",
                                            "fontSize": "1rem",
                                            "border": "0.0625rem solid #fbbf24",
                                        },
                                        children="Zoom in to level 14+ to view bus stops"
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
            # Store for toggle states
            dcc.Store(id="bus-stops-toggle-state", data=False),
            dcc.Store(id="selected-bus-stop-code", data=None),
            # Interval for auto-refresh
            dcc.Interval(
                id='bus-arrival-page-interval',
                interval=2*60*1000,  # Update every 2 minutes
                n_intervals=0
            ),
            # Interval for map invalidation (fixes grey tiles)
            dcc.Interval(
                id='bus-arrival-map-invalidate-interval',
                interval=300,  # 300ms
                n_intervals=0,
                max_intervals=1,  # Only fire once per activation
                disabled=True  # Start disabled
            ),
            # Interval for bus arrival updates (every 1 minute)
            dcc.Interval(
                id='bus-arrival-interval',
                interval=60*1000,  # Update every 1 minute
                n_intervals=0
            ),
            # Store for current bus stop code to enable auto-refresh
            dcc.Store(id='current-bus-stop-code', data=None),
        ]
    )

