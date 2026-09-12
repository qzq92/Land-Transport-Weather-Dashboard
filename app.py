import logging
import os
import sys

if sys.platform == "win32":
    # Remove SSLKEYLOGFILE if set (typically by Avast antivirus)
    # This variable points to an antivirus proxy and breaks OpenSSL initialization
    if "SSLKEYLOGFILE" in os.environ:
        del os.environ["SSLKEYLOGFILE"]

    # Force Python's OpenSSL to initialize first by importing ssl and accessing
    # OPENSSL_VERSION. This establishes the applink before C++ bindings load.
    import ssl
    import _ssl
    _ = _ssl.OPENSSL_VERSION
    _ = ssl.OPENSSL_VERSION  # Force initialization

    # Let requests/urllib3 verify certificates against the Windows certificate
    # store. This keeps Avast/corporate TLS inspection roots trusted without
    # disabling certificate verification.
    import truststore
    truststore.inject_into_ssl()

# Import packages
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
# Load environment variables and logging
load_dotenv(override=True)

from conf.page_layout_config import MAIN_DASHBOARD_HEIGHT, get_content_container_style, STANDARD_GAP

from components.banner_component import build_dashboard_banner
from components.mrt_line_status_banner import build_mrt_line_status_banner
from components.map_component import map_component
from components.metric_card import create_metric_card
from components.traffic_incidents_legend import build_traffic_incidents_legend
from conf.cache_config import INTERVAL_MAIN_MS, INTERVAL_FLOOD_MS
from callbacks.map_callback import register_search_callbacks
from callbacks.traffic_callback import register_camera_feed_callbacks
from callbacks.weather_callback import register_weather_callbacks
from callbacks.realtime_weather_callback import register_realtime_weather_callbacks
from callbacks.weather_indices_callback import (
    register_weather_indices_callbacks,
    initialize_disease_cluster_cache,
)
from callbacks.mrt_callback import register_mrt_callbacks
from callbacks.busstop_callbacks import register_busstop_callbacks
from callbacks.carpark_callback import register_carpark_callbacks
from callbacks.tab_navigation_callback import register_tab_navigation_callback
from callbacks.transport_callback import register_transport_callbacks
from callbacks.bus_arrival_callback import register_bus_arrival_callbacks
from callbacks.bus_service_callback import register_bus_service_callbacks
from callbacks.train_service_alerts_callback import register_train_service_alerts_callbacks
from callbacks.mrt_crowd_callback import register_mrt_crowd_callbacks
from callbacks.travel_times_callback import register_travel_times_callbacks
from callbacks.analytics_forecast_callback import register_analytics_forecast_callbacks
from callbacks.traffic_conditions_callback import register_traffic_conditions_callbacks
from utils.transport.ev import fetch_evc_batch_async
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
           title="Land Transport and Weather Dashboard"
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
register_travel_times_callbacks(app)
register_analytics_forecast_callbacks(app)
register_traffic_conditions_callbacks(app)
register_tab_navigation_callback(app)

# Warm disease cluster datasets once at startup to reduce poll-download bursts
# and avoid repeated 429 responses from upstream API.
initialize_disease_cluster_cache()

def _loading_placeholder():
    """Spinner shown while a tab page's layout is being built server-side."""
    return html.Div(
        "Loading…",
        style={
            "color": "#aaa",
            "textAlign": "center",
            "padding": "3rem",
            "fontSize": "0.875rem",
        },
    )


