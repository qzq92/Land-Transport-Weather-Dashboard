"""Compact list rows and empty states for Nearby Facilities."""

from typing import Any, List, Optional, Union

from dash import html

NEARBY_EMPTY_COPY = "Search an address to see the nearest 5."

_TITLE_STYLE = {
    "textAlign": "center",
    "marginBottom": "0.5rem",
    "color": "#fff",
    "fontWeight": "700",
    "fontSize": "0.875rem",
}

_EMPTY_STYLE = {
    "textAlign": "center",
    "color": "#999",
    "fontSize": "0.75rem",
    "fontStyle": "italic",
    "padding": "0.5rem 0.25rem",
    "margin": "0",
}

_ROW_STYLE = {
    "padding": "0.5rem 0.625rem",
    "marginBottom": "0.375rem",
    "backgroundColor": "#1a1a1a",
    "borderRadius": "0.25rem",
}

_NAME_STYLE = {
    "fontSize": "0.8125rem",
    "color": "#fff",
    "fontWeight": "600",
}

_DISTANCE_STYLE = {
    "fontSize": "0.75rem",
    "color": "#60a5fa",
    "fontWeight": "500",
}

_EXTRA_STYLE = {
    "fontSize": "0.6875rem",
    "fontWeight": "600",
    "color": "#cbd5e1",
}


def nearby_section_title(title: str) -> html.H4:
    """Section heading used at the top of each nearby list."""
    return html.H4(title, style=_TITLE_STYLE)


def nearby_empty_message(text: Optional[str] = None) -> html.P:
    """Placeholder shown before a location is chosen, or for a simple empty note."""
    return html.P(text or NEARBY_EMPTY_COPY, style=_EMPTY_STYLE)


def nearby_compact_row(
    name: str,
    distance_text: str,
    extra: Optional[Union[str, html.Span, html.Div]] = None,
    leading: Optional[Any] = None,
) -> html.Div:
    """Name (optional badge/lots) on line 1, distance only on line 2."""
    name_row: List[Any] = []
    if leading is not None:
        name_row.append(leading)
    name_row.append(html.Span(name, style=_NAME_STYLE))
    if extra is not None:
        if isinstance(extra, str):
            name_row.append(html.Span(extra, style=_EXTRA_STYLE))
        else:
            name_row.append(extra)

    return html.Div(
        [
            html.Div(
                name_row,
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "0.5rem",
                    "flexWrap": "wrap",
                    "marginBottom": "0.125rem",
                },
            ),
            html.Div(distance_text, style=_DISTANCE_STYLE),
        ],
        style=_ROW_STYLE,
    )
