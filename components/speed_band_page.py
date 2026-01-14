"""
Component for the Speed Band on the Roads page.
Displays traffic speed band data on a map.
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


def speed_band_page():
    """
    Create the Speed Band on the Roads page layout.
    Features: Traffic speed band data displayed as color-coded polylines on map.

    Returns:
        HTML Div containing the Speed Band page section
    """
    # Use standardized map configuration
    sg_center = SG_MAP_CENTER
    onemap_tiles_url = ONEMAP_TILES_URL
    fixed_zoom = SG_MAP_DEFAULT_ZOOM
    onemap_attribution = get_onemap_attribution()
    sg_bounds = SG_MAP_BOUNDS

    return html.Div(
        id="speed-band-page",
        style={
            "display": "none",  # Hidden by default
            "padding": "1.25rem",
            "height": "calc(100vh - 7.5rem)",
            "width": "100%",
        },
        children=[
            # Main content container
            html.Div(
                id="speed-band-content",
                style={
                    "display": "flex",
                    "gap": "1.25rem",
                    "height": "calc(100% - 3.125rem)",
                    "maxWidth": "112.5rem",
                    "margin": "0 auto",
                },
                children=[
                    # Left side: Speed Band Information Panel
                    html.Div(
                        id="speed-band-info-panel",
                        style={
                            "flex": "1",
                            "minWidth": "18.75rem",
                            "maxWidth": "25rem",
                            "backgroundColor": "#4a5a6a",
                            "borderRadius": "0.5rem",
                            "padding": "0.9375rem",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0.9375rem",
                            "overflowY": "auto",
                        },
                        children=[
                            html.Div(
                                style={
                                    "borderBottom": "0.0625rem solid #5a6a7a",
                                    "paddingBottom": "0.625rem",
                                    "marginBottom": "0.625rem",
                                },
                                children=[
                                    html.H5(
                                        "🏎️ Speed Band on the Roads",
                                        style={
                                            "margin": "0",
                                            "color": "#fff",
                                            "fontWeight": "600",
                                        }
                                    ),
                                ]
                            ),
                            html.Div(
                                id="speed-band-count-value",
                                style={
                                    "color": "#00BCD4",
                                    "fontSize": "1.125rem",
                                    "fontWeight": "700",
                                    "marginBottom": "0.625rem",
                                },
                                children=[
                                    html.Div(
                                        html.Span("Zoom in to view speed bands", style={"color": "#999"}),
                                        style={
                                            "backgroundColor": "rgb(58, 74, 90)",
                                            "padding": "4px 8px",
                                            "borderRadius": "4px",
                                        }
                                    )
                                ]
                            ),
                            html.Div(
                                id="speed-band-center-coords",
                                style={
                                    "marginBottom": "0.625rem",
                                },
                                children=[
                                    html.Div(
                                        [
                                            html.Span("Viewport Center: ", style={"color": "#ccc", "fontSize": "0.75rem"}),
                                            html.Span("--", style={"color": "#999", "fontSize": "0.75rem"}),
                                        ],
                                        style={
                                            "backgroundColor": "rgb(58, 74, 90)",
                                            "padding": "4px 8px",
                                            "borderRadius": "4px",
                                        }
                                    )
                                ]
                            ),
                            html.Div(
                                id="speed-band-legend",
                                style={
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "gap": "0.625rem",
                                    "padding": "0.625rem",
                                    "backgroundColor": "rgba(42, 54, 66, 0.8)",
                                    "borderRadius": "8px",
                                    "border": "2px solid rgba(255, 255, 255, 0.2)",
                                },
                                children=[
                                    html.P("Speed Band Legend", style={
                                        "color": "#fff",
                                        "fontSize": "0.875rem",
                                        "fontWeight": "700",
                                        "marginBottom": "10px",
                                        "marginTop": "0",
                                        "textAlign": "center",
                                    }),
                                    html.Div([
                                        html.Div([
                                            html.Div(style={
                                                "width": "30px",
                                                "height": "4px",
                                                "backgroundColor": "#FF0000",
                                                "marginRight": "8px",
                                                "borderRadius": "2px",
                                            }),
                                            html.Span("1: 0-9 km/h", style={
                                                "color": "#ddd",
                                                "fontSize": "0.75rem",
                                                "whiteSpace": "nowrap",
                                            })
                                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"}),
                                        html.Div([
                                            html.Div(style={
                                                "width": "30px",
                                                "height": "4px",
                                                "backgroundColor": "#FF4500",
                                                "marginRight": "8px",
                                                "borderRadius": "2px",
                                            }),
                                            html.Span("2: 10-19 km/h", style={
                                                "color": "#ddd",
                                                "fontSize": "0.75rem",
                                                "whiteSpace": "nowrap",
                                            })
                                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"}),
                                        html.Div([
                                            html.Div(style={
                                                "width": "30px",
                                                "height": "4px",
                                                "backgroundColor": "#FFA500",
                                                "marginRight": "8px",
                                                "borderRadius": "2px",
                                            }),
                                            html.Span("3: 20-29 km/h", style={
                                                "color": "#ddd",
                                                "fontSize": "0.75rem",
                                                "whiteSpace": "nowrap",
                                            })
                                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"}),
                                        html.Div([
                                            html.Div(style={
                                                "width": "30px",
                                                "height": "4px",
                                                "backgroundColor": "#FFD700",
                                                "marginRight": "8px",
                                                "borderRadius": "2px",
                                            }),
                                            html.Span("4: 30-39 km/h", style={
                                                "color": "#ddd",
                                                "fontSize": "0.75rem",
                                                "whiteSpace": "nowrap",
                                            })
                                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"}),
                                        html.Div([
                                            html.Div(style={
                                                "width": "30px",
                                                "height": "4px",
                                                "backgroundColor": "#FFFF00",
                                                "marginRight": "8px",
                                                "borderRadius": "2px",
                                            }),
                                            html.Span("5: 40-49 km/h", style={
                                                "color": "#ddd",
                                                "fontSize": "0.75rem",
                                                "whiteSpace": "nowrap",
                                            })
                                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"}),
                                        html.Div([
                                            html.Div(style={
                                                "width": "30px",
                                                "height": "4px",
                                                "backgroundColor": "#ADFF2F",
                                                "marginRight": "8px",
                                                "borderRadius": "2px",
                                            }),
                                            html.Span("6: 50-59 km/h", style={
                                                "color": "#ddd",
                                                "fontSize": "0.75rem",
                                                "whiteSpace": "nowrap",
                                            })
                                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"}),
                                        html.Div([
                                            html.Div(style={
                                                "width": "30px",
                                                "height": "4px",
                                                "backgroundColor": "#32CD32",
                                                "marginRight": "8px",
                                                "borderRadius": "2px",
                                            }),
                                            html.Span("7: 60-69 km/h", style={
                                                "color": "#ddd",
                                                "fontSize": "0.75rem",
                                                "whiteSpace": "nowrap",
                                            })
                                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"}),
                                        html.Div([
                                            html.Div(style={
                                                "width": "30px",
                                                "height": "4px",
                                                "backgroundColor": "#008000",
                                                "marginRight": "8px",
                                                "borderRadius": "2px",
                                            }),
                                            html.Span("8: 70+ km/h", style={
                                                "color": "#ddd",
                                                "fontSize": "0.75rem",
                                                "whiteSpace": "nowrap",
                                            })
                                        ], style={"display": "flex", "alignItems": "center"}),
                                    ]),
                                    html.Div(
                                        "Note: Due to computation limits, speed band "
                                        "is only shown during map zoom in.",
                                        style={
                                            "color": "#aaa",
                                            "fontSize": "0.6875rem",
                                            "fontStyle": "italic",
                                            "marginTop": "0.3125rem",
                                            "paddingTop": "0.625rem",
                                            "borderTop": "1px solid rgba(255, 255, 255, 0.1)",
                                            "textAlign": "center",
                                            "lineHeight": "1.4"
                                        }
                                    )
                                ]
                            ),
                        ]
                    ),
                    # Middle: Map
                    html.Div(
                        id="speed-band-map-panel",
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
                            html.Div(
                                style={
                                    "position": "relative",
                                    "width": "100%",
                                    "height": "100%",
                                    "flex": "1",
                                    "minHeight": "25rem",
                                },
                                children=[
                                    dcc.Loading(
                                        id="speed-band-map-loading",
                                        type="circle",
                                        color="#00BCD4",
                                        style={
                                            "position": "absolute",
                                            "top": "50%",
                                            "left": "50%",
                                            "transform": "translate(-50%, -50%)",
                                            "zIndex": "1000"
                                        },
                                        children=[
                                            dl.Map(
                                                id="speed-band-map",
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
                                                    dl.LayerGroup(id="speed-band-map-markers"),
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
                ]
            ),
            # Store for speed band data
            dcc.Store(id="speed-band-page-toggle-state", data=True),
            # Interval for auto-refresh
            dcc.Interval(
                id='speed-band-interval',
                interval=5*60*1000,  # Update every 5 minutes
                n_intervals=0
            ),
        ]
    )
