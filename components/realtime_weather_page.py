"""
Component for the realtime weather metrics page.
Displays live weather station data across Singapore.
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
from conf.page_layout_config import PAGE_PADDING, PAGE_HEIGHT, get_content_container_style, LARGE_GAP


def realtime_weather_page():
    """
    Create the realtime weather metrics page layout.
    Features: temperature, rainfall, humidity, wind readings with map.

    Returns:
        HTML Div containing the realtime weather metrics section
    """
    # Use standardized map configuration
    sg_center = SG_MAP_CENTER
    onemap_tiles_url = ONEMAP_TILES_URL
    fixed_zoom = SG_MAP_DEFAULT_ZOOM
    onemap_attribution = get_onemap_attribution()
    sg_bounds = SG_MAP_BOUNDS

    return html.Div(
        id="realtime-weather-page",
        style={
            "display": "none",  # Hidden by default
            "padding": PAGE_PADDING,
            "height": PAGE_HEIGHT,
            "width": "100%",
        },
        children=[
            # Main content: readings grid on left, map and indicators on right
            html.Div(
                id="realtime-weather-section",
                style=get_content_container_style(gap=LARGE_GAP),
                children=[
                    # Store for active marker type (none by default)
                    dcc.Store(id="active-marker-type", data={'type': None, 'ts': 0}),
                    # Left side: Weather readings panels in 2x2 grid (3/10 width)
                    html.Div(
                        id="realtime-readings-panel",
                        style={
                            "flex": "3",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0.75rem",
                            "minWidth": "18.75rem",
                        },
                        children=[
                            # Temperature readings card
                            html.Div(
                                id="temperature-readings-card",
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
                                            "flexDirection": "row",
                                            "alignItems": "center",
                                            "justifyContent": "space-between",
                                        },
                                        children=[
                                            html.Span(
                                                "🌡️ Temperature averaged across sensors",
                                                style={
                                                    "color": "#fff",
                                                    "fontWeight": "600",
                                                    "fontSize": "0.8125rem"
                                                }
                                            ),
                                            html.Div(
                                                id="temperature-readings-content",
                                                children=[
                                                    html.Span("Loading...", style={
                                                        "color": "#999",
                                                        "fontSize": "0.75rem"
                                                    })
                                                ],
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="temp-sensor-values",
                                        style={
                                            "display": "none",
                                            "backgroundColor": "#3a4a5a",
                                            "borderRadius": "0.3125rem",
                                            "padding": "0.625rem",
                                            "maxHeight": "12.5rem",
                                            "overflowY": "auto",
                                        },
                                        children=[
                                            html.Div(id="temp-sensor-content", children=[
                                                html.P("Loading...", style={
                                                    "color": "#999",
                                                    "fontSize": "12px",
                                                    "textAlign": "center"
                                                })
                                            ])
                                        ]
                                    ),
                                ]
                            ),
                            # Rainfall readings card
                            html.Div(
                                id="rainfall-readings-card",
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
                                            "flexDirection": "row",
                                            "alignItems": "center",
                                            "justifyContent": "space-between",
                                        },
                                        children=[
                                            html.Span(
                                                "🌧️ Rainfall averaged across sensors",
                                                style={
                                                    "color": "#fff",
                                                    "fontWeight": "600",
                                                    "fontSize": "0.8125rem"
                                                }
                                            ),
                                            html.Div(
                                                id="rainfall-readings-content",
                                                children=[
                                                    html.Span("Loading...", style={
                                                        "color": "#999",
                                                        "fontSize": "0.75rem"
                                                    })
                                                ],
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="rainfall-sensor-values",
                                        style={
                                            "display": "none",
                                            "backgroundColor": "#3a4a5a",
                                            "borderRadius": "0.3125rem",
                                            "padding": "0.625rem",
                                            "maxHeight": "12.5rem",
                                            "overflowY": "auto",
                                        },
                                        children=[
                                            html.Div(id="rainfall-sensor-content", children=[
                                                html.P("Loading...", style={
                                                    "color": "#999",
                                                    "fontSize": "12px",
                                                    "textAlign": "center"
                                                })
                                            ])
                                        ]
                                    ),
                                ]
                            ),
                            # Humidity readings card
                            html.Div(
                                id="humidity-readings-card",
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
                                            "flexDirection": "row",
                                            "alignItems": "center",
                                            "justifyContent": "space-between",
                                        },
                                        children=[
                                            html.Span(
                                                "💧 Humidity",
                                                style={
                                                    "color": "#fff",
                                                    "fontWeight": "600",
                                                    "fontSize": "0.8125rem"
                                                }
                                            ),
                                            html.Div(
                                                id="humidity-readings-content",
                                                children=[
                                                    html.Span("Loading...", style={
                                                        "color": "#999",
                                                        "fontSize": "0.75rem"
                                                    })
                                                ],
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="humidity-sensor-values",
                                        style={
                                            "display": "none",
                                            "backgroundColor": "#3a4a5a",
                                            "borderRadius": "0.3125rem",
                                            "padding": "0.625rem",
                                            "maxHeight": "12.5rem",
                                            "overflowY": "auto",
                                        },
                                        children=[
                                            html.Div(id="humidity-sensor-content", children=[
                                                html.P("Loading...", style={
                                                    "color": "#999",
                                                    "fontSize": "12px",
                                                    "textAlign": "center"
                                                })
                                            ])
                                        ]
                                    ),
                                ]
                            ),
                            # Wind readings card
                            html.Div(
                                id="wind-readings-card",
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
                                            "flexDirection": "row",
                                            "alignItems": "center",
                                            "justifyContent": "space-between",
                                        },
                                        children=[
                                            html.Span(
                                                "💨 Wind Speed averaged across sensors",
                                                style={
                                                    "color": "#fff",
                                                    "fontWeight": "600",
                                                    "fontSize": "0.8125rem"
                                                }
                                            ),
                                            html.Div(
                                                id="wind-readings-content",
                                                children=[
                                                    html.Span("Loading...", style={
                                                        "color": "#999",
                                                        "fontSize": "0.75rem"
                                                    })
                                                ],
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="wind-sensor-values",
                                        style={
                                            "display": "none",
                                            "backgroundColor": "#3a4a5a",
                                            "borderRadius": "0.3125rem",
                                            "padding": "0.625rem",
                                            "maxHeight": "12.5rem",
                                            "overflowY": "auto",
                                        },
                                        children=[
                                            html.Div(id="wind-sensor-content", children=[
                                                html.P("Loading...", style={
                                                    "color": "#999",
                                                    "fontSize": "12px",
                                                    "textAlign": "center"
                                                })
                                            ])
                                        ]
                                    ),
                                ]
                            ),
                            # Lightning readings card
                            html.Div(
                                id="lightning-readings-card",
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
                                            "flexDirection": "row",
                                            "alignItems": "center",
                                            "justifyContent": "space-between",
                                        },
                                        children=[
                                            html.Span(
                                                "⚡ Lightning observations in last 5 minutes",
                                                style={
                                                    "color": "#fff",
                                                    "fontWeight": "600",
                                                    "fontSize": "0.8125rem"
                                                }
                                            ),
                                            html.Div(
                                                id="lightning-readings-content",
                                                children=[
                                                    html.Span("Loading...", style={
                                                        "color": "#999",
                                                        "fontSize": "0.75rem"
                                                    })
                                                ],
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="lightning-sensor-values",
                                        style={
                                            "display": "none",
                                            "backgroundColor": "#3a4a5a",
                                            "borderRadius": "0.3125rem",
                                            "padding": "0.625rem",
                                            "maxHeight": "12.5rem",
                                            "overflowY": "auto",
                                        },
                                        children=[
                                            html.Div(id="lightning-sensor-content", children=[
                                                html.P("Loading...", style={
                                                    "color": "#999",
                                                    "fontSize": "12px",
                                                    "textAlign": "center"
                                                })
                                            ])
                                        ]
                                    ),
                                ]
                            ),
                            # Flood readings card
                            html.Div(
                                id="flood-readings-card",
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
                                            "flexDirection": "row",
                                            "alignItems": "center",
                                            "justifyContent": "space-between",
                                        },
                                        children=[
                                            html.Span(
                                                "🌊 Flood Alerts",
                                                style={
                                                    "color": "#fff",
                                                    "fontWeight": "600",
                                                    "fontSize": "0.8125rem"
                                                }
                                            ),
                                            html.Div(
                                                id="flood-readings-content",
                                                children=[
                                                    html.Span("Loading...", style={
                                                        "color": "#999",
                                                        "fontSize": "0.75rem"
                                                    })
                                                ],
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="flood-sensor-values",
                                        style={
                                            "display": "none",
                                            "backgroundColor": "#3a4a5a",
                                            "borderRadius": "0.3125rem",
                                            "padding": "0.625rem",
                                            "maxHeight": "12.5rem",
                                            "overflowY": "auto",
                                        },
                                        children=[
                                            html.Div(id="flood-sensor-content", children=[
                                                html.P("Loading...", style={
                                                    "color": "#999",
                                                    "fontSize": "12px",
                                                    "textAlign": "center"
                                                })
                                            ])
                                        ]
                                    ),
                                ]
                            ),
                            # WBGT readings card
                            html.Div(
                                id="wbgt-readings-card",
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
                                            "flexDirection": "row",
                                            "alignItems": "center",
                                            "justifyContent": "space-between",
                                        },
                                        children=[
                                            html.Span(
                                                "🌡️ WBGT (Heat Stress) average across sensors",
                                                style={
                                                    "color": "#fff",
                                                    "fontWeight": "600",
                                                    "fontSize": "0.8125rem"
                                                }
                                            ),
                                            html.Div(
                                                id="wbgt-readings-content",
                                                children=[
                                                    html.Span("Loading...", style={
                                                        "color": "#999",
                                                        "fontSize": "0.75rem"
                                                    })
                                                ],
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        id="wbgt-sensor-values",
                                        style={
                                            "display": "none",
                                            "backgroundColor": "#3a4a5a",
                                            "borderRadius": "0.3125rem",
                                            "padding": "0.625rem",
                                            "maxHeight": "12.5rem",
                                            "overflowY": "auto",
                                        },
                                        children=[
                                            html.Div(id="wbgt-sensor-content", children=[
                                                html.P("Loading...", style={
                                                    "color": "#999",
                                                    "fontSize": "12px",
                                                    "textAlign": "center"
                                                })
                                            ])
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                    # Right side: Map with station markers (7/10 width total)
                    html.Div(
                        style={
                            "flex": "7",
                            "display": "flex",
                            "gap": "10px",
                            "minWidth": "600px",
                        },
                        children=[
                            # Map panel
                            html.Div(
                                id="realtime-map-panel",
                                style={
                                    "flex": "1",
                                    "backgroundColor": "#4a5a6a",
                                    "borderRadius": "5px",
                                    "padding": "10px",
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "position": "relative",
                                },
                                children=[
                                    # Header with reading type toggles and 2H forecast toggle
                                    html.Div(
                                        style={
                                            "display": "flex",
                                            "justifyContent": "space-between",
                                            "alignItems": "center",
                                            "margin": "0 0 10px 0",
                                        },
                                        children=[
                                            html.Div(
                                                style={
                                                    "display": "flex",
                                                    "alignItems": "center",
                                                    "gap": "0.5rem",
                                                    "flexWrap": "wrap",
                                                },
                                                children=[
                                                    html.Button(
                                                        "Show temperature sensor locations",
                                                        id="toggle-temp-readings",
                                                        n_clicks=0,
                                                        style={
                                                            "padding": "4px 8px",
                                                            "borderRadius": "4px",
                                                            "border": "2px solid #FF9800",
                                                            "backgroundColor": "transparent",
                                                            "color": "#FF9800",
                                                            "cursor": "pointer",
                                                            "fontSize": "0.75rem",
                                                            "fontWeight": "600",
                                                        }
                                                    ),
                                                    html.Button(
                                                        "Show rainfall sensor locations",
                                                        id="toggle-rainfall-readings",
                                                        n_clicks=0,
                                                        style={
                                                            "padding": "4px 8px",
                                                            "borderRadius": "4px",
                                                            "border": "2px solid #2196F3",
                                                            "backgroundColor": "transparent",
                                                            "color": "#2196F3",
                                                            "cursor": "pointer",
                                                            "fontSize": "0.75rem",
                                                            "fontWeight": "600",
                                                        }
                                                    ),
                                                    html.Button(
                                                        "Show humidity sensor locations",
                                                        id="toggle-humidity-readings",
                                                        n_clicks=0,
                                                        style={
                                                            "padding": "4px 8px",
                                                            "borderRadius": "4px",
                                                            "border": "2px solid #00BCD4",
                                                            "backgroundColor": "transparent",
                                                            "color": "#00BCD4",
                                                            "cursor": "pointer",
                                                            "fontSize": "0.75rem",
                                                            "fontWeight": "600",
                                                        }
                                                    ),
                                                    html.Button(
                                                        "Show wind speed sensor locations",
                                                        id="toggle-wind-readings",
                                                        n_clicks=0,
                                                        style={
                                                            "padding": "4px 8px",
                                                            "borderRadius": "4px",
                                                            "border": "2px solid #4CAF50",
                                                            "backgroundColor": "transparent",
                                                            "color": "#4CAF50",
                                                            "cursor": "pointer",
                                                            "fontSize": "0.75rem",
                                                            "fontWeight": "600",
                                                        }
                                                    ),
                                                    html.Button(
                                                        "Show lightning sensor locations",
                                                        id="toggle-lightning-readings",
                                                        n_clicks=0,
                                                        style={
                                                            "padding": "4px 8px",
                                                            "borderRadius": "4px",
                                                            "border": "2px solid #FFD700",
                                                            "backgroundColor": "transparent",
                                                            "color": "#FFD700",
                                                            "cursor": "pointer",
                                                            "fontSize": "0.75rem",
                                                            "fontWeight": "600",
                                                        }
                                                    ),
                                                    html.Button(
                                                        "Show flood sensor locations",
                                                        id="toggle-flood-readings",
                                                        n_clicks=0,
                                                        style={
                                                            "padding": "4px 8px",
                                                            "borderRadius": "4px",
                                                            "border": "2px solid #ff6b6b",
                                                            "backgroundColor": "transparent",
                                                            "color": "#ff6b6b",
                                                            "cursor": "pointer",
                                                            "fontSize": "0.75rem",
                                                            "fontWeight": "600",
                                                        }
                                                    ),
                                                    html.Button(
                                                        "Show WBGT sensor locations",
                                                        id="toggle-wbgt-readings",
                                                        n_clicks=0,
                                                        style={
                                                            "padding": "4px 8px",
                                                            "borderRadius": "4px",
                                                            "border": "2px solid #fff",
                                                            "backgroundColor": "transparent",
                                                            "color": "#fff",
                                                            "cursor": "pointer",
                                                            "fontSize": "0.75rem",
                                                            "fontWeight": "600",
                                                        }
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                    # Map
                                    html.Div(
                                        style={
                                            "flex": "1",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "borderRadius": "5px",
                                            "overflow": "hidden",
                                            "minHeight": "400px",
                                        },
                                        children=[
                                            html.Div(
                                                style={
                                                    "flex": "1",
                                                    "borderRadius": "5px",
                                                    "overflow": "hidden",
                                                    "minHeight": "400px",
                                                },
                                                children=[
                                                    dl.Map(
                                                        id="realtime-weather-map",
                                                        center=sg_center,
                                                        zoom=fixed_zoom,
                                                        minZoom=10,
                                                        maxZoom=18,
                                                        maxBounds=sg_bounds,
                                                        maxBoundsViscosity=1.0,
                                                        style={
                                                            "width": "100%",
                                                            "height": "100%",
                                                            "minHeight": "400px",
                                                        },
                                                        dragging=True,
                                                        scrollWheelZoom=True,
                                                        zoomControl=True,
                                                        children=[
                                                            dl.TileLayer(
                                                                url=onemap_tiles_url,
                                                                attribution=onemap_attribution,
                                                                maxNativeZoom=18,
                                                            ),
                                                            dl.LayerGroup(id="realtime-weather-markers"),
                                                            dl.LayerGroup(id="lightning-markers"),
                                                            dl.LayerGroup(id="flood-markers"),
                                                            dl.LayerGroup(id="sensor-markers"),
                                                        ],
                                                    )
                                                ]
                                            ),
                                            # Disclaimer for lightning markers
                                            html.Div(
                                                style={
                                                    "padding": "8px 12px",
                                                    "backgroundColor": "#2c3e50",
                                                    "borderTop": "1px solid #5a6a7a",
                                                    "borderRadius": "0 0 5px 5px",
                                                },
                                                children=[
                                                    html.P(
                                                        "Location detected is based on last 5 minutes information",
                                                        style={
                                                            "color": "#999",
                                                            "fontSize": "11px",
                                                            "margin": "0",
                                                            "fontStyle": "italic",
                                                            "textAlign": "center",
                                                        }
                                                    )
                                                ]
                                            ),
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
                id='realtime-weather-interval',
                interval=2*60*1000,  # Update every 2 minutes
                n_intervals=0
            ),
            # Interval for map invalidation (fixes grey tiles)
            dcc.Interval(
                id='realtime-weather-map-invalidate-interval',
                interval=300,  # 300ms
                n_intervals=0,
                max_intervals=1,  # Only fire once per activation
                disabled=True  # Start disabled
            ),
        ]
    )
