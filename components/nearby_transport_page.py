"""
Component for the Nearby Transportation and Parking Info page.
Displays nearby transportation options and parking facilities.
"""
from dash import html, dcc
from conf.cache_config import INTERVAL_NEARBY_TRANSPORT_MS
import dash_leaflet as dl
from utils.map_utils import (
    get_onemap_attribution,
    SG_MAP_CENTER,
    SG_MAP_DEFAULT_ZOOM,
    SG_MAP_BOUNDS,
    ONEMAP_TILES_URL
)
from conf.page_layout_config import PAGE_PADDING, PAGE_HEIGHT, get_content_container_style, STANDARD_GAP
from components.nearby_list_items import nearby_empty_message

NEARBY_SUBTAB_STYLE = {
    "padding": "0.4rem 0.75rem",
    "backgroundColor": "#1a2a3a",
    "border": "none",
    "color": "#cbd5e1",
    "fontSize": "0.75rem",
    "fontWeight": "500",
}

NEARBY_SUBTAB_SELECTED_STYLE = {
    **NEARBY_SUBTAB_STYLE,
    "backgroundColor": "#334155",
    "color": "#fff",
    "fontWeight": "600",
    "borderBottom": "0.1875rem solid #60a5fa",
}

FACILITY_COLUMN_STYLE = {
    "width": "100%",
    "backgroundColor": "#2c3e50",
    "borderRadius": "0.3125rem",
    "padding": "0.75rem",
    "overflowX": "hidden",
}

TAB_GROUP_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "0.625rem",
}


def _facility_column(column_id):
    """Full-width list container; callbacks replace children after search."""
    return html.Div(
        id=column_id,
        style=FACILITY_COLUMN_STYLE,
        children=[nearby_empty_message()],
    )


def _amenity_toggle_button(button_id, label, color):
    return html.Button(
        label,
        id=button_id,
        n_clicks=0,
        style={
            "backgroundColor": "transparent",
            "border": f"0.125rem solid {color}",
            "borderRadius": "0.25rem",
            "color": color,
            "cursor": "pointer",
            "padding": "0.25rem 0.625rem",
            "fontSize": "0.75rem",
            "fontWeight": "600",
        },
    )


def _legend_item(color, label, emoji=None):
    swatch = html.Div(
        emoji or "",
        style={
            "width": "0.75rem" if not emoji else "1.25rem",
            "height": "0.75rem" if not emoji else "1.25rem",
            "borderRadius": "50%",
            "backgroundColor": color,
            "marginRight": "0.5rem",
            "flexShrink": "0",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "fontSize": "0.625rem",
            "border": "0.125rem solid #fff" if emoji else "none",
        },
    )
    return html.Div(
        [swatch, html.Span(label, style={"color": "#fff", "fontSize": "0.6875rem"})],
        style={"display": "flex", "alignItems": "center", "marginBottom": "0.25rem"},
    )


def _nearby_search_bar():
    return html.Div(
        id="nearby-transport-search-bar",
        style={
            "flexShrink": "0",
            "display": "flex",
            "flexDirection": "column",
            "gap": "0.5rem",
        },
        children=[
            html.Div(
                style={
                    "display": "flex",
                    "flexDirection": "row",
                    "flexWrap": "wrap",
                    "gap": "0.5rem",
                    "alignItems": "center",
                },
                children=[
                    dcc.Input(
                        id="nearby-transport-search-query",
                        type="text",
                        placeholder="Type an address, then press Enter",
                        n_submit=0,
                        debounce=False,
                        style={
                            "flex": "1",
                            "minWidth": "10rem",
                            "padding": "0.5rem 0.75rem",
                            "borderRadius": "0.375rem",
                            "border": "0.0625rem solid #5a6a7a",
                            "backgroundColor": "rgb(58, 74, 90)",
                            "color": "#fff",
                            "fontSize": "0.8125rem",
                        },
                    ),
                    html.Button(
                        "Search",
                        id="nearby-transport-search-btn",
                        n_clicks=0,
                        title="Search after you finish typing",
                        style={
                            "padding": "0.5rem 0.75rem",
                            "backgroundColor": "#4169E1",
                            "color": "#fff",
                            "border": "none",
                            "borderRadius": "0.375rem",
                            "cursor": "pointer",
                            "fontSize": "0.8125rem",
                            "fontWeight": "600",
                            "flexShrink": "0",
                        },
                    ),
                ],
            ),
            html.Div(
                id="nearby-transport-search-matches-wrap",
                className="nearby-search-matches-wrap",
                children=[
                    html.P(
                        "Matching locations appear after you press Enter",
                        className="nearby-search-matches-hint",
                    ),
                    dcc.RadioItems(
                        id="nearby-transport-search",
                        options=[],
                        value=None,
                        className="nearby-search-matches",
                    ),
                ],
            ),
        ],
    )


