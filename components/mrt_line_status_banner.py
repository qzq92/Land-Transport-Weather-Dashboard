"""
Component for displaying MRT and LRT line service status banner.
Shows real-time operational status for all train lines.
"""
from dash import html


def build_mrt_line_status_banner():
    """
    Create the MRT/LRT line service status banner component.
    
    Returns:
        HTML Div containing the rail operational status banner with MRT and LRT line displays
    """
    return html.Div(
        id="rail-status-banner",
        style={
            "backgroundColor": "#1a2a3a",
            "padding": "0.125rem 1rem",
            "borderBottom": "0.0625rem solid #4a5a6a",
            "width": "100%",
            "display": "flex",
            "flexDirection": "row",
            "alignItems": "flex-start",
            "justifyContent": "space-between",
            "minHeight": "1.5rem",
            "gap": "0.25rem",
        },
        children=[
            # Left column: MRT Lines (70% width)
            html.Div(
                style={
                    "flex": "6.5",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "0.25rem",
                },
                children=[
                    html.Span(
                        "MRT Lines Service Statuses:",
                        style={
                            "color": "#fff",
                            "fontWeight": "600",
                            "fontSize": "0.8rem",
                            "whiteSpace": "nowrap",
                        }
                    ),
                    html.Div(
                        id="mrt-lines-display",
                        style={"width": "100%"},
                        children=[
                            html.P(
                                "Loading MRT line status...",
                                style={"color": "#999", "margin": "0", "fontSize": "0.75rem"}
                            )
                        ]
                    )
                ]
            ),
            # Right column: LRT Lines (30% width)
            html.Div(
                style={
                    "flex": "3.5",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "0.25rem",
                },
                children=[
                    html.Span(
                        "LRT Lines Service Statuses:",
                        style={
                            "color": "#fff",
                            "fontWeight": "600",
                            "fontSize": "0.8rem",
                            "whiteSpace": "nowrap",
                        }
                    ),
                    html.Div(
                        id="lrt-lines-display",
                        style={"width": "100%"},
                        children=[
                            html.P(
                                "Loading LRT line status...",
                                style={"color": "#999", "margin": "0", "fontSize": "0.75rem"}
                            )
                        ]
                    )
                ]
            )
        ]
    )

