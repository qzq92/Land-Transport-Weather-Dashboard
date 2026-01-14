"""
Component for the Daily Health and Environmental Watch page.
Displays various exposure indexes across Singapore.
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
            "padding": "20px",
            "height": "calc(100vh - 120px)",
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
                    "display": "flex",
                    "gap": "10px",
                    "height": "calc(100% - 50px)",
                    "maxWidth": "1800px",
                    "margin": "0 auto",
                    "padding": "0 5px",
                },
                children=[
                    # Left side: Indices panels
                    html.Div(
                        id="weather-indices-panel",
                        style={
                            "flex": "2",
                            "minWidth": "300px",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "10px",
                            "overflowY": "auto",
                        },
                        children=[
                            # UV Index card
                            html.Div(
                                id="uv-index-card",
                                style={
                                    "backgroundColor": "#4a5a6a",
                                    "borderRadius": "8px",
                                    "padding": "10px",
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
                                            "borderBottom": "1px solid #5a6a7a",
                                            "paddingBottom": "6px",
                                            "marginBottom": "8px",
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
                                                    "padding": "12px",
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
                            "flex": "6",
                            "minWidth": "400px",
                            "backgroundColor": "#1a2a3a",
                            "borderRadius": "8px",
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
                                            "minHeight": "400px",
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
                    # Pollutant Legend (separate div, not sharing parent with map)
                    html.Div(
                        id="pollutant-legend",
                        style={
                            "flex": "2",
                            "minWidth": "250px",
                            "backgroundColor": "#2a3a4a",
                            "borderRadius": "0.5rem",
                            "padding": "0.5rem",
                            "overflowY": "auto",
                            "maxHeight": "100%",
                            "display": "flex",
                            "flexDirection": "column",
                            "height": "100%",
                        },
                        children=[
                            # PSI Metrics Table
                            html.Div(
                                id="psi-metrics-table-container",
                                style={
                                    "display": "none",  # Hidden by default, shown when toggle is on
                                    "marginBottom": "0.5rem",
                                    "flexShrink": "0",
                                    "padding": "2rem",
                                },
                                children=[
                                    html.Div(
                                        id="psi-metrics-table-content",
                                        children=[
                                            html.P("Loading PSI data...", style={
                                                "color": "#ccc",
                                                "textAlign": "center",
                                                "padding": "0.75rem",
                                            })
                                        ],
                                    ),
                                ]
                            ),
                            html.Div(
                                "Pollutant Abbreviations",
                                style={
                                    "fontSize": "0.6875rem",
                                    "fontWeight": "700",
                                    "color": "#60a5fa",
                                    "marginBottom": "0.25rem",
                                    "flexShrink": "0",
                                }
                            ),
                            html.Div(
                                style={
                                    "display": "flex",
                                    "flexWrap": "wrap",
                                    "gap": "0.25rem 0.5rem",
                                    "fontSize": "0.625rem",
                                    "color": "#ccc",
                                    "flexShrink": "0",
                                },
                                children=[
                                    html.Span([
                                        html.Strong("PSI", style={"color": "#fff"}),
                                        " = Pollutant Standards Index"
                                    ]),
                                    html.Span([
                                        html.Strong("PM2.5", style={"color": "#fff"}),
                                        " = Particulate Matter ≤2.5µm"
                                    ]),
                                    html.Span([
                                        html.Strong("PM10", style={"color": "#fff"}),
                                        " = Particulate Matter ≤10µm"
                                    ]),
                                    html.Span([
                                        html.Strong("SO₂", style={"color": "#fff"}),
                                        " = Sulphur Dioxide"
                                    ]),
                                    html.Span([
                                        html.Strong("CO", style={"color": "#fff"}),
                                        " = Carbon Monoxide"
                                    ]),
                                    html.Span([
                                        html.Strong("O₃", style={"color": "#fff"}),
                                        " = Ozone"
                                    ]),
                                    html.Span([
                                        html.Strong("NO₂", style={"color": "#fff"}),
                                        " = Nitrogen Dioxide"
                                    ]),
                                ]
                            ),
                            # PSI Color Legend
                            html.Div(
                                        style={
                                            "marginTop": "0.375rem",
                                            "paddingTop": "0.375rem",
                                            "borderTop": "0.0625rem solid #3a4a5a",
                                            "flex": "1",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "minHeight": "0",
                                        },
                                children=[
                                    html.Div(
                                        "PSI Color Categories",
                                        style={
                                            "fontSize": "10px",
                                            "fontWeight": "600",
                                            "color": "#60a5fa",
                                            "marginBottom": "3px",
                                        }
                                    ),
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "flexWrap": "wrap",
                                            "gap": "4px 8px",
                                            "fontSize": "9px",
                                            "color": "#ccc",
                                        },
                                        children=[
                                            html.Span([
                                                html.Span(
                                                    "●",
                                                    style={
                                                        "color": "#3ea72d",
                                                        "fontSize": "12px",
                                                        "marginRight": "4px",
                                                    }
                                                ),
                                                "Good (0-50)"
                                            ]),
                                            html.Span([
                                                html.Span(
                                                    "●",
                                                    style={
                                                        "color": "#fff300",
                                                        "fontSize": "12px",
                                                        "marginRight": "4px",
                                                    }
                                                ),
                                                "Moderate (51-100)"
                                            ]),
                                            html.Span([
                                                html.Span(
                                                    "●",
                                                    style={
                                                        "color": "#f18b00",
                                                        "fontSize": "12px",
                                                        "marginRight": "4px",
                                                    }
                                                ),
                                                "Unhealthy (101-200)"
                                            ]),
                                            html.Span([
                                                html.Span(
                                                    "●",
                                                    style={
                                                        "color": "#e53210",
                                                        "fontSize": "12px",
                                                        "marginRight": "4px",
                                                    }
                                                ),
                                                "Very Unhealthy (201-300)"
                                            ]),
                                            html.Span([
                                                html.Span(
                                                    "●",
                                                    style={
                                                        "color": "#b567a4",
                                                        "fontSize": "12px",
                                                        "marginRight": "4px",
                                                    }
                                                ),
                                                "Hazardous (301+)"
                                            ]),
                                        ]
                                    ),
                                    html.Div(
                                        style={
                                            "marginTop": "4px",
                                            "paddingTop": "4px",
                                            "borderTop": "1px solid #3a4a5a",
                                            "fontSize": "8px",
                                            "color": "#888",
                                            "fontStyle": "italic",
                                        },
                                        children=[
                                            "Source: Singapore NEA PSI Standards"
                                        ]
                                    ),
                                ]
                            ),
                            # Pollutant Color Categories Legend
                            html.Div(
                                        style={
                                            "marginTop": "0.375rem",
                                            "paddingTop": "0.375rem",
                                            "borderTop": "0.0625rem solid #3a4a5a",
                                            "flex": "1",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "minHeight": "0",
                                        },
                                children=[
                                    html.Div(
                                        "Pollutant Color Categories",
                                        style={
                                            "fontSize": "10px",
                                            "fontWeight": "600",
                                            "color": "#60a5fa",
                                            "marginBottom": "3px",
                                        }
                                    ),
                                    html.Table(
                                        style={
                                            "width": "100%",
                                            "fontSize": "8px",
                                            "color": "#ccc",
                                            "borderCollapse": "collapse",
                                        },
                                        children=[
                                            # Header row
                                            html.Thead(
                                                children=[
                                                    html.Tr(
                                                        children=[
                                                            html.Th(
                                                                "Pollutant",
                                                                style={
                                                                    "textAlign": "left",
                                                                    "padding": "3px 4px",
                                                                    "borderBottom": "1px solid #3a4a5a",
                                                                    "fontWeight": "600",
                                                                    "color": "#fff",
                                                                }
                                                            ),
                                                            html.Th(
                                                                "Good",
                                                                style={
                                                                    "textAlign": "center",
                                                                    "padding": "3px 4px",
                                                                    "borderBottom": "1px solid #3a4a5a",
                                                                    "fontWeight": "600",
                                                                    "color": "#fff",
                                                                }
                                                            ),
                                                            html.Th(
                                                                "Moderate",
                                                                style={
                                                                    "textAlign": "center",
                                                                    "padding": "3px 4px",
                                                                    "borderBottom": "1px solid #3a4a5a",
                                                                    "fontWeight": "600",
                                                                    "color": "#fff",
                                                                }
                                                            ),
                                                            html.Th(
                                                                "Unhealthy",
                                                                style={
                                                                    "textAlign": "center",
                                                                    "padding": "3px 4px",
                                                                    "borderBottom": "1px solid #3a4a5a",
                                                                    "fontWeight": "600",
                                                                    "color": "#fff",
                                                                }
                                                            ),
                                                            html.Th(
                                                                "Very Unhealthy",
                                                                style={
                                                                    "textAlign": "center",
                                                                    "padding": "3px 4px",
                                                                    "borderBottom": "1px solid #3a4a5a",
                                                                    "fontWeight": "600",
                                                                    "color": "#fff",
                                                                }
                                                            ),
                                                            html.Th(
                                                                "Hazardous",
                                                                style={
                                                                    "textAlign": "center",
                                                                    "padding": "3px 4px",
                                                                    "borderBottom": "1px solid #3a4a5a",
                                                                    "fontWeight": "600",
                                                                    "color": "#fff",
                                                                }
                                                            ),
                                                        ]
                                                    )
                                                ]
                                            ),
                                            # Data rows
                                            html.Tbody(
                                                children=[
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                [html.Strong("PM2.5", style={"color": "#fff"}), " (µg/m³)"],
                                                                style={"padding": "4px 6px", "borderBottom": "1px solid #2a2a2a"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#3ea72d", "fontSize": "10px", "marginRight": "4px"}), "0-15"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#3ea72d"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#fff300", "fontSize": "10px", "marginRight": "4px"}), "15-35"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#fff300"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#f18b00", "fontSize": "10px", "marginRight": "4px"}), "35-55"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#f18b00"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#e53210", "fontSize": "10px", "marginRight": "4px"}), "55-150"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#e53210"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#b567a4", "fontSize": "10px", "marginRight": "4px"}), "150+"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#b567a4"}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                [html.Strong("PM10", style={"color": "#fff"}), " (µg/m³)"],
                                                                style={"padding": "4px 6px", "borderBottom": "1px solid #2a2a2a"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#3ea72d", "fontSize": "10px", "marginRight": "4px"}), "0-45"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#3ea72d"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#fff300", "fontSize": "10px", "marginRight": "4px"}), "45-100"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#fff300"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#f18b00", "fontSize": "10px", "marginRight": "4px"}), "100-200"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#f18b00"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#e53210", "fontSize": "10px", "marginRight": "4px"}), "200-300"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#e53210"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#b567a4", "fontSize": "10px", "marginRight": "4px"}), "300+"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#b567a4"}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                [html.Strong("SO₂", style={"color": "#fff"}), " (µg/m³)"],
                                                                style={"padding": "4px 6px", "borderBottom": "1px solid #2a2a2a"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#3ea72d", "fontSize": "10px", "marginRight": "4px"}), "0-20"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#3ea72d"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#fff300", "fontSize": "10px", "marginRight": "4px"}), "20-50"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#fff300"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#f18b00", "fontSize": "10px", "marginRight": "4px"}), "50-125"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#f18b00"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#e53210", "fontSize": "10px", "marginRight": "4px"}), "125-250"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#e53210"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#b567a4", "fontSize": "10px", "marginRight": "4px"}), "250+"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#b567a4"}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                [html.Strong("CO", style={"color": "#fff"}), " (mg/m³)"],
                                                                style={"padding": "4px 6px", "borderBottom": "1px solid #2a2a2a"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#3ea72d", "fontSize": "10px", "marginRight": "4px"}), "0-4"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#3ea72d"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#fff300", "fontSize": "10px", "marginRight": "4px"}), "4-9"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#fff300"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#f18b00", "fontSize": "10px", "marginRight": "4px"}), "9-15"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#f18b00"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#e53210", "fontSize": "10px", "marginRight": "4px"}), "15-30"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#e53210"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#b567a4", "fontSize": "10px", "marginRight": "4px"}), "30+"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#b567a4"}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                [html.Strong("O₃", style={"color": "#fff"}), " (µg/m³)"],
                                                                style={"padding": "4px 6px", "borderBottom": "1px solid #2a2a2a"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#3ea72d", "fontSize": "10px", "marginRight": "4px"}), "0-100"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#3ea72d"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#fff300", "fontSize": "10px", "marginRight": "4px"}), "100-160"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#fff300"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#f18b00", "fontSize": "10px", "marginRight": "4px"}), "160-240"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#f18b00"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#e53210", "fontSize": "10px", "marginRight": "4px"}), "240-300"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#e53210"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#b567a4", "fontSize": "10px", "marginRight": "4px"}), "300+"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#b567a4"}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                [html.Strong("NO₂", style={"color": "#fff"}), " (µg/m³)"],
                                                                style={"padding": "4px 6px", "borderBottom": "1px solid #2a2a2a"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#3ea72d", "fontSize": "10px", "marginRight": "4px"}), "0-200"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#3ea72d"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#fff300", "fontSize": "10px", "marginRight": "4px"}), "200-400"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#fff300"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#f18b00", "fontSize": "10px", "marginRight": "4px"}), "400-1000"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#f18b00"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#e53210", "fontSize": "10px", "marginRight": "4px"}), "1000-2000"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#e53210"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("●", style={"color": "#b567a4", "fontSize": "10px", "marginRight": "4px"}), "2000+"],
                                                                style={"textAlign": "center", "padding": "4px 6px", "borderBottom": "1px solid #2a2a2a", "color": "#b567a4"}
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        style={
                                            "marginTop": "4px",
                                            "paddingTop": "4px",
                                            "borderTop": "1px solid #3a4a5a",
                                            "fontSize": "8px",
                                            "color": "#888",
                                            "fontStyle": "italic",
                                        },
                                        children=[
                                            "Source: WHO/EPA Air Quality Standards"
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
            # Interval for auto-refresh
            dcc.Interval(
                id='weather-indices-interval',
                interval=2*60*1000,  # Update every 2 minutes
                n_intervals=0
            ),
        ]
    )