def _amenity_overlay_controls():
    return html.Div(
        id="nearby-transport-overlay-controls",
        style={
            "display": "flex",
            "gap": "0.5rem",
            "flexWrap": "wrap",
        },
        children=[
            _amenity_toggle_button(
                "nearby-hawker-centres-toggle-btn",
                "Show Hawker Centres",
                "#e11d48",
            ),
            _amenity_toggle_button("nearby-parks-toggle-btn", "Show Parks@SG", "#22c55e"),
            _amenity_toggle_button(
                "nearby-sports-fields-toggle-btn", "Show SportsFields@SG", "#a78bfa"
            ),
            _amenity_toggle_button(
                "nearby-recycling-bins-toggle-btn", "Show Recycling Bins", "#f97316"
            ),
        ],
    )


def _nearby_legend():
    return html.Div(
        id="nearby-transport-legend",
        style={
            "position": "absolute",
            "bottom": "0.625rem",
            "right": "0.625rem",
            "backgroundColor": "rgba(26, 42, 58, 0.9)",
            "borderRadius": "0.5rem",
            "padding": "0.5rem 0.625rem",
            "zIndex": "1000",
            "boxShadow": "0 0.125rem 0.5rem rgba(0, 0, 0, 0.3)",
            "minWidth": "10rem",
        },
        children=[
            html.Div(
                "Map Legend",
                style={
                    "fontSize": "0.75rem",
                    "fontWeight": "600",
                    "color": "#fff",
                    "marginBottom": "0.375rem",
                    "borderBottom": "0.0625rem solid #4a5a6a",
                    "paddingBottom": "0.25rem",
                },
            ),
            _legend_item("#4CAF50", "Bus Stop", emoji="🚌"),
            _legend_item("#FFA500", "Taxi Stand", emoji="🚕"),
            _legend_item("#4169E1", "MRT/LRT Station"),
            _legend_item("#60a5fa", "Carpark"),
            _legend_item("#9C27B0", "Bicycle Parking"),
            _legend_item("#81C784", "EV Charging Point"),
            _legend_item("#22c55e", "Parks@SG"),
            _legend_item("#a78bfa", "SportsFields@SG"),
            _legend_item("#f97316", "Recycling Bins"),
            _legend_item("#e11d48", "Hawker Centres"),
        ],
    )


def _nearby_map(sg_center, onemap_tiles_url, fixed_zoom, onemap_attribution, sg_bounds):
    return html.Div(
        style={
            "flex": "1",
            "minHeight": "0",
            "position": "relative",
            "backgroundColor": "#1a2a3a",
            "borderRadius": "0.5rem",
            "overflow": "hidden",
        },
        children=[
            dl.Map(
                id="nearby-transport-map",
                center=sg_center,
                zoom=fixed_zoom,
                minZoom=10,
                maxZoom=18,
                maxBounds=sg_bounds,
                maxBoundsViscosity=1.0,
                style={
                    "width": "100%",
                    "height": "100%",
                    "minHeight": "25rem",
                    "backgroundColor": "#1a2a3a",
                },
                children=[
                    dl.TileLayer(
                        url=onemap_tiles_url,
                        attribution=onemap_attribution,
                        maxNativeZoom=18,
                    ),
                    dl.LayerGroup(id="nearby-transport-search-marker"),
                    dl.LayerGroup(id="nearby-bus-stop-markers"),
                    dl.LayerGroup(id="nearby-mrt-markers"),
                    dl.LayerGroup(id="nearby-taxi-stand-markers"),
                    dl.LayerGroup(id="nearby-carpark-markers"),
                    dl.LayerGroup(id="nearby-bicycle-markers"),
                    dl.LayerGroup(id="nearby-ev-charging-markers"),
                    dl.LayerGroup(id="nearby-parks-markers"),
                    dl.LayerGroup(id="nearby-sports-fields-markers"),
                    dl.LayerGroup(id="nearby-recycling-bins-markers"),
                    dl.LayerGroup(id="nearby-hawker-centres-markers"),
                ],
                zoomControl=True,
                dragging=True,
                scrollWheelZoom=True,
            ),
            _nearby_legend(),
        ],
    )


