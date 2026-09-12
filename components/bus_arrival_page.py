"""
Component for the Bus Arrival & Services Search page.
"""
from dash import html, dcc
from conf.cache_config import INTERVAL_TRANSPORT_MS, INTERVAL_BUS_ARRIVAL_MS
import dash_leaflet as dl
from utils.map_utils import (
    get_onemap_attribution,
    SG_MAP_CENTER,
    SG_MAP_DEFAULT_ZOOM,
    SG_MAP_BOUNDS,
    ONEMAP_TILES_URL
)
from conf.page_layout_config import get_content_container_style, STANDARD_GAP


def bus_arrival_view():
    """
    Create the reusable Bus Arrival & Services Search view.
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
        id="transit-bus-view",
        style={
            "display": "none",
            "flex": "1",
            "minHeight": "0",
            "width": "100%",
        },
        children=[
            # Main content container
            html.Div(
                id="bus-arrival-page-content",
                style={
                    **get_content_container_style(gap=STANDARD_GAP),
                    "flexWrap": "wrap",
                    "minWidth": "0",
                },
                children=[
                    # Left side: Bus search panel
                    html.Div(
                        id="bus-info-panel",
                        style={
                            "flex": "1 1 22rem",
                            "minWidth": "18.75rem",
                            "maxWidth": "100%",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0.75rem",
                            "minHeight": "0",
                            "overflow": "hidden",
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
                                    "flexWrap": "wrap",
                                    "gap": "1rem",
                                    "boxShadow": "0 0.125rem 0.5rem rgba(0, 0, 0, 0.3)",
                                    "border": "0.0625rem solid #4a5a6a",
                                    "width": "100%",
                                    "maxWidth": "100%",
                                    "minWidth": "0",
                                    "boxSizing": "border-box",
                                    "overflow": "hidden",
                                },
                                children=[
                                    # Bus Arrival Search Section
                                    html.Div(
                                        style={
                                            "flex": "1 1 16rem",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "gap": "0.5rem",
                                            "minWidth": "0",
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
                                                    "flexWrap": "wrap",
                                                    "gap": "0.5rem",
                                                    "alignItems": "center",
                                                    "minWidth": "0",
                                                },
                                                children=[
                                                    dcc.Input(
                                                        id="bus-stop-search-input",
                                                        type="text",
                                                        placeholder="Enter bus stop code or click on map",
                                                        style={
                                                            "flex": "1",
                                                            "minWidth": "0",
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
                                                            "flexShrink": "0",
                                                        },
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                    # Bus Service Search Section
                                    html.Div(
                                        style={
                                            "flex": "1 1 16rem",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "gap": "0.5rem",
                                            "minWidth": "0",
                                            "paddingLeft": "1rem",
                                            "borderLeft": "0.0625rem solid #4a5a6a",
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
                                                    "flexWrap": "wrap",
                                                    "gap": "0.5rem",
                                                    "alignItems": "center",
                                                    "minWidth": "0",
                                                },
                                                children=[
                                                    dcc.Input(
                                                        id="bus-service-search-input",
                                                        type="text",
                                                        placeholder="Enter service number (e.g., 21, 21A, CT8)",
                                                        style={
                                                            "flex": "1",
                                                            "minWidth": "0",
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
                                                            "flexShrink": "0",
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
                                style={
                                    "flex": "1",
                                    "minHeight": "0",
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "gap": "0.5rem",
                                },
                                children=[
                                    html.Div(
                                        className="bus-arrival-toolbar",
                                        style={
                                            "display": "flex",
                                            "flexWrap": "wrap",
                                            "gap": "0.5rem",
                                            "alignItems": "center",
                                            "justifyContent": "space-between",
                                        },
                                        children=[
                                            dcc.RadioItems(
                                                id="bus-arrival-sort-mode",
                                                options=[
                                                    {"label": "Soonest", "value": "soonest"},
                                                    {"label": "Service no.", "value": "service"},
                                                ],
                                                value="soonest",
                                                inline=True,
                                                className="bus-arrival-sort",
                                            ),
                                            dcc.Input(
                                                id="bus-arrival-service-filter",
                                                type="text",
                                                placeholder="Filter service (e.g. 12)",
                                                debounce=False,
                                                style={
                                                    "width": "11rem",
                                                    "padding": "0.35rem 0.6rem",
                                                    "borderRadius": "0.375rem",
                                                    "border": "0.0625rem solid #5a6a7a",
                                                    "backgroundColor": "rgb(58, 74, 90)",
                                                    "color": "#fff",
                                                    "fontSize": "0.75rem",
                                                },
                                            ),
                                        ],
                                    ),
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
                                                "Enter a 5-digit stop code, or zoom the map and click a stop. You can also search a service number for its route.",
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
                                ],
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
                interval=INTERVAL_TRANSPORT_MS,
                n_intervals=0,
                disabled=True,
            ),
            # Interval for map invalidation (fixes grey tiles)
            dcc.Interval(
                id='bus-arrival-map-invalidate-interval',
                interval=300,  # 300 ms — intentionally short for map tile fix
                n_intervals=0,
                max_intervals=1,  # Only fire once per activation
                disabled=True  # Start disabled
            ),
            # Interval for bus arrival updates
            dcc.Interval(
                id='bus-arrival-interval',
                interval=INTERVAL_BUS_ARRIVAL_MS,
                n_intervals=0,
                disabled=True,
            ),
            # Store for current bus stop code to enable auto-refresh
            dcc.Store(id='current-bus-stop-code', data=None),
            dcc.Store(id='bus-arrival-results-store', data=None),
            dcc.Store(id='bus-arrival-filter-status', data=None),
        ]
    )

