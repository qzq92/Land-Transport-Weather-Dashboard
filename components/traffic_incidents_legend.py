"""Shared traffic incidents legend component for map overlays."""

from dash import html


_INCIDENT_ITEMS = [
    (
        "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB4PSIyIiB5PSIyIiB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIGZpbGw9IiNEQzI2MjYiIHN0cm9rZT0iIzk5MUIxQiIgc3Ryb2tlLXdpZHRoPSIyIiByeD0iMiIvPjxsaW5lIHgxPSI2IiB5MT0iNiIgeDI9IjE4IiB5Mj0iMTgiIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSIzIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48bGluZSB4MT0iMTgiIHkxPSI2IiB4Mj0iNiIgeTI9IjE4IiBzdHJva2U9IiNGRkZGRkYiIHN0cm9rZS13aWR0aD0iMyIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+PHJlY3QgeD0iNCIgeT0iNCIgd2lkdGg9IjE2IiBoZWlnaHQ9IjE2IiBmaWxsPSJub25lIiBzdHJva2U9IiNGRkZGRkYiIHN0cm9rZS13aWR0aD0iMS41IiByeD0iMSIvPjwvc3ZnPg==",
        "Road Block",
        {"width": "1.5rem", "height": "1.5rem"},
        {"width": "1.5rem", "height": "1.5rem"},
    ),
    (
        "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjgiIHZpZXdCb3g9IjAgMCAyMCAyOCIgZXhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTSAxMCAyIEwgMTggMjYgTCAyIDI2IFoiIGZpbGw9IiNGOTczMTYiIHN0cm9rZT0iI0VBNTgwQyIgc3Ryb2tlLXdpZHRoPSIxLjUiLz48cGF0aCBkPSJNIDEwIDYgTCAxNiAyNCBMIDQgMjQgWiIgZmlsbD0iI0ZCOTIzQyIvPjxyZWN0IHg9IjYiIHk9IjEwIiB3aWR0aD0iOCIgaGVpZ2h0PSIyIiBmaWxsPSIjRkZGRkZGIiByeD0iMSIvPjxyZWN0IHg9IjYiIHk9IjE0IiB3aWR0aD0iOCIgaGVpZ2h0PSIyIiBmaWxsPSIjRkZGRkZGIiByeD0iMSIvPjxyZWN0IHg9IjYiIHk9IjE4IiB3aWR0aD0iOCIgaGVpZ2h0PSIyIiBmaWxsPSIjRkZGRkZGIiByeD0iMSIvPjxjaXJjbGUgY3g9IjEwIiBjeT0iMjgiIHI9IjIiIGZpbGw9IiMxRjI5MzciLz48L3N2Zz4=",
        "Road Work",
        {"width": "1.25rem", "height": "1.75rem"},
        {"width": "1.25rem", "height": "1.75rem"},
    ),
    (
        "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMSIgZmlsbD0iI0VGNjQ0NCIgc3Ryb2tlPSIjREMyNjI2IiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNIDYgMTQgTCA2IDE4IEwgMTggMTggTCAxOCAxNCBMIDE1IDEwIEwgOSAxMCBaIiBmaWxsPSIjRkZGRkZGIiBzdHJva2U9IiMxRjI5MzciIHN0cm9rZS13aWR0aD0iMS41Ii8+PGNpcmNsZSBjeD0iOSIgY3k9IjE4IiByPSIyIiBmaWxsPSIjMUYyOTM3Ii8+PGNpcmNsZSBjeD0iMTUiIGN5PSIxOCIgcj0iMiIgZmlsbD0iIzFGMjkzNyIvPjxwYXRoIGQ9Ik0gOCAxMCBMIDkgNyBMIDE1IDcgTCAxNiAxMCIgZmlsbD0iI0ZFRjNDNyIgc3Ryb2tlPSIjMUYyOTM3IiBzdHJva2Utd2lkdGg9IjEiLz48bGluZSB4MT0iMTIiIHkxPSI3IiB4Mj0iMTIiIHkyPSIxMCIgc3Ryb2tlPSIjREMyNjI2IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjxsaW5lIHgxPSIxMiIgeTE9IjUiIHgyPSIxMiIgeTI9IjMiIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48Y2lyY2xlIGN4PSIxMiIgY3k9IjIiIHI9IjEiIGZpbGw9IiNGRkZGRkYiLz48L3N2Zz4=",
        "Accident/Breakdown",
        {"width": "1.5rem", "height": "1.5rem"},
        {"width": "1.5rem", "height": "1.5rem"},
    ),
    (
        "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNIDEyIDIgTCAyMiAyMCBMIDIgMjAgWiIgZmlsbD0iI0ZDRDM0RCIgc3Ryb2tlPSIjRjU5RTAwQiIgc3Ryb2tlLXdpZHRoPSIyIi8+PHBhdGggZD0iTSAxMiA2IEwgMTIgMTQiIHN0cm9rZT0iIzkyNDAwRSIgc3Ryb2tlLXdpZHRoPSIyLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTciIHI9IjEuNSIgZmlsbD0iIzkyNDAwRSIvPjwvc3ZnPg==",
        "Other Incidents",
        {"width": "1.5rem", "height": "1.5rem"},
        {"width": "1.5rem", "height": "1.5rem"},
    ),
    (
        "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyMCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB4PSI2IiB5PSIyIiB3aWR0aD0iOCIgaGVpZ2h0PSIxOCIgZmlsbD0iIzFGMjkzNyIgc3Ryb2tlPSIjMzc0MTUxIiBzdHJva2Utd2lkdGg9IjEuNSIgcng9IjEiLz48Y2lyY2xlIGN4PSIxMCIgY3k9IjciIHI9IjIuNSIgZmlsbD0iI0VGNjQ0NCIvPjxjaXJjbGUgY3g9IjEwIiBjeT0iMTIiIHI9IjIuNSIgZmlsbD0iI0ZDRDM0RCIvPjxjaXJjbGUgY3g9IjEwIiBjeT0iMTciIHI9IjIuNSIgZmlsbD0iIzEwQjk4MSIgZmlsbC1vcGFjaXR5PSIwLjMiLz48cmVjdCB4PSI4IiB5PSIyMCIgd2lkdGg9IjQiIGhlaWdodD0iMiIgZmlsbD0iIzFGMjkzNyIgcng9IjAuNSIvPjxsaW5lIHgxPSIxMCIgeTE9IjciIHgyPSIxMCIgeTI9IjciIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSIxIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48bGluZSB4MT0iMTAiIHkxPSIxMiIgeDI9IjEwIiB5Mj0iMTIiIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSIxIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48L3N2Zz4=",
        "Signal faults (red) / maintenance (amber)",
        {"width": "1.25rem", "height": "1.5rem"},
        {"width": "1.25rem", "height": "1.5rem"},
    ),
]


