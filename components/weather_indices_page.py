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
from conf.page_layout_config import PAGE_PADDING, PAGE_HEIGHT, get_content_container_style, STANDARD_GAP


# Helper functions for pollutant category table
def _create_bullet_span(color):
    """Create a colored bullet point span for pollutant categories."""
    return html.Span("", style={
        "color": color,
        "fontSize": "0.625rem",
        "marginRight": "0.25rem"
    })


def _create_category_cell(color, range_text):
    """Create a table cell for a pollutant category with bullet and range."""
    return html.Td(
        [_create_bullet_span(color), range_text],
        style={
            "textAlign": "center",
            "padding": "0.25rem 0.375rem",
            "borderBottom": "0.0625rem solid #2a2a2a",
            "color": color,
            "fontSize": "0.875rem"
        }
    )


def _create_pollutant_label_cell(label_text):
    """Create a table cell for pollutant label (first column)."""
    return html.Td(
        label_text,
        style={
            "padding": "0.25rem 0.375rem",
            "borderBottom": "0.0625rem solid #2a2a2a",
            "fontSize": "0.875rem"
        }
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
                            "flex": "2",
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
                    # Right side: Legend panels (stacked vertically)
                    html.Div(
                        style={
                            "flex": "1",
                            "minWidth": "15.625rem",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": STANDARD_GAP,
                        },
                        children=[
                            # Pollutant Legend
                            html.Div(
                                id="pollutant-legend",
                                style={
                                    "flex": "8",
                                    "minWidth": "15.625rem",
                                    "backgroundColor": "#2a3a4a",
                                    "borderRadius": "0.5rem",
                                    "padding": "0.5rem",
                                    "overflowY": "auto",
                                    "minHeight": "0",
                                    "display": "flex",
                                    "flexDirection": "column",
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
                                    "fontSize": "1rem",
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
                                    "fontSize": "0.875rem",
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
                            # Pollutant Color Categories Legend
                            html.Div(
                                        style={
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
                                            "fontSize": "1rem",
                                            "fontWeight": "600",
                                            "color": "#60a5fa",
                                            "marginBottom": "0.1875rem",
                                        }
                                    ),
                                    html.Table(
                                        style={
                                            "width": "100%",
                                            "fontSize": "0.875rem",
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
                                                                    "padding": "0.25rem 0.375rem",
                                                                    "borderBottom": "0.0625rem solid #3a4a5a",
                                                                    "fontWeight": "600",
                                                                    "color": "#fff",
                                                                    "fontSize": "0.875rem",
                                                                }
                                                            ),
                                                            html.Th(
                                                                "Good",
                                                                style={
                                                                    "textAlign": "center",
                                                                    "padding": "0.25rem 0.375rem",
                                                                    "borderBottom": "0.0625rem solid #3a4a5a",
                                                                    "fontWeight": "600",
                                                                    "color": "#fff",
                                                                    "fontSize": "0.875rem",
                                                                }
                                                            ),
                                                            html.Th(
                                                                "Moderate",
                                                                style={
                                                                    "textAlign": "center",
                                                                    "padding": "0.25rem 0.375rem",
                                                                    "borderBottom": "0.0625rem solid #3a4a5a",
                                                                    "fontWeight": "600",
                                                                    "color": "#fff",
                                                                    "fontSize": "0.875rem",
                                                                }
                                                            ),
                                                            html.Th(
                                                                "Unhealthy",
                                                                style={
                                                                    "textAlign": "center",
                                                                    "padding": "0.25rem 0.375rem",
                                                                    "borderBottom": "0.0625rem solid #3a4a5a",
                                                                    "fontWeight": "600",
                                                                    "color": "#fff",
                                                                    "fontSize": "0.875rem",
                                                                }
                                                            ),
                                                            html.Th(
                                                                "Very Unhealthy",
                                                                style={
                                                                    "textAlign": "center",
                                                                    "padding": "0.25rem 0.375rem",
                                                                    "borderBottom": "0.0625rem solid #3a4a5a",
                                                                    "fontWeight": "600",
                                                                    "color": "#fff",
                                                                    "fontSize": "0.875rem",
                                                                }
                                                            ),
                                                            html.Th(
                                                                "Hazardous",
                                                                style={
                                                                    "textAlign": "center",
                                                                    "padding": "0.25rem 0.375rem",
                                                                    "borderBottom": "0.0625rem solid #3a4a5a",
                                                                    "fontWeight": "600",
                                                                    "color": "#fff",
                                                                    "fontSize": "0.875rem",
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
                                                                style={"padding": "0.375rem 0.5rem", "borderBottom": "0.0625rem solid #2a2a2a", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#3ea72d", "fontSize": "0.875rem", "marginRight": "0.375rem"}), "0-15"],
                                                                style={"textAlign": "center", "padding": "0.375rem 0.5rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#3ea72d", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#fff300", "fontSize": "0.875rem", "marginRight": "0.375rem"}), "15-35"],
                                                                style={"textAlign": "center", "padding": "0.375rem 0.5rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#fff300", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#f18b00", "fontSize": "0.875rem", "marginRight": "0.375rem"}), "35-55"],
                                                                style={"textAlign": "center", "padding": "0.375rem 0.5rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#f18b00", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#e53210", "fontSize": "0.875rem", "marginRight": "0.375rem"}), "55-150"],
                                                                style={"textAlign": "center", "padding": "0.375rem 0.5rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#e53210", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#b567a4", "fontSize": "0.875rem", "marginRight": "0.375rem"}), "150+"],
                                                                style={"textAlign": "center", "padding": "0.375rem 0.5rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#b567a4", "fontSize": "0.875rem"}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                [html.Strong("PM10", style={"color": "#fff"}), " (µg/m³)"],
                                                                style={"padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#3ea72d", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "0-45"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#3ea72d", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#fff300", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "45-100"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#fff300", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#f18b00", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "100-200"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#f18b00", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#e53210", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "200-300"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#e53210", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#b567a4", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "300+"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#b567a4", "fontSize": "0.875rem"}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                [html.Strong("SO₂", style={"color": "#fff"}), " (µg/m³)"],
                                                                style={"padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#3ea72d", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "0-20"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#3ea72d", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#fff300", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "20-50"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#fff300", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#f18b00", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "50-125"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#f18b00", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#e53210", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "125-250"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#e53210", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#b567a4", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "250+"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#b567a4", "fontSize": "0.875rem"}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                [html.Strong("CO", style={"color": "#fff"}), " (mg/m³)"],
                                                                style={"padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#3ea72d", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "0-4"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#3ea72d", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#fff300", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "4-9"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#fff300", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#f18b00", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "9-15"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#f18b00", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#e53210", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "15-30"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#e53210", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#b567a4", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "30+"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#b567a4", "fontSize": "0.875rem"}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                [html.Strong("O₃", style={"color": "#fff"}), " (µg/m³)"],
                                                                style={"padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#3ea72d", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "0-100"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#3ea72d", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#fff300", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "100-160"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#fff300", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#f18b00", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "160-240"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#f18b00", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#e53210", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "240-300"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#e53210", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#b567a4", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "300+"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#b567a4", "fontSize": "0.875rem"}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Tr(
                                                        children=[
                                                            html.Td(
                                                                [html.Strong("NO₂", style={"color": "#fff"}), " (µg/m³)"],
                                                                style={"padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#3ea72d", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "0-200"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#3ea72d", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#fff300", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "200-400"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#fff300", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#f18b00", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "400-1000"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#f18b00", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#e53210", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "1000-2000"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#e53210", "fontSize": "0.875rem"}
                                                            ),
                                                            html.Td(
                                                                [html.Span("", style={"color": "#b567a4", "fontSize": "0.625rem", "marginRight": "0.25rem"}), "2000+"],
                                                                style={"textAlign": "center", "padding": "0.25rem 0.375rem", "borderBottom": "0.0625rem solid #2a2a2a", "color": "#b567a4", "fontSize": "0.875rem"}
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        style={
                                            "marginTop": "0.25rem",
                                            "paddingTop": "0.25rem",
                                            "borderTop": "0.0625rem solid #3a4a5a",
                                            "fontSize": "0.5rem",
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
                            # PSI Color Categories (separate div from pollutant-legend)
                            html.Div(
                                id="psi-color-categories",
                                style={
                                    "flex": "2",
                                    "minWidth": "15.625rem",
                                    "backgroundColor": "#2a3a4a",
                                    "borderRadius": "0.5rem",
                                    "padding": "0.5rem",
                                    "overflowY": "auto",
                                    "minHeight": "0",
                                    "display": "flex",
                                    "flexDirection": "column",
                                },
                                children=[
                                    html.Div(
                                        "PSI Color Categories",
                                        style={
                                            "fontSize": "1rem",
                                            "fontWeight": "600",
                                            "color": "#60a5fa",
                                            "marginBottom": "0.1875rem",
                                        }
                                    ),
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "flexWrap": "wrap",
                                            "gap": "0.25rem 0.5rem",
                                            "fontSize": "0.875rem",
                                            "color": "#ccc",
                                        },
                                        children=[
                                            html.Span([
                                                html.Span(
                                                    "●",
                                                    style={
                                                        "color": "#3ea72d",
                                                        "fontSize": "0.75rem",
                                                        "marginRight": "0.25rem",
                                                    }
                                                ),
                                                "Good (0-50)"
                                            ]),
                                            html.Span([
                                                html.Span(
                                                    "●",
                                                    style={
                                                        "color": "#fff300",
                                                        "fontSize": "0.75rem",
                                                        "marginRight": "0.25rem",
                                                    }
                                                ),
                                                "Moderate (51-100)"
                                            ]),
                                            html.Span([
                                                html.Span(
                                                    "●",
                                                    style={
                                                        "color": "#f18b00",
                                                        "fontSize": "0.75rem",
                                                        "marginRight": "0.25rem",
                                                    }
                                                ),
                                                "Unhealthy (101-200)"
                                            ]),
                                            html.Span([
                                                html.Span(
                                                    "●",
                                                    style={
                                                        "color": "#e53210",
                                                        "fontSize": "0.75rem",
                                                        "marginRight": "0.25rem",
                                                    }
                                                ),
                                                "Very Unhealthy (201-300)"
                                            ]),
                                            html.Span([
                                                html.Span(
                                                    "●",
                                                    style={
                                                        "color": "#b567a4",
                                                        "fontSize": "0.75rem",
                                                        "marginRight": "0.25rem",
                                                    }
                                                ),
                                                "Hazardous (301+)"
                                            ]),
                                        ]
                                    ),
                                    html.Div(
                                        style={
                                            "marginTop": "0.25rem",
                                            "paddingTop": "0.25rem",
                                            "borderTop": "0.0625rem solid #3a4a5a",
                                            "fontSize": "0.5rem",
                                            "color": "#888",
                                            "fontStyle": "italic",
                                        },
                                        children=[
                                            "Source: Singapore NEA PSI Standards"
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
