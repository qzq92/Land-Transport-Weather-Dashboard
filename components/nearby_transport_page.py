"""
Component for the Nearby Transportation and Parking Info page.
Displays nearby transportation options and parking facilities.
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


def nearby_transport_page():
    """
    Create the Nearby Transportation and Parking Info page layout.
    Features: Nearby bus stops, MRT/LRT stations, taxi stands, carparks, and bicycle parking.

    Returns:
        HTML Div containing the Nearby Transportation and Parking Info section
    """
    # Use standardized map configuration
    sg_center = SG_MAP_CENTER
    onemap_tiles_url = ONEMAP_TILES_URL
    fixed_zoom = SG_MAP_DEFAULT_ZOOM
    onemap_attribution = get_onemap_attribution()
    sg_bounds = SG_MAP_BOUNDS

    return html.Div(
        id="nearby-transport-page",
        style={
            "display": "none",  # Hidden by default
            "padding": "1.25rem",
            "height": "calc(100vh - 7.5rem)",
            "width": "100%",
        },
        children=[
            # Main content container
            html.Div(
                id="nearby-transport-content",
                style={
                    "display": "flex",
                    "gap": "1.25rem",
                    "height": "calc(100% - 3.125rem)",
                    "maxWidth": "112.5rem",
                    "margin": "0 auto",
                },
                children=[
                    # Left side: Info panel with tabs
                    html.Div(
                        id="nearby-transport-info-panel",
                        style={
                            "width": "30%",
                            "minWidth": "18.75rem",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0.9375rem",
                            "backgroundColor": "#1a2a3a",
                            "borderRadius": "0.5rem",
                            "padding": "0.9375rem",
                            "overflowY": "auto",
                        },
                        children=[
                            html.H3(
                                "Nearby Facilities",
                                style={
                                    "color": "#fff",
                                    "margin": "0 0 0.9375rem 0",
                                    "fontSize": "1.125rem",
                                    "fontWeight": "600",
                                }
                            ),
                            # Nearby facilities containers (row-wise)
                            html.Div(
                                id="nearby-facilities-containers",
                                style={
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "gap": "0.625rem",
                                    "flex": "1",
                                    "overflowY": "auto",
                                },
                                children=[
                                    # Row 1: Nearest HDB Carpark
                                    html.Div(
                                        id="nearby-transport-carpark-column",
                                        style={
                                            "width": "100%",
                                            "backgroundColor": "#2c3e50",
                                            "borderRadius": "0.3125rem",
                                            "padding": "0.9375rem",
                                            "minHeight": "9.375rem"
                                        },
                                        children=[
                                            html.H4(
                                                "Top 5 Nearest HDB Carparks",
                                                style={
                                                    "textAlign": "center",
                                                    "marginBottom": "0.625rem",
                                                    "color": "#fff",
                                                    "fontWeight": "700",
                                                    "fontSize": "0.875rem"
                                                }
                                            ),
                                            html.Div(
                                                id="nearby-transport-carpark-content",
                                                style={
                                                    "overflowY": "auto",
                                                    "overflowX": "hidden",
                                                    "maxHeight": "calc(100% - 2.5rem)"
                                                },
                                                children=[
                                                    html.P(
                                                        "Select a location to view nearest carparks",
                                                        style={
                                                            "textAlign": "center",
                                                            "color": "#999",
                                                            "fontSize": "0.75rem",
                                                            "fontStyle": "italic",
                                                            "padding": "0.9375rem"
                                                        }
                                                    )
                                                ]
                                            )
                                        ]
                                    ),
                                    # Row 2: Nearest Bus Stop
                                    html.Div(
                                        id="nearby-transport-bus-stop-column",
                                        style={
                                            "width": "100%",
                                            "backgroundColor": "#2c3e50",
                                            "borderRadius": "0.3125rem",
                                            "padding": "0.9375rem",
                                            "minHeight": "9.375rem"
                                        },
                                        children=[
                                            html.H4(
                                                "Top 5 Nearest Bus Stops",
                                                style={
                                                    "textAlign": "center",
                                                    "marginBottom": "0.625rem",
                                                    "color": "#fff",
                                                    "fontWeight": "700",
                                                    "fontSize": "0.875rem"
                                                }
                                            ),
                                            html.Div(
                                                id="nearby-transport-bus-stop-content",
                                                style={
                                                    "overflowY": "auto",
                                                    "overflowX": "hidden",
                                                    "maxHeight": "calc(100% - 2.5rem)"
                                                },
                                                children=[
                                                    html.P(
                                                        "Select a location to view nearest bus stops",
                                                        style={
                                                            "textAlign": "center",
                                                            "color": "#999",
                                                            "fontSize": "0.75rem",
                                                            "fontStyle": "italic",
                                                            "padding": "0.9375rem"
                                                        }
                                                    )
                                                ]
                                            )
                                        ]
                                    ),
                                    # Row 3: Nearest EV Charging Point
                                    html.Div(
                                        id="nearby-transport-ev-charging-column",
                                        style={
                                            "width": "100%",
                                            "backgroundColor": "#2c3e50",
                                            "borderRadius": "0.3125rem",
                                            "padding": "0.9375rem",
                                            "minHeight": "9.375rem"
                                        },
                                        children=[
                                            html.H4(
                                                "Nearby EV Charging Points",
                                                style={
                                                    "textAlign": "center",
                                                    "marginBottom": "0.625rem",
                                                    "color": "#fff",
                                                    "fontWeight": "700",
                                                    "fontSize": "0.875rem"
                                                }
                                            ),
                                            html.Div(
                                                id="nearby-transport-ev-charging-content",
                                                style={
                                                    "overflowY": "auto",
                                                    "overflowX": "hidden",
                                                    "maxHeight": "calc(100% - 2.5rem)"
                                                },
                                                children=[
                                                    html.P(
                                                        "Select a location to view nearby EV charging points",
                                                        style={
                                                            "textAlign": "center",
                                                            "color": "#999",
                                                            "fontSize": "0.75rem",
                                                            "fontStyle": "italic",
                                                            "padding": "0.9375rem"
                                                        }
                                                    )
                                                ]
                                            )
                                        ]
                                    ),
                                    # Row 4: Nearest MRT Stations
                                    html.Div(
                                        id="nearby-transport-mrt-column",
                                        style={
                                            "width": "100%",
                                            "backgroundColor": "#2c3e50",
                                            "borderRadius": "0.3125rem",
                                            "padding": "0.9375rem",
                                            "minHeight": "9.375rem"
                                        },
                                        children=[
                                            html.H4(
                                                "Nearest MRT (1KM radius) with crowd level",
                                                style={
                                                    "textAlign": "center",
                                                    "marginBottom": "0.625rem",
                                                    "color": "#fff",
                                                    "fontWeight": "700",
                                                    "fontSize": "0.875rem"
                                                }
                                            ),
                                            html.Div(
                                                id="nearby-transport-mrt-content",
                                                style={
                                                    "overflowY": "auto",
                                                    "overflowX": "hidden",
                                                    "maxHeight": "calc(100% - 2.5rem)"
                                                },
                                                children=[
                                                    html.P(
                                                        "Select a location to view nearest MRT stations",
                                                        style={
                                                            "textAlign": "center",
                                                            "color": "#999",
                                                            "fontSize": "0.75rem",
                                                            "fontStyle": "italic",
                                                            "padding": "0.9375rem"
                                                        }
                                                    )
                                                ]
                                            )
                                        ]
                                    ),
                                ]
                            ),
                            # Taxi Stands column (outside nearby facilities)
                            html.Div(
                                id="nearby-transport-taxi-stand-column",
                                style={
                                    "width": "100%",
                                    "backgroundColor": "#2c3e50",
                                    "borderRadius": "0.3125rem",
                                    "padding": "0.9375rem",
                                    "minHeight": "9.375rem",
                                    "marginTop": "0.625rem"
                                },
                                children=[
                                    html.H4(
                                        "Nearby 300m Taxi Stands",
                                        style={
                                            "textAlign": "center",
                                            "marginBottom": "0.625rem",
                                            "color": "#fff",
                                            "fontWeight": "700",
                                            "fontSize": "0.875rem"
                                        }
                                    ),
                                    html.Div(
                                        id="nearby-transport-taxi-stand-content",
                                        style={
                                            "overflowY": "auto",
                                            "overflowX": "hidden",
                                            "maxHeight": "calc(100% - 2.5rem)"
                                        },
                                        children=[
                                            html.P(
                                                "Select a location to view nearest taxi stands",
                                                style={
                                                    "textAlign": "center",
                                                    "color": "#999",
                                                    "fontSize": "0.75rem",
                                                    "fontStyle": "italic",
                                                    "padding": "0.9375rem"
                                                }
                                            )
                                        ]
                                    )
                                ]
                            ),
                            # Bicycle Parking column (outside nearby facilities)
                            html.Div(
                                id="nearby-transport-bicycle-column",
                                style={
                                    "width": "100%",
                                    "backgroundColor": "#2c3e50",
                                    "borderRadius": "0.3125rem",
                                    "padding": "0.9375rem",
                                    "minHeight": "9.375rem",
                                    "marginTop": "0.625rem"
                                },
                                children=[
                                    html.H4(
                                        "Nearby 300m Bicycle Parking Spots",
                                        style={
                                            "textAlign": "center",
                                            "marginBottom": "0.625rem",
                                            "color": "#fff",
                                            "fontWeight": "700",
                                            "fontSize": "0.875rem"
                                        }
                                    ),
                                    html.Div(
                                        id="nearby-transport-bicycle-content",
                                        style={
                                            "overflowY": "auto",
                                            "overflowX": "hidden",
                                            "maxHeight": "calc(100% - 2.5rem)"
                                        },
                                        children=[
                                            html.P(
                                                "Select a location to view nearest bicycle parking",
                                                style={
                                                    "textAlign": "center",
                                                    "color": "#999",
                                                    "fontSize": "0.75rem",
                                                    "fontStyle": "italic",
                                                    "padding": "0.9375rem"
                                                }
                                            )
                                        ]
                                    )
                                ]
                            ),
                        ]
                    ),
                    # Right side: Search bar and Map
                    html.Div(
                        id="nearby-transport-map-panel",
                        style={
                            "flex": "1",
                            "minWidth": "31.25rem",
                            "display": "flex",
                            "flexDirection": "column",
                            "height": "100%",
                            "gap": "0.625rem",
                        },
                        children=[
                            # Search bar above map
                            html.Div(
                                id="nearby-transport-search-bar",
                                style={
                                    "flexShrink": "0",
                                },
                                children=[
                                    dcc.Dropdown(
                                        id="nearby-transport-search",
                                        placeholder="Search address or location in Singapore",
                                        style={"width": "100%", "marginBottom": "0.5rem"},
                                        searchable=True,
                                        clearable=True,
                                        optionHeight=40,
                                        maxHeight=240,
                                    )
                                ]
                            ),
                            # Map container
                            html.Div(
                                style={
                                    "flex": "1",
                                    "minHeight": "0",
                                    "backgroundColor": "#1a2a3a",
                                    "borderRadius": "0.5rem",
                                    "overflow": "hidden",
                                },
                                children=[
                                    dl.Map(
                                        id="nearby-transport-map",
                                        center=sg_center,
                                        zoom=fixed_zoom,
                                        minZoom=10,
                                        maxZoom=18,
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
                                    dl.LayerGroup(id="nearby-transport-search-marker"),
                                    dl.LayerGroup(id="nearby-bus-stop-markers"),
                                    dl.LayerGroup(id="nearby-mrt-markers"),
                                    dl.LayerGroup(id="nearby-taxi-stand-markers"),
                                    dl.LayerGroup(id="nearby-carpark-markers"),
                                    dl.LayerGroup(id="nearby-bicycle-markers"),
                                    dl.LayerGroup(id="nearby-ev-charging-markers"),
                                        ],
                                        zoomControl=True,
                                        dragging=True,
                                        scrollWheelZoom=True,
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
            # Store for search location
            dcc.Store(id="nearby-transport-location-store", data=None),
            # Interval for auto-refresh
            dcc.Interval(
                id='nearby-transport-interval',
                interval=2*60*1000,  # Update every 2 minutes
                n_intervals=0
            ),
        ]
    )

