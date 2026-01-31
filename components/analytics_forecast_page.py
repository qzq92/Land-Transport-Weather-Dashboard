"""
Component for the analytics and forecast page.
"""
from dash import html, dcc
from conf.page_layout_config import PAGE_PADDING, PAGE_HEIGHT


# Train line options for dropdown
TRAIN_LINE_OPTIONS = [
    {'label': '-- Select a train line --', 'value': ''},
    {'label': 'Circle Line (CCL)', 'value': 'CCL'},
    {'label': 'Circle Line Extension (CEL)', 'value': 'CEL'},
    {'label': 'Changi Airport Line (CGL)', 'value': 'CGL'},
    {'label': 'Downtown Line (DTL)', 'value': 'DTL'},
    {'label': 'East-West Line (EWL)', 'value': 'EWL'},
    {'label': 'North-East Line (NEL)', 'value': 'NEL'},
    {'label': 'North-South Line (NSL)', 'value': 'NSL'},
    {'label': 'Bukit Panjang LRT (BPL)', 'value': 'BPL'},
    {'label': 'Sengkang LRT (SLRT)', 'value': 'SLRT'},
    {'label': 'Punggol LRT (PLRT)', 'value': 'PLRT'},
    {'label': 'Thomson-East Coast Line (TEL)', 'value': 'TEL'},
]


def analytics_forecast_page():
    """
    Create the analytics and forecast page layout.

    Returns:
        HTML Div containing the analytics and forecast page
    """
    return html.Div(
        id="analytics-forecast-page",
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
                    # Header with dropdown
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
                            html.Div(
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "gap": "1rem",
                                },
                                children=[
                                    html.H4(
                                        "📊 MRT/LRT Crowd Forecast",
                                        style={
                                            "margin": "0",
                                            "color": "#fff",
                                            "fontWeight": "600",
                                            "fontSize": "1.125rem",
                                        }
                                    ),
                                    html.Label(
                                        "Select Train Line:",
                                        style={
                                            "color": "#fff",
                                            "fontWeight": "500",
                                            "fontSize": "0.875rem",
                                        }
                                    ),
                                    dcc.Dropdown(
                                        id="trainline-selector",
                                        options=TRAIN_LINE_OPTIONS,
                                        value='',  # Default to blank (no selection)
                                        clearable=False,
                                        style={
                                            "width": "15rem",
                                        },
                                    ),
                                ]
                            ),
                        ]
                    ),
                    # Chart area
                    html.Div(
                        id="analytics-forecast-content",
                        style={
                            "flex": "1",
                            "backgroundColor": "#2a3a4a",
                            "borderRadius": "0.5rem",
                            "padding": "1rem",
                            "overflowY": "auto",
                        },
                        children=[]  # Will be populated by callback
                    ),
                ]
            )
        ]
    )