def build_traffic_incidents_legend(legend_id: str) -> html.Div:
    """Build a hidden-by-default overlay legend for traffic incidents."""
    legend_rows = []
    for index, (icon_src, label, icon_wrapper_style, icon_image_style) in enumerate(_INCIDENT_ITEMS):
        row_style = {
            "display": "flex",
            "alignItems": "center",
        }
        if index < len(_INCIDENT_ITEMS) - 1:
            row_style["marginBottom"] = "0.375rem"

        legend_rows.append(
            html.Div(
                style=row_style,
                children=[
                    html.Div(
                        style={
                            **icon_wrapper_style,
                            "marginRight": "0.5rem",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                        },
                        children=html.Img(src=icon_src, style=icon_image_style),
                    ),
                    html.Span(
                        label,
                        style={
                            "color": "#fff",
                            "fontSize": "0.6875rem",
                        },
                    ),
                ],
            )
        )

    return html.Div(
        id=legend_id,
        style={
            "position": "absolute",
            "top": "0.625rem",
            "right": "0.625rem",
            "backgroundColor": "rgba(26, 42, 58, 0.9)",
            "borderRadius": "0.5rem",
            "padding": "0.625rem",
            "zIndex": "1000",
            "boxShadow": "0 0.125rem 0.5rem rgba(0, 0, 0, 0.3)",
            "display": "none",
        },
        children=[
            html.Div(
                "Road Alerts Legend",
                style={
                    "fontSize": "0.75rem",
                    "fontWeight": "600",
                    "color": "#fff",
                    "marginBottom": "0.5rem",
                    "borderBottom": "0.0625rem solid #4a5a6a",
                    "paddingBottom": "0.25rem",
                },
            ),
            *legend_rows,
        ],
    )
