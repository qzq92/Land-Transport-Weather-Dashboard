"""Compact air-quality scale and optional pollutant threshold guide."""
from dash import html

from conf.page_layout_config import STANDARD_GAP
from conf.weather_indices_config import (
    AIR_QUALITY_BANDS,
    POLLUTANT_ABBREVIATIONS,
    POLLUTANT_THRESHOLD_ROWS,
)


def _create_category_cell(color, range_text):
    """Create a table cell for a pollutant category range."""
    return html.Td(
        range_text,
        style={
            "textAlign": "center",
            "padding": "0.25rem 0.3rem",
            "borderBottom": "0.0625rem solid #2a2a2a",
            "color": color,
            "fontSize": "0.75rem",
            "fontWeight": "600",
        },
    )


def _build_psi_scale():
    """Build the public PSI colour strip."""
    return html.Div(
        id="psi-color-categories",
        className="air-quality-scale",
        children=[
            html.Div(
                "Air quality (PSI)",
                className="air-quality-scale-title",
            ),
            html.Div(
                className="air-quality-scale-bands",
                children=[
                    html.Div(
                        className="air-quality-scale-band",
                        children=[
                            html.Div(
                                className="air-quality-scale-swatch",
                                style={"backgroundColor": color},
                            ),
                            html.Div(label, className="air-quality-scale-label"),
                            html.Div(range_text, className="air-quality-scale-range"),
                        ],
                    )
                    for label, range_text, color in AIR_QUALITY_BANDS
                ],
            ),
            html.Div(
                "Colours match the PSI boxes on the map. Source: NEA.",
                className="air-quality-scale-source",
            ),
        ],
    )


def _build_threshold_table():
    """Build the specialist per-pollutant cutoff table."""
    header_cells = [
        html.Th(
            "Pollutant",
            style={
                "textAlign": "left",
                "padding": "0.25rem 0.3rem",
                "borderBottom": "0.0625rem solid #3a4a5a",
                "fontWeight": "600",
                "color": "#fff",
                "fontSize": "0.75rem",
            },
        )
    ]
    header_cells.extend(
        html.Th(
            label,
            style={
                "textAlign": "center",
                "padding": "0.25rem 0.3rem",
                "borderBottom": "0.0625rem solid #3a4a5a",
                "fontWeight": "600",
                "color": color,
                "fontSize": "0.6875rem",
            },
        )
        for label, _range, color in AIR_QUALITY_BANDS
    )

    body_rows = [
        html.Tr(
            children=[
                html.Td(
                    [html.Strong(name, style={"color": "#fff"}), f" ({unit})"],
                    style={
                        "padding": "0.25rem 0.3rem",
                        "borderBottom": "0.0625rem solid #2a2a2a",
                        "fontSize": "0.75rem",
                    },
                ),
                *[
                    _create_category_cell(color, range_text)
                    for range_text, (_label, _range, color) in zip(
                        ranges, AIR_QUALITY_BANDS
                    )
                ],
            ]
        )
        for name, unit, ranges in POLLUTANT_THRESHOLD_ROWS
    ]

    return html.Table(
        className="air-quality-threshold-table",
        style={
            "width": "100%",
            "color": "#ccc",
            "borderCollapse": "collapse",
        },
        children=[
            html.Thead(html.Tr(header_cells)),
            html.Tbody(body_rows),
        ],
    )


def _build_pollutant_guide():
    """Build the collapsed specialist guide for abbreviations and cutoffs."""
    abbreviation_items = [
        html.Span(
            [html.Strong(abbrev, style={"color": "#fff"}), f" = {meaning}"],
            style={"marginRight": "0.75rem", "whiteSpace": "nowrap"},
        )
        for abbrev, meaning in POLLUTANT_ABBREVIATIONS
    ]

    return html.Details(
        id="pollutant-legend",
        className="air-quality-guide",
        open=False,
        children=[
            html.Summary("How are these colours decided?"),
            html.Div(
                className="air-quality-guide-body",
                children=[
                    html.Div(
                        "Each pollutant uses the same five bands, with different cutoffs.",
                        className="air-quality-guide-intro",
                    ),
                    html.Div(
                        abbreviation_items,
                        className="air-quality-abbreviations",
                    ),
                    _build_threshold_table(),
                    html.Div(
                        "Pollutant cutoffs follow WHO/EPA air quality bands. PSI bands follow NEA.",
                        className="air-quality-scale-source",
                    ),
                ],
            ),
        ],
    )


def build_air_quality_legend_column():
    """
    Build the Daily Health legend column.

    The PSI table toggle still writes to psi-metrics-table-container; that
    block stays outside the collapsed guide so it remains visible.
    """
    return html.Div(
        id="weather-indices-legend-column",
        style={
            "flex": "1",
            "minWidth": "16rem",
            "maxWidth": "26rem",
            "display": "flex",
            "flexDirection": "column",
            "gap": STANDARD_GAP,
            "minHeight": "0",
        },
        children=[
            html.Div(
                id="psi-metrics-table-container",
                style={
                    "display": "none",
                    "marginBottom": "0.5rem",
                    "flexShrink": "0",
                    "overflowX": "auto",
                },
                children=[
                    html.Div(
                        id="psi-metrics-table-content",
                        children=[
                            html.P(
                                "Loading PSI data...",
                                style={
                                    "color": "#ccc",
                                    "textAlign": "center",
                                    "padding": "0.75rem",
                                },
                            )
                        ],
                    ),
                ],
            ),
            _build_psi_scale(),
            _build_pollutant_guide(),
        ],
    )
