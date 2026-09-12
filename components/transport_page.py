"""
Component for the Transport Information page.
Displays transport-related information including taxi availability.
"""
from dash import html, dcc

from conf.cache_config import INTERVAL_EV_CHARGING_MS, INTERVAL_TRANSPORT_MS
from conf.page_layout_config import PAGE_HEIGHT, PAGE_PADDING
from components.traffic_conditions_page import traffic_conditions_view
from components.transport_metrics_view import transport_metrics_view
from components.travel_times_page import travel_times_view


TRANSPORT_SUBTAB_STYLE = {
    "padding": "0.5rem 1rem",
    "backgroundColor": "#1a2a3a",
    "border": "none",
    "color": "#cbd5e1",
    "fontSize": "0.8125rem",
    "fontWeight": "500",
}

TRANSPORT_SUBTAB_SELECTED_STYLE = {
    **TRANSPORT_SUBTAB_STYLE,
    "backgroundColor": "#334155",
    "color": "#fff",
    "fontWeight": "600",
    "borderBottom": "0.1875rem solid #60a5fa",
}


def transport_page():
    """
    Create the Transport Information page layout.

    Returns:
        HTML Div containing the Transport Information section
    """
    return html.Div(
        id="transport-page",
        style={
            "display": "none",
            "padding": PAGE_PADDING,
            "height": PAGE_HEIGHT,
            "width": "100%",
            "flexDirection": "column",
        },
        children=[
            dcc.Tabs(
                id="transport-sub-tabs",
                value="transport-metrics",
                style={
                    "height": "2.75rem",
                    "marginBottom": "0.375rem",
                    "flexShrink": "0",
                },
                children=[
                    dcc.Tab(
                        label="Metrics & Map",
                        value="transport-metrics",
                        style=TRANSPORT_SUBTAB_STYLE,
                        selected_style=TRANSPORT_SUBTAB_SELECTED_STYLE,
                    ),
                    dcc.Tab(
                        label="Expressway Travel Times",
                        value="transport-travel-times",
                        style=TRANSPORT_SUBTAB_STYLE,
                        selected_style=TRANSPORT_SUBTAB_SELECTED_STYLE,
                    ),
                    dcc.Tab(
                        label="Traffic Cameras",
                        value="transport-cameras",
                        style=TRANSPORT_SUBTAB_STYLE,
                        selected_style=TRANSPORT_SUBTAB_SELECTED_STYLE,
                    ),
                ],
            ),
            transport_metrics_view(),
            html.Div(
                id="transport-travel-times-view",
                style={
                    "display": "none",
                    "flex": "1",
                    "minHeight": "0",
                    "flexDirection": "column",
                },
                children=[travel_times_view()],
            ),
            html.Div(
                id="transport-cameras-view",
                style={
                    "display": "none",
                    "flex": "1",
                    "minHeight": "0",
                    "flexDirection": "column",
                },
                children=[traffic_conditions_view()],
            ),
            dcc.Store(id="taxi-toggle-state", data=False),
            dcc.Store(id="transport-bus-stops-toggle-state", data=False),
            dcc.Store(id="cctv-toggle-state", data=False),
            dcc.Store(id="erp-toggle-state", data=False),
            dcc.Store(id="speed-camera-toggle-state", data=False),
            dcc.Store(id="traffic-incidents-toggle-state", data=False),
            dcc.Store(id="vms-toggle-state", data=False),
            dcc.Store(id="ev-charging-toggle-state", data=False),
            dcc.Store(id="evc-batch-refresh-result", data=None),
            dcc.Interval(
                id="transport-interval",
                interval=INTERVAL_TRANSPORT_MS,
                n_intervals=0,
            ),
            dcc.Interval(
                id="transport-map-invalidate-interval",
                interval=300,
                n_intervals=0,
                max_intervals=1,
                disabled=True,
            ),
            dcc.Interval(
                id="ev-charging-interval",
                interval=INTERVAL_EV_CHARGING_MS,
                n_intervals=0,
            ),
        ],
    )
