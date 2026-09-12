"""Compact, globally visible MRT and LRT service-status summary."""
from dash import html


def build_mrt_line_status_banner():
    """Create the rail summary and an expandable all-lines status region."""
    return html.Div(
        id="rail-status-banner",
        className="rail-status-banner",
        children=[
            html.Div(
                className="rail-status-primary",
                children=[
                    html.Span(
                        "Rail service:",
                        className="rail-status-label",
                    ),
                    html.Div(
                        id="rail-status-summary",
                        className="rail-status-summary",
                        children=[
                            html.Span(
                                "Updating rail status…",
                                className="rail-status-updating",
                            )
                        ],
                    ),
                ],
            ),
            html.Span(
                id="rail-status-updated",
                className="rail-status-updated",
                children="Updating",
            ),
            html.Details(
                id="rail-status-details",
                className="rail-status-details",
                children=[
                    html.Summary("View all lines"),
                    html.Div(
                        className="rail-status-expanded",
                        children=[
                            html.Section(
                                children=[
                                    html.H3("MRT"),
                                    html.Div(
                                        id="mrt-lines-display",
                                        className="rail-line-grid",
                                        children="Updating MRT status…",
                                    ),
                                ],
                            ),
                            html.Section(
                                children=[
                                    html.H3("LRT"),
                                    html.Div(
                                        id="lrt-lines-display",
                                        className="rail-line-grid",
                                        children="Updating LRT status…",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

