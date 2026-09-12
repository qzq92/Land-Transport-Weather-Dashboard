"""
Component for the Traffic Conditions page.
Displays all LTA traffic camera feeds in a grid layout.
"""
from dash import html, dcc
from conf.cache_config import INTERVAL_TRAFFIC_CONDITIONS_MS


def traffic_conditions_view():
    """Create the reusable LTA traffic-camera conditions view."""
    return html.Div(
        style={
            "display": "flex",
            "flexDirection": "column",
            "height": "100%",
            "gap": "0.75rem",
        },
        children=[
            html.Div(
                id="traffic-conditions-content",
                style={
                    "flex": "1",
                    "backgroundColor": "#2a3a4a",
                    "borderRadius": "0.5rem",
                    "padding": "1rem",
                    "overflowY": "auto",
                },
                children=[],
            ),
            dcc.Interval(
                id='traffic-conditions-interval',
                interval=INTERVAL_TRAFFIC_CONDITIONS_MS,
                n_intervals=0,
                disabled=True,
            ),
        ]
    )