# Dashboard app layout ------------------------------------------------------#
app.layout = html.Div(
    id="root",
    style={
        "display": "flex",
        "flexDirection": "column",
        "minHeight": "100vh",
        "overflowY": "auto",
        "overflowX": "hidden",
    },
    children=[
        # Header/Banner -------------------------------------------------#
        html.Div(
            id="header",
            style={
                "flex": "0 0 auto",
                "minHeight": "0",
            },
            children=[
                html.Div(
                    id="banner",
                    className="banner",
                    style={
                        "height": "100%",
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "padding": "0 0.875rem",
                        "background": "linear-gradient(180deg, #1a202c 0%, #2d3748 100%)",
                        "borderBottom": "0.0625rem solid #4a5568",
                    },
                    children=build_dashboard_banner().children,
                ),
            ],
        ),
        # Rail Operational Status Banner --------------------------------#
        html.Div(
            build_mrt_line_status_banner(),
            style={
                "flex": "0 0 auto",
                "minHeight": "0",
            }
        ),
        # Hidden search bar section div (for tab navigation callback compatibility)
                html.Div(
                    id="search-bar-section",
            style={"display": "none"},
        ),

        # App Container ------------------------------------------#
        html.Div(
            id="app-container",
            style={
                "flex": "1 1 auto",
                "minHeight": "0",
                "display": "flex",
                "flexDirection": "column",
            },
            children=[
                # --- Lazy-loaded tab pages ---
                # Each page is an empty placeholder; its children are populated on
                # first visit by the lazy_load_tab callback in tab_navigation_callback.
                html.Div(id="realtime-weather-page", style={"display": "none"},
                         children=[_loading_placeholder()]),
                html.Div(id="weather-indices-page", style={"display": "none"},
                         children=[_loading_placeholder()]),
                html.Div(id="transport-page", style={"display": "none"},
                         children=[_loading_placeholder()]),
                html.Div(id="transit-page", style={"display": "none"},
                         children=[_loading_placeholder()]),
                html.Div(id="nearby-transport-page", style={"display": "none"},
                         children=[_loading_placeholder()]),
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
                                **get_content_container_style(gap=STANDARD_GAP, height=MAIN_DASHBOARD_HEIGHT),
                                "padding": "0.25rem",
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
                                        html.H5(
                                            "Land Checkpoints Traffic",
                                            style={
                                                "textAlign": "center",
                                                "margin": "0.2rem 0",
                                                "color": "#fff",
                                                "fontWeight": "700",
                                                "fontSize": "1rem"
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
                                                        "fontSize": "0.75rem",
                                                        "color": "#ccc",
                                                    }
                                                ),
                                            ],
                                            style={
                                                "flex": "1",
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
                                                        "fontSize": "0.75rem",
                                                        "color": "#ccc",
                                                    }
                                                ),
                                            ],
                                            style={
                                                "flex": "1",
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
                                        build_traffic_incidents_legend("main-traffic-incidents-legend"),
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
                                                        html.P("Loading...", style={"textAlign": "center", "color": "#ccc", "fontSize": "0.75rem"})
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
                # Tracks which tab pages have had their layout built (lazy-load)
                dcc.Store(id="initialized-tabs", data=[]),
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
                    interval=INTERVAL_MAIN_MS,
                    n_intervals=0
                ),
                # Interval component for flood alerts
                dcc.Interval(
                    id='flood-alert-interval',
                    interval=INTERVAL_FLOOD_MS,
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

    # Download EV charging points batch data on startup (only if file doesn't exist)
    print("Checking EV charging points batch data on startup...")
    try:
        evc_future = fetch_evc_batch_async(skip_if_exists=True)
        if evc_future:
            # Wait for the download to complete (non-blocking due to @run_in_thread)
            result = evc_future.result() if hasattr(evc_future, "result") else evc_future
            if result and result.get('success'):
                if result.get('skipped'):
                    print(f"EV charging points batch data available (file already exists)")
                else:
                    print(f"EV charging points batch data downloaded successfully")
                print(f"  File path: {result.get('file_path')}")
                print(f"  File size: {result.get('file_size', 0)} bytes")
                print(f"  Format: {result.get('format', 'unknown')}")
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                print(f"Warning: Failed to download EV charging points batch data: {error_msg}")
        else:
            print("Warning: Failed to initiate EV charging points batch data download.")
    except Exception as e:
        print(f"Warning: Error during EV charging points batch data download: {e}")
        import traceback
        traceback.print_exc()

    # Initialize OneMap API token on application startup
    print("Initializing OneMap API authentication...")
    if initialize_onemap_token():
        print("OneMap API token initialized successfully")
    else:
        print("Warning: Failed to initialize OneMap API token. Some features may not work.")

    # Set app title
    app.title = "Land Transport and Weather Dashboard"
    
    # Enable hot reloading to capture latest changes in code
    # If running locally in Anaconda env:
    if "conda-forge" in sys.version:
        app.run(debug=True, dev_tools_hot_reload=False)
    else:
        app.run(debug=True, dev_tools_hot_reload=False, host='0.0.0.0', port=8050)