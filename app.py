# Import packages
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import sys
import logging
from dotenv import load_dotenv
# Load environment variables and logging
load_dotenv(override=True)

from components.banner_component import build_dashboard_banner
from components.map_component import map_component
from components.realtime_weather_page import realtime_weather_page
from components.weather_indices_page import weather_indices_page
from components.transport_page import transport_page
from components.nearby_transport_page import nearby_transport_page
from components.metric_card import create_metric_card
from callbacks.map_callback import register_search_callbacks
from callbacks.traffic_callback import register_camera_feed_callbacks
from callbacks.weather_callback import register_weather_callbacks
from callbacks.realtime_weather_callback import register_realtime_weather_callbacks
from callbacks.weather_indices_callback import register_weather_indices_callbacks
from callbacks.mrt_callback import register_mrt_callbacks
from callbacks.busstop_callbacks import register_busstop_callbacks
from callbacks.carpark_callback import register_carpark_callbacks
from callbacks.tab_navigation_callback import register_tab_navigation_callback
from callbacks.transport_callback import register_transport_callbacks
from callbacks.bus_arrival_callback import register_bus_arrival_callbacks
from callbacks.bus_service_callback import register_bus_service_callbacks
from callbacks.train_service_alerts_callback import register_train_service_alerts_callbacks
from callbacks.mrt_crowd_callback import register_mrt_crowd_callbacks
from auth.onemap_api import initialize_onemap_token
from utils.data_download_helper import (
    download_hdb_carpark_csv,
    download_speed_camera_csv
)
from callbacks.carpark_callback import clear_carpark_locations_cache


# Dash instantiation ---------------------------------------------------------#
app = Dash(__name__,
           meta_tags=[{
               "name": "viewport",
               "content": "width=device-width",
               "initial-scale": "1.0"}],
           external_stylesheets=[dbc.themes.DARKLY],
           suppress_callback_exceptions = True, #
           title="SimpleDashboard Demo"
        )
register_search_callbacks(app)
register_camera_feed_callbacks(app)
register_weather_callbacks(app)
register_realtime_weather_callbacks(app)
register_weather_indices_callbacks(app)
register_mrt_callbacks(app)
register_busstop_callbacks(app)
register_carpark_callbacks(app)
register_transport_callbacks(app)
register_bus_arrival_callbacks(app)
register_bus_service_callbacks(app)
register_train_service_alerts_callbacks(app)
register_mrt_crowd_callbacks(app)
register_tab_navigation_callback(app)