def nearby_transport_page():
    """
    Create the Nearby Transportation and Parking Info page layout.
    Features: Nearby bus stops, MRT/LRT stations, taxi stands, carparks, bicycle parking, and EV charging points.

    Returns:
        HTML Div containing the Nearby Transportation and Parking Info section
    """
    sg_center = SG_MAP_CENTER
    onemap_tiles_url = ONEMAP_TILES_URL
    fixed_zoom = SG_MAP_DEFAULT_ZOOM
    onemap_attribution = get_onemap_attribution()
    sg_bounds = SG_MAP_BOUNDS

    return html.Div(
        id="nearby-transport-page",
        style={
            "display": "none",
            "padding": PAGE_PADDING,
            "height": PAGE_HEIGHT,
            "width": "100%",
        },
        children=[
            html.Div(
                id="nearby-transport-content",
                style=get_content_container_style(gap=STANDARD_GAP, height="100%"),
                children=[
                    html.Div(
                        id="nearby-transport-info-panel",
                        style={
                            "flex": "0 0 30rem",
                            "minWidth": "26rem",
                            "maxWidth": "32rem",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0.75rem",
                            "backgroundColor": "#1a2a3a",
                            "borderRadius": "0.5rem",
                            "padding": "0.9375rem",
                            "overflow": "hidden",
                            "height": "100%",
                        },
                        children=[
                            html.H3(
                                "Nearby Facilities",
                                style={
                                    "color": "#fff",
                                    "margin": "0",
                                    "fontSize": "1.125rem",
                                    "fontWeight": "600",
                                    "flexShrink": "0",
                                },
                            ),
                            _nearby_search_bar(),
                            dcc.Tabs(
                                id="nearby-facilities-tabs",
                                value="nearby-getting-around",
                                parent_style={
                                    "flex": "1",
                                    "minHeight": "0",
                                    "display": "flex",
                                    "flexDirection": "column",
                                },
                                style={"flexShrink": "0"},
                                content_style={
                                    "flex": "1",
                                    "minHeight": "0",
                                    "overflowY": "auto",
                                    "paddingTop": "0.5rem",
                                },
                                children=[
                                    dcc.Tab(
                                        label="Getting around",
                                        value="nearby-getting-around",
                                        style=NEARBY_SUBTAB_STYLE,
                                        selected_style=NEARBY_SUBTAB_SELECTED_STYLE,
                                        children=html.Div(
                                            style=TAB_GROUP_STYLE,
                                            children=[
                                                _facility_column("nearby-transport-bus-stop-column"),
                                                _facility_column("nearby-transport-mrt-column"),
                                                _facility_column("nearby-transport-taxi-stand-column"),
                                            ],
                                        ),
                                    ),
                                    dcc.Tab(
                                        label="Park and charge",
                                        value="nearby-park-and-charge",
                                        style=NEARBY_SUBTAB_STYLE,
                                        selected_style=NEARBY_SUBTAB_SELECTED_STYLE,
                                        children=html.Div(
                                            style=TAB_GROUP_STYLE,
                                            children=[
                                                _facility_column("nearby-transport-carpark-column"),
                                                _facility_column("nearby-transport-bicycle-column"),
                                                _facility_column("nearby-transport-ev-charging-column"),
                                            ],
                                        ),
                                    ),
                                    dcc.Tab(
                                        label="Food & Amenities",
                                        value="nearby-amenities",
                                        style=NEARBY_SUBTAB_STYLE,
                                        selected_style=NEARBY_SUBTAB_SELECTED_STYLE,
                                        children=html.Div(
                                            style=TAB_GROUP_STYLE,
                                            children=[
                                                _amenity_overlay_controls(),
                                                html.Div(
                                                    [
                                                        html.Strong(
                                                            "Food places",
                                                            style={
                                                                "color": "#fff",
                                                                "fontSize": "0.8125rem",
                                                            },
                                                        ),
                                                        html.P(
                                                            (
                                                                "Official NEA hawker-centre locations "
                                                                "near the selected place. Crowd levels, "
                                                                "ratings, and opening hours are not "
                                                                "inferred from this dataset."
                                                            ),
                                                            style={
                                                                "color": "#cbd5e1",
                                                                "fontSize": "0.6875rem",
                                                                "lineHeight": "1.4",
                                                                "margin": "0.25rem 0 0",
                                                            },
                                                        ),
                                                    ],
                                                    className="nearby-source-note",
                                                ),
                                                _facility_column("nearby-transport-parks-column"),
                                                _facility_column(
                                                    "nearby-transport-sports-fields-column"
                                                ),
                                                _facility_column(
                                                    "nearby-transport-recycling-bins-column"
                                                ),
                                                _facility_column(
                                                    "nearby-transport-hawker-centres-column"
                                                ),
                                            ],
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        id="nearby-transport-map-panel",
                        style={
                            "flex": "1",
                            "minWidth": "18rem",
                            "display": "flex",
                            "flexDirection": "column",
                            "height": "100%",
                            "minHeight": "0",
                        },
                        children=[
                            _nearby_map(
                                sg_center,
                                onemap_tiles_url,
                                fixed_zoom,
                                onemap_attribution,
                                sg_bounds,
                            ),
                        ],
                    ),
                ],
            ),
            dcc.Store(id="nearby-transport-location-store", data=None),
            dcc.Store(id="nearby-parks-toggle-state", data=False),
            dcc.Store(id="nearby-sports-fields-toggle-state", data=False),
            dcc.Store(id="nearby-recycling-bins-toggle-state", data=False),
            dcc.Store(id="nearby-hawker-centres-toggle-state", data=False),
            dcc.Interval(
                id="nearby-transport-interval",
                interval=INTERVAL_NEARBY_TRANSPORT_MS,
                n_intervals=0,
            ),
        ],
    )
