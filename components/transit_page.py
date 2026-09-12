"""Combined rail crowd forecast and bus information page."""

from dash import dcc, html

from components.analytics_forecast_page import analytics_forecast_view
from components.bus_arrival_page import bus_arrival_view
from conf.page_layout_config import PAGE_HEIGHT, PAGE_PADDING


TRANSIT_SUBTAB_STYLE = {
    "padding": "0.5rem 1rem",
    "backgroundColor": "#1a2a3a",
    "border": "none",
    "color": "#cbd5e1",
    "fontSize": "0.8125rem",
    "fontWeight": "500",
}

TRANSIT_SUBTAB_SELECTED_STYLE = {
    **TRANSIT_SUBTAB_STYLE,
    "backgroundColor": "#334155",
    "color": "#fff",
    "fontWeight": "600",
    "borderBottom": "0.1875rem solid #60a5fa",
}


def transit_page():
    """Create Transit with crowd forecast and bus-search inner views."""
    return html.Div(
        id="transit-page",
        style={
            "display": "none",
            "padding": PAGE_PADDING,
            "height": PAGE_HEIGHT,
            "width": "100%",
            "flexDirection": "column",
        },
        children=[
            dcc.Tabs(
                id="transit-sub-tabs",
                value="transit-crowd",
                style={
                    "height": "2.75rem",
                    "marginBottom": "0.375rem",
                    "flexShrink": "0",
                },
                children=[
                    dcc.Tab(
                        label="Station Crowd Forecast",
                        value="transit-crowd",
                        style=TRANSIT_SUBTAB_STYLE,
                        selected_style=TRANSIT_SUBTAB_SELECTED_STYLE,
                    ),
                    dcc.Tab(
                        label="Bus Arrivals & Services",
                        value="transit-bus",
                        style=TRANSIT_SUBTAB_STYLE,
                        selected_style=TRANSIT_SUBTAB_SELECTED_STYLE,
                    ),
                ],
            ),
            analytics_forecast_view(),
            bus_arrival_view(),
        ],
    )
