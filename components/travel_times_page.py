"""
Component for the estimated travel times page.
Displays expressway travel times from LTA DataMall API.
"""
from dash import html, dcc
from conf.cache_config import INTERVAL_TRAVEL_TIMES_MS
from components.travel_times_board import EXPRESSWAY_FILTER_OPTIONS


def travel_times_view():
    """Create the reusable estimated expressway travel-times view."""
    return html.Div(
        className="travel-times-page",
        children=[
            html.Div(
                className="travel-times-toolbar",
                children=[
                    html.H4("Estimated Expressway Travel Times"),
                    dcc.Dropdown(
                        id="travel-times-expressway-filter",
                        options=EXPRESSWAY_FILTER_OPTIONS,
                        value="all",
                        clearable=False,
                        style={"width": "16rem", "fontSize": "0.8125rem"},
                    ),
                    html.Span(
                        id="travel-times-last-updated",
                        className="travel-times-updated",
                    ),
                ],
            ),
            html.Div(
                id="travel-times-table-container",
                className="travel-times-table",
                children=[
                    html.P(
                        "Loading travel times...",
                        style={
                            "color": "#94a3b8",
                            "textAlign": "center",
                            "fontSize": "0.875rem",
                        },
                    )
                ],
            ),
            dcc.Interval(
                id="travel-times-interval",
                interval=INTERVAL_TRAVEL_TIMES_MS,
                n_intervals=0,
                disabled=True,
            ),
        ]
    )
