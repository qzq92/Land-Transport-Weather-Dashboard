"""
Component for the estimated travel times page.
Displays expressway travel times from LTA DataMall API.
"""
from dash import html, dcc
from conf.page_layout_config import PAGE_PADDING, PAGE_HEIGHT


def travel_times_page():
    """
    Create the estimated travel times page layout.
    Displays a table of expressway travel times.

    Returns:
        HTML Div containing the travel times page
    """
    return html.Div(
        id="travel-times-page",
        style={
            "display": "none",  # Hidden by default
            "padding": PAGE_PADDING,
            "height": PAGE_HEIGHT,
            "width": "100%",
        },
        children=[
            html.Div(
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "height": "100%",
                    "gap": "0.75rem",
                },
                children=[
                    # Header
                    html.Div(
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "space-between",
                            "padding": "0.5rem 1rem",
                            "backgroundColor": "#1a2a3a",
                            "borderRadius": "0.5rem",
                            "borderBottom": "0.0625rem solid #4a5a6a",
                        },
                        children=[
                            html.H4(
                                "🚗 Estimated Expressway Travel Times",
                                style={
                                    "margin": "0",
                                    "color": "#fff",
                                    "fontWeight": "600",
                                    "fontSize": "1.125rem",
                                }
                            ),
                            html.Span(
                                id="travel-times-last-updated",
                                style={
                                    "color": "#999",
                                    "fontSize": "0.75rem",
                                }
                            ),
                        ]
                    ),
                    # Table container
                    html.Div(
                        id="travel-times-table-container",
                        style={
                            "flex": "1",
                            "backgroundColor": "#2a3a4a",
                            "borderRadius": "0.5rem",
                            "padding": "1rem",
                            "overflowY": "auto",
                        },
                        children=[
                            html.P(
                                "Loading travel times...",
                                style={
                                    "color": "#999",
                                    "textAlign": "center",
                                    "fontSize": "0.875rem",
                                }
                            )
                        ]
                    ),
                    # Interval for auto-refresh
                    dcc.Interval(
                        id="travel-times-interval",
                        interval=2 * 60 * 1000,  # Update every 2 minutes
                        n_intervals=0
                    ),
                ]
            )
        ]
    )