# Dashboard app layout ------------------------------------------------------#
app.layout = html.Div(
    id="root",
    children=[
        # Header/Banner -------------------------------------------------#
        html.Div(
            id="header",
            children=[
                build_dashboard_banner(),
            ],
        ),
        # Rail Operational Status Banner --------------------------------#
        html.Div(
            id="rail-status-banner",
            style={
                "backgroundColor": "#1a2a3a",
                "padding": "0.375rem 1.25rem",
                "borderBottom": "0.0625rem solid #4a5a6a",
                "width": "100%",
                "display": "flex",
                "flexDirection": "row",
                "alignItems": "flex-start",
                "justifyContent": "space-between",
                "minHeight": "2rem",
                "gap": "1rem",
            },
            children=[
                # Left column: MRT Lines (70% width)
                html.Div(
                    style={
                        "flex": "7",
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "0.5rem",
                    },
                    children=[
                        html.Span(
                            "MRT Lines:",
                            style={
                                "color": "#fff",
                                "fontWeight": "600",
                                "fontSize": "0.8125rem",
                                "whiteSpace": "nowrap",
                            }
                        ),
                        html.Div(
                            id="mrt-lines-display",
                    style={"width": "100%"},
                            children=[
                                html.P("Loading MRT line status...", 
                                       style={"color": "#999", "margin": "0", "fontSize": "0.75rem"})
                            ]
                        )
                    ]
                ),
                # Right column: LRT Lines (30% width)
                html.Div(
                    style={
                        "flex": "3",
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "0.5rem",
                    },
                    children=[
                        html.Span(
                            "LRT Lines:",
                            style={
                                "color": "#fff",
                                "fontWeight": "600",
                                "fontSize": "0.8125rem",
                                "whiteSpace": "nowrap",
                            }
                        ),
                        html.Div(
                            id="lrt-lines-display",
                            style={"width": "100%"},
                            children=[
                                html.P("Loading LRT line status...", 
                                       style={"color": "#999", "margin": "0", "fontSize": "0.75rem"})
                            ]
                        )
                    ]
                )
            ]
        ),
        # Hidden search bar section div (for tab navigation callback compatibility)
                html.Div(
                    id="search-bar-section",
            style={"display": "none"},
        ),

        # App Container ------------------------------------------#
        html.Div(
            id="app-container",
            children=[
                # Realtime weather page (hidden by default)
                realtime_weather_page(),
                # Weather indices page (hidden by default)
                weather_indices_page(),
                # Transport page (hidden by default)
                transport_page(),
                # Nearby transport page (hidden by default)
                nearby_transport_page(),
                # Main content area with map and right panel side by side
                html.Div(
                    id="main-content",
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "width": "100%",
                    },
                    children=[
                        html.Div(
                            id="main-content-area",
                            style={
                                "display": "flex",
                                "width": "100%",
                                "gap": "0.25rem",
                                "padding": "0.25rem",
                                "height": "calc(100vh - 6.25rem)",  # Adjusted for header only (search bar moved to map)
                                "alignItems": "stretch",  # Ensure both containers have same height
                                "boxSizing": "border-box",  # Ensure padding is included in width calculation
                            },
                    children=[
                        # Left container - Land Checkpoints
                        html.Div(
                            id="left-container",
                            style={
                                "width": "25%",
                                "display": "flex",
                                "flexDirection": "column",
                                "height": "100%",
                            },
                            children=[
                                html.Div(
                                    id="camera-feeds-section",
                                    style={
                                        "width": "100%",
                                        "height": "100%",
                                        "backgroundColor": "#000000",
                                        "borderRadius": "0.3125rem",
                                        "padding": "0",
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "justifyContent": "space-around",
                                        "flexWrap": "nowrap",
                                    },
                                    children=[
                                        html.H4(
                                            "Land Checkpoints",
                                            style={
                                                "textAlign": "center",
                                                "margin": "0.3125rem 0",
                                                "color": "#fff",
                                                "fontWeight": "700",
                                                "fontSize": "1.125rem"
                                            }
                                        ),
                                        html.Div(
                                            id="camera-2701-container",
                                            children=[
                                                html.Div(
                                                    style={
                                                        "width": "100%",
                                                        "flex": "1",
                                                        "minHeight": "0",
                                                        "overflow": "hidden",
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "center",
                                                        "backgroundColor": "#000",
                                                    },
                                                    id="camera-feed-2701-container",
                                                    children=[]
                                                ),
                                                html.Div(
                                                    id="camera-2701-metadata",
                                                    style={
                                                        "textAlign": "center",
                                                        "padding": "0.3125rem 0",
                                                        "fontSize": "0.75rem",
                                                        "color": "#ccc",
                                                    }
                                                ),
                                            ],
                                            style={
                                                "flex": "1",
                                                "padding": "0.625rem",
                                                "display": "flex",
                                                "flexDirection": "column",
                                                "minHeight": "0",
                                            }
                                        ),
                                        html.Div(
                                            id="camera-4713-container",
                                            children=[
                                                html.Div(
                                                    style={
                                                        "width": "100%",
                                                        "flex": "1",
                                                        "minHeight": "0",
                                                        "overflow": "hidden",
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "center",
                                                        "backgroundColor": "#000",
                                                    },
                                                    id="camera-feed-4713-container",
                                                    children=[]
                                                ),
                                                html.Div(
                                                    id="camera-4713-metadata",
                                                    style={
                                                        "textAlign": "center",
                                                        "padding": "0.3125rem 0",
                                                        "fontSize": "0.75rem",
                                                        "color": "#ccc",
                                                    }
                                                ),
                                            ],
                                            style={
                                                "flex": "1",
                                                "padding": "0.625rem",
                                                "display": "flex",
                                                "flexDirection": "column",
                                                "minHeight": "0",
                                            }
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        # Center container - Map
                        html.Div(
                            id="center-container",
                            style={
                                "width": "50%",
                                "display": "flex",
                                "flexDirection": "column",
                                "height": "100%",
                            },
                            children=[
                                # Toggle buttons above map (top left corner)
                                html.Div(
                                    style={
                                        "display": "flex",
                                        "justifyContent": "flex-start",
                                        "gap": "0.25rem",
                                        "marginBottom": "0.25rem",
                                        "padding": "0 0.25rem",
                                    },
                                    children=[
                                        html.Button(
                                            "📍 Regional PSI Info",
                                            id="toggle-psi-locations",
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
                                            }
                                        ),
                                        html.Button(
                                            "🌦️ Show 2H Forecast",
                                            id="toggle-2h-forecast",
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
                                            }
                                        ),
                                        html.Button(
                                            "🚆 MRT Crowd Level",
                                            id="toggle-mrt-crowd",
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
                                            }
                                        ),
                                        html.Button(
                                            "🚧 Show Traffic Incidents",
                                            id="toggle-main-traffic-incidents",
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
                                            }
                                        ),
                                    ]
                                ),
                                # Map container
                                html.Div(
                                    style={
                                        "width": "100%",
                                        "height": "100%",
                                        "minHeight": "0",
                                        "position": "relative",
                                    },
                                    children=[
                                        map_component(),
                                        # Traffic incidents legend overlay
                                        html.Div(
                                            id="main-traffic-incidents-legend",
                                            style={
                                                "position": "absolute",
                                                "top": "0.625rem",
                                                "right": "0.625rem",
                                                "backgroundColor": "rgba(26, 42, 58, 0.9)",
                                                "borderRadius": "0.5rem",
                                                "padding": "0.625rem",
                                                "zIndex": "1000",
                                                "boxShadow": "0 0.125rem 0.5rem rgba(0, 0, 0, 0.3)",
                                                "display": "none",  # Hidden by default, shown when toggle is on
                                            },
                                            children=[
                                                html.Div(
                                                    style={
                                                        "fontSize": "0.75rem",
                                                        "fontWeight": "600",
                                                        "color": "#fff",
                                                        "marginBottom": "0.5rem",
                                                        "borderBottom": "0.0625rem solid #4a5a6a",
                                                        "paddingBottom": "0.25rem",
                                                    },
                                                    children="Traffic Incidents Legend"
                                                ),
                                                html.Div(
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "marginBottom": "0.375rem",
                                                    },
                                                    children=[
                                                        html.Div(
                                                            style={
                                                                "width": "0.75rem",
                                                                "height": "0.9375rem",
                                                                "backgroundColor": "#FF6B00",
                                                                "border": "0.0625rem solid #FFA500",
                                                                "borderRadius": "0.125rem",
                                                                "marginRight": "0.5rem",
                                                                "position": "relative",
                                                            },
                                                            children=html.Div(
                                                                style={
                                                                    "position": "absolute",
                                                                    "top": "0.125rem",
                                                                    "left": "0.125rem",
                                                                    "right": "0.125rem",
                                                                    "height": "0.125rem",
                                                                    "backgroundColor": "#000",
                                                                }
                                                            )
                                                        ),
                                                        html.Span(
                                                            "Road Block",
                                                            style={
                                                                "color": "#fff",
                                                                "fontSize": "0.6875rem",
                                                            }
                                                        ),
                                                    ]
                                                ),
                                                html.Div(
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "marginBottom": "0.375rem",
                                                    },
                                                    children=[
                                                        html.Div(
                                                            style={
                                                                "width": "0",
                                                                "height": "0",
                                                                "borderLeft": "0.375rem solid transparent",
                                                                "borderRight": "0.375rem solid transparent",
                                                                "borderBottom": "0.625rem solid #FFA500",
                                                                "marginRight": "0.5rem",
                                                                "position": "relative",
                                                            },
                                                            children=html.Div(
                                                                style={
                                                                    "position": "absolute",
                                                                    "top": "0.125rem",
                                                                    "left": "-0.1875rem",
                                                                    "width": "0.375rem",
                                                                    "height": "0.375rem",
                                                                    "backgroundColor": "#FFD700",
                                                                    "borderRadius": "50%",
                                                                }
                                                            )
                                                        ),
                                                        html.Span(
                                                            "Road Work",
                                                            style={
                                                                "color": "#fff",
                                                                "fontSize": "0.6875rem",
                                                            }
                                                        ),
                                                    ]
                                                ),
                                                html.Div(
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "marginBottom": "0.375rem",
                                                    },
                                                    children=[
                                                        html.Div(
                                                            style={
                                                                "width": "0.75rem",
                                                                "height": "0.75rem",
                                                                "backgroundColor": "#FF9800",
                                                                "border": "0.0625rem solid #FF6B6B",
                                                                "borderRadius": "0.125rem",
                                                                "marginRight": "0.5rem",
                                                                "position": "relative",
                                                            },
                                                            children=[
                                                                html.Div(
                                                                    style={
                                                                        "position": "absolute",
                                                                        "top": "0.125rem",
                                                                        "left": "0.125rem",
                                                                        "width": "0.5rem",
                                                                        "height": "0.5rem",
                                                                        "backgroundColor": "#FFD700",
                                                                        "borderRadius": "0.0625rem",
                                                                    }
                                                                )
                                                            ]
                                                        ),
                                                        html.Span(
                                                            "Accident/Breakdown",
                                                            style={
                                                                "color": "#fff",
                                                                "fontSize": "0.6875rem",
                                                            }
                                                        ),
                                                    ]
                                                ),
                                                html.Div(
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "marginBottom": "0.375rem",
                                                    },
                                                    children=[
                                                        html.Div(
                                                            style={
                                                                "width": "0",
                                                                "height": "0",
                                                                "borderLeft": "0.375rem solid transparent",
                                                                "borderRight": "0.375rem solid transparent",
                                                                "borderTop": "0.5625rem solid #FF9800",
                                                                "marginRight": "0.5rem",
                                                                "position": "relative",
                                                            },
                                                            children=html.Div(
                                                                style={
                                                                    "position": "absolute",
                                                                    "top": "-0.4375rem",
                                                                    "left": "-0.0625rem",
                                                                    "width": "0.125rem",
                                                                    "height": "0.375rem",
                                                                    "backgroundColor": "#000",
                                                                }
                                                            )
                                                        ),
                                                        html.Span(
                                                            "Other Incidents",
                                                            style={
                                                                "color": "#fff",
                                                                "fontSize": "0.6875rem",
                                                            }
                                                        ),
                                                    ]
                                                ),
                                                html.Div(
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                    },
                                                    children=[
                                                        html.Div(
                                                            style={
                                                                "width": "0.75rem",
                                                                "height": "0.75rem",
                                                                "borderRadius": "50%",
                                                                "backgroundColor": "#FF8C00",
                                                                "marginRight": "0.5rem",
                                                            }
                                                        ),
                                                        html.Span(
                                                            "Faulty Traffic Lights",
                                                            style={
                                                                "color": "#fff",
                                                                "fontSize": "0.6875rem",
                                                            }
                                                        ),
                                                    ]
                                                ),
                                            ]
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        # Right container - PSI and 24-hour forecast
                        html.Div(
                            id="right-container",
                            style={
                                "width": "25%",
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "0.25rem",
                                "height": "100%",
                            },
                            children=[
                                # Incidents and Alerts container
                                html.Div(
                                    id="incidents-and-alerts",
                                    style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                        "gap": "0.25rem",
                                    },
                                    children=[
                                        # Flood alert metric card
                                        html.Div(
                                            id="main-flood-indicator-container",
                                            style={
                                                "backgroundColor": "#4a5a6a",
                                                "borderRadius": "0.5rem",
                                                "padding": "0.625rem",
                                                "display": "flex",
                                                "flexDirection": "column",
                                                "gap": "0.25rem",
                                                "flexShrink": "0",
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
                                                            "🌊 Number of latest flood alerts",
                                                            style={
                                                                "color": "#fff",
                                                                "fontWeight": "600",
                                                                "fontSize": "0.8125rem"
                                                            }
                                                        ),
                                                        html.Div(
                                                            id="main-flood-indicator-summary",
                                                            style={
                                                                "color": "#4169E1",
                                                                "fontSize": "1.125rem",
                                                                "fontWeight": "700",
                                                            },
                                                            children=[
                                                                html.Div(
                                                                    html.Span("--", style={"color": "#999"}),
                                                                    style={
                                                                        "backgroundColor": "rgb(58, 74, 90)",
                                                                        "padding": "0.25rem 0.5rem",
                                                                        "borderRadius": "0.25rem",
                                                                    }
                                                                )
                                                            ],
                                                        ),
                                                    ]
                                                ),
                                            ]
                                        ),
                                        # Lightning observations metric card
                                        create_metric_card(
                                            card_id="main-lightning-indicator-container",
                                            label="⚡ Lightning observations (past 5 mins)",
                                            value_id="main-lightning-indicator-summary",
                                            initial_value="--"
                                        ),
                                        # Average 24h PSI metric card
                                        create_metric_card(
                                            card_id="main-psi-24h-container",
                                            label="🌬️ Average 24H PSI across region",
                                            value_id="main-psi-24h-value",
                                            initial_value="--"
                                        ),
                                        # 24-hour Weather forecast section (as separate sibling container)
                                        html.Div(
                                            id="weather-forecast-24h-section",
                                            style={
                                                "backgroundColor": "#3a4a5a",
                                                "borderRadius": "0.5rem",
                                                "padding": "0.25rem",
                                                "display": "flex",
                                                "flexDirection": "column",
                                                "gap": "0.5rem",
                                                "flexShrink": "0",
                                            },
                                            children=[
                                                html.Div(
                                                    style={
                                                        "display": "flex",
                                                        "flexDirection": "row",
                                                        "alignItems": "center",
                                                        "justifyContent": "center",
                                                        "flexShrink": "0",
                                                    },
                                                    children=[
                                                        html.Span(
                                                            "🌤️ Next 24-Hour Forecast",
                                                            style={
                                                                "color": "#fff",
                                                                "fontWeight": "600",
                                                                "fontSize": "0.8125rem"
                                                            }
                                                        ),
                                                    ]
                                                ),
                                                html.Div(
                                                    id="weather-24h-content",
                                                    children=[
                                                        html.P("Loading...", style={"textAlign": "center",  "color": "#999"})
                                                    ],
                                                    style={
                                                        "flex": "1",
                                                        "display": "flex",
                                                        "flexDirection": "column",
                                                        "width": "100%",
                                                        "overflow": "hidden",
                                                        "minHeight": "0",
                                                        "minWidth": "0",
                                                    }
                                                ),
                                            ]
                                        ),
                                        # Traffic incidents alert (below)
                                        html.Div(
                                            id="main-traffic-incidents-container",
                                            style={
                                                "backgroundColor": "#3a4a5a",
                                                "borderRadius": "0.5rem",
                                                "padding": "0.25rem",
                                                "display": "flex",
                                                "flexDirection": "column",
                                                "gap": "0.5rem",
                                                "overflow": "hidden",
                                            },
                                            children=[
                                                html.Div(
                                                    style={
                                                        "display": "flex",
                                                        "flexDirection": "row",
                                                        "alignItems": "center",
                                                        "justifyContent": "center",
                                                    },
                                                    children=[
                                                        html.Span(
                                                            "🚦 Traffic incident/ traffic light issues",
                                                            style={
                                                                "color": "#fff",
                                                                "fontWeight": "600",
                                                                "fontSize": "0.8125rem"
                                                            }
                                                        ),
                                                    ]
                                                ),
                                                html.Div(
                                                    id="main-traffic-incidents-indicator",
                                                    style={
                                                        "flex": "1",
                                                        "overflowY": "auto",
                                                        "overflowX": "hidden",
                                                        "minHeight": "0",
                                                    },
                                                    children=[
                                                        html.P("Loading...", style={
                                                            "color": "#999",
                                                            "fontSize": "0.75rem"
                                                        })
                                                    ]
                                                )
                                            ]
                                        ),
                                        # Disease clusters count section (Dengue and Zika)
                                        html.Div(
                                            id="disease-clusters-section",
                                            style={
                                                "backgroundColor": "#3a4a5a",
                                                "borderRadius": "0.5rem",
                                                "padding": "0.25rem",
                                                "display": "flex",
                                                "flexDirection": "column",
                                                "gap": "0.5rem",
                                                "flexShrink": "0",
                                            },
                                            children=[
                                                html.Div(
                                                    style={
                                                        "display": "flex",
                                                        "flexDirection": "row",
                                                        "alignItems": "center",
                                                        "justifyContent": "center",
                                                    },
                                                    children=[
                                                        html.Span(
                                                            "🦠 Active Disease Clusters",
                                                            style={
                                                                "color": "#fff",
                                                                "fontWeight": "600",
                                                                "fontSize": "0.8125rem"
                                                            }
                                                        ),
                                                    ]
                                                ),
                                                # Disease clusters sub-container
                                                html.Div(
                                                    id="disease-clusters-indicator",
                                                    style={
                                                        "flex": "1",
                                                        "overflowY": "auto",
                                                        "overflowX": "hidden",
                                                        "minHeight": "0",
                                                    },
                                                    children=[
                                                        # Disease clusters in 2-column grid layout
                                                        html.Div(
                                                            style={
                                                                "display": "grid",
                                                                "gridTemplateColumns": "repeat(2, 1fr)",
                                                                "gap": "0.5rem",
                                                            },
                                                            children=[
                                                                # Dengue cluster count
                                                                html.Div(
                                                                    id="dengue-count-content",
                                                                    children=[
                                                                        html.P("Loading...", style={"textAlign": "center", "color": "#ccc", "fontSize": "0.75rem"})
                                                                    ],
                                                                ),
                                                                # Zika cluster count
                                                                html.Div(
                                                                    id="zika-count-content",
                                                                    children=[
                                                                        html.P("Loading...", style={"textAlign": "center", "color": "#ccc", "fontSize": "0.75rem"})
                                                                    ],
                                                                ),
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
                    ]
                ),
                # Footer with plotly|dash logo
                html.Div(
                    id="footer",
                    style={
                        "display": "flex",
                        "justifyContent": "flex-end",
                        "padding": "0.625rem 1.25rem",
                        "width": "100%",
                    },
                    children=[
                        html.A(
                            html.Img(
                                id="plotly-logo",
                                src=r"../assets/dash-logo.png",
                                style={"height": "1.875rem"},
                            ),
                            href="https://plotly.com/dash/",
                        ),
                    ],
                ),
            ]
        ),
                # Store for 2H forecast toggle state
                dcc.Store(id="2h-forecast-toggle-state", data=False),
                # Store for Regional PSI Info toggle state
                dcc.Store(id="psi-locations-toggle-state", data=False),
                # Store for MRT Crowd Level toggle state (default: disabled)
                dcc.Store(id="mrt-crowd-toggle-state", data=False),
                # Store for Traffic Incidents toggle state (default: disabled)
                dcc.Store(id="main-traffic-incidents-toggle-state", data=False),
                # Interval component to update images and weather periodically
                dcc.Interval(
                    id='interval-component',
                    interval=2*60*1000,  # Update every 2 minutes
                    n_intervals=0
                ),
                # Interval component for flood alerts (updates every 3 minutes)
                dcc.Interval(
                    id='flood-alert-interval',
                    interval=3*60*1000,  # Update every 3 minutes
                    n_intervals=0
                ),
            ],
        ),
    ]
)

# Expose server for Plotly Cloud deployment (gunicorn expects app:server)
server = app.server

if __name__ == '__main__':
    logging.info(sys.version)
    # Download HDB carpark data from initiate-download API on startup (only if file doesn't exist)
    print("Checking HDB carpark data on startup...")
    if download_hdb_carpark_csv(skip_if_exists=True):
        # Check if file was actually downloaded (not skipped)
        import os
        csv_path = os.path.join(os.path.dirname(__file__), 'data', 'HDBCarparkInformation.csv')
        if os.path.exists(csv_path):
            # File exists - clear cache to ensure fresh data is loaded
            print("HDB carpark data available (downloaded or already exists)")
            clear_carpark_locations_cache()
        else:
            print("HDB carpark data file not found after download attempt")
    else:
        print("Warning: Failed to download HDB carpark data. Using existing CSV file if available.")

    # Download speed camera data from initiate-download API on startup (only if file doesn't exist)
    print("Checking speed camera data on startup...")
    if download_speed_camera_csv(skip_if_exists=True):
        print("Speed camera data available (downloaded or already exists)")
    else:
        print("Warning: Failed to download speed camera data. Using existing CSV file if available.")

    # Initialize OneMap API token on application startup
    print("Initializing OneMap API authentication...")
    if initialize_onemap_token():
        print("OneMap API token initialized successfully")
    else:
        print("Warning: Failed to initialize OneMap API token. Some features may not work.")

    # Enable hot reloading to capture latest changes in code
    # If running locally in Anaconda env:
    if "conda-forge" in sys.version:
        app.run(debug=True, dev_tools_hot_reload=False)
    else:
        app.run(debug=True, dev_tools_hot_reload=False, host='0.0.0.0', port=8050)
    # Set app title
    app.title = "SG Dashboard"