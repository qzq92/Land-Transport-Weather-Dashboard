# Import packages
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import sys
import logging
from dotenv import load_dotenv
# Load environment variables and logging
load_dotenv(override=True)

from conf.page_layout_config import MAIN_DASHBOARD_HEIGHT, get_content_container_style, STANDARD_GAP

from components.banner_component import build_dashboard_banner
from components.mrt_line_status_banner import build_mrt_line_status_banner
from components.map_component import map_component
from components.realtime_weather_page import realtime_weather_page
from components.weather_indices_page import weather_indices_page
from components.transport_page import transport_page
from components.nearby_transport_page import nearby_transport_page
from components.travel_times_page import travel_times_page
from components.analytics_forecast_page import analytics_forecast_page
from components.traffic_conditions_page import traffic_conditions_page
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
from callbacks.travel_times_callback import register_travel_times_callbacks
from callbacks.analytics_forecast_callback import register_analytics_forecast_callbacks
from callbacks.transport_callback import register_traffic_conditions_callbacks
from auth.onemap_api import initialize_onemap_token
from utils.data_download_helper import (
    download_hdb_carpark_csv,
    download_speed_camera_csv
)
from callbacks.carpark_callback import clear_carpark_locations_cache
from callbacks.transport_callback import fetch_evc_batch_async


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
                # Realtime weather page (hidden by default)
                realtime_weather_page(),
                # Weather indices page (hidden by default)
                weather_indices_page(),
                # Transport page (hidden by default)
                transport_page(),
                # Nearby transport page (hidden by default)
                nearby_transport_page(),
                # Travel times page (hidden by default)
                travel_times_page(),
                # Analytics and forecast page (hidden by default)
                analytics_forecast_page(),
                # Traffic conditions page (hidden by default)
                traffic_conditions_page(),
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
                                                                "width": "1.5rem",
                                                                "height": "1.5rem",
                                                                "marginRight": "0.5rem",
                                                                "display": "flex",
                                                                "alignItems": "center",
                                                                "justifyContent": "center",
                                                            },
                                                            children=html.Img(
                                                                src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB4PSIyIiB5PSIyIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIGZpbGw9IiNEQzI2MjYiIHN0cm9rZT0iIzk5MUIxQiIgc3Ryb2tlLXdpZHRoPSIyIiByeD0iMiIvPjxsaW5lIHgxPSI2IiB5MT0iNiIgeDI9IjE4IiB5Mj0iMTgiIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSIzIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48bGluZSB4MT0iMTgiIHkxPSI2IiB4Mj0iNiIgeTI9IjE4IiBzdHJva2U9IiNGRkZGRkYiIHN0cm9rZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+PHJlY3QgeD0iNCIgeT0iNCIgd2lkdGg9IjE2IiBoZWlnaHQ9IjE2IiBmaWxsPSJub25lIiBzdHJva2U9IiNGRkZGRkYiIHN0cm9rZS13aWR0aD0iMS41IiByeD0iMSIvPjwvc3ZnPg==",
                                                                style={"width": "1.5rem", "height": "1.5rem"}
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
                                                                "width": "1.25rem",
                                                                "height": "1.75rem",
                                                                "marginRight": "0.5rem",
                                                                "display": "flex",
                                                                "alignItems": "center",
                                                                "justifyContent": "center",
                                                            },
                                                            children=html.Img(
                                                                src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjgiIHZpZXdCb3g9IjAgMCAyMCAyOCIgZXhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTSAxMCAyIEwgMTggMjYgTCAyIDI2IFoiIGZpbGw9IiNGOTczMTYiIHN0cm9rZT0iI0VBNTgwQyIgc3Ryb2tlLXdpZHRoPSIxLjUiLz48cGF0aCBkPSJNIDEwIDYgTCAxNiAyNCBMIDQgMjQgWiIgZmlsbD0iI0ZCOTIzQyIvPjxyZWN0IHg9IjYiIHk9IjEwIiB3aWR0aD0iOCIgaGVpZ2h0PSIyIiBmaWxsPSIjRkZGRkZGIiByeD0iMSIvPjxyZWN0IHg9IjYiIHk9IjE0IiB3aWR0aD0iOCIgaGVpZ2h0PSIyIiBmaWxsPSIjRkZGRkZGIiByeD0iMSIvPjxyZWN0IHg9IjYiIHk9IjE4IiB3aWR0aD0iOCIgaGVpZ2h0PSIyIiBmaWxsPSIjRkZGRkZGIiByeD0iMSIvPjxjaXJjbGUgY3g9IjEwIiBjeT0iMjgiIHI9IjIiIGZpbGw9IiMxRjI5MzciLz48L3N2Zz4=",
                                                                style={"width": "1.25rem", "height": "1.75rem"}
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
                                                                "width": "1.5rem",
                                                                "height": "1.5rem",
                                                                "marginRight": "0.5rem",
                                                                "display": "flex",
                                                                "alignItems": "center",
                                                                "justifyContent": "center",
                                                            },
                                                            children=html.Img(
                                                                src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMSIgZmlsbD0iI0VGNjQ0NCIgc3Ryb2tlPSIjREMyNjI2IiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNIDYgMTQgTCA2IDE4IEwgMTggMTggTCAxOCAxNCBMIDE1IDEwIEwgOSAxMCBaIiBmaWxsPSIjRkZGRkZGIiBzdHJva2U9IiMxRjI5MzciIHN0cm9rZS13aWR0aD0iMS41Ii8+PGNpcmNsZSBjeD0iOSIgY3k9IjE4IiByPSIyIiBmaWxsPSIjMUYyOTM3Ii8+PGNpcmNsZSBjeD0iMTUiIGN5PSIxOCIgcj0iMiIgZmlsbD0iIzFGMjkzNyIvPjxwYXRoIGQ9Ik0gOCAxMCBMIDkgNyBMIDE1IDcgTCAxNiAxMCIgZmlsbD0iI0ZFRjNDNyIgc3Ryb2tlPSIjMUYyOTM3IiBzdHJva2Utd2lkdGg9IjEiLz48bGluZSB4MT0iMTIiIHkxPSI3IiB4Mj0iMTIiIHkyPSIxMCIgc3Ryb2tlPSIjREMyNjI2IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjxsaW5lIHgxPSIxMiIgeTE9IjUiIHgyPSIxMiIgeTI9IjMiIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48Y2lyY2xlIGN4PSIxMiIgY3k9IjIiIHI9IjEiIGZpbGw9IiNGRkZGRkYiLz48L3N2Zz4=",
                                                                style={"width": "1.5rem", "height": "1.5rem"}
                                                            )
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
                                                                "width": "1.5rem",
                                                                "height": "1.5rem",
                                                                "marginRight": "0.5rem",
                                                                "display": "flex",
                                                                "alignItems": "center",
                                                                "justifyContent": "center",
                                                            },
                                                            children=html.Img(
                                                                src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNIDEyIDIgTCAyMiAyMCBMIDIgMjAgWiIgZmlsbD0iI0ZDRDM0RCIgc3Ryb2tlPSIjRjU5RTAwQiIgc3Ryb2tlLXdpZHRoPSIyIi8+PHBhdGggZD0iTSAxMiA2IEwgMTIgMTQiIHN0cm9rZT0iIzkyNDAwRSIgc3Ryb2tlLXdpZHRoPSIyLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTciIHI9IjEuNSIgZmlsbD0iIzkyNDAwRSIvPjwvc3ZnPg==",
                                                                style={"width": "1.5rem", "height": "1.5rem"}
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
                                                                "width": "1.25rem",
                                                                "height": "1.5rem",
                                                                "marginRight": "0.5rem",
                                                                "display": "flex",
                                                                "alignItems": "center",
                                                                "justifyContent": "center",
                                                            },
                                                            children=html.Img(
                                                                src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyMCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB4PSI2IiB5PSIyIiB3aWR0aD0iOCIgaGVpZ2h0PSIxOCIgZmlsbD0iIzFGMjkzNyIgc3Ryb2tlPSIjMzc0MTUxIiBzdHJva2Utd2lkdGg9IjEuNSIgcng9IjEiLz48Y2lyY2xlIGN4PSIxMCIgY3k9IjciIHI9IjIuNSIgZmlsbD0iI0VGNjQ0NCIvPjxjaXJjbGUgY3g9IjEwIiBjeT0iMTIiIHI9IjIuNSIgZmlsbD0iI0ZDRDM0RCIvPjxjaXJjbGUgY3g9IjEwIiBjeT0iMTciIHI9IjIuNSIgZmlsbD0iIzEwQjk4MSIgZmlsbC1vcGFjaXR5PSIwLjMiLz48cmVjdCB4PSI4IiB5PSIyMCIgd2lkdGg9IjQiIGhlaWdodD0iMiIgZmlsbD0iIzFGMjkzNyIgcng9IjAuNSIvPjxsaW5lIHgxPSIxMCIgeTE9IjciIHgyPSIxMCIgeTI9IjciIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSIxIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48bGluZSB4MT0iMTAiIHkxPSIxMiIgeDI9IjEwIiB5Mj0iMTIiIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSIxIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48L3N2Zz4=",
                                                                style={"width": "1.25rem", "height": "1.5rem"}
                                                            )
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