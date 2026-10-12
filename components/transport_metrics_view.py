"""Metrics & Map view: compact left rail plus a full-height map."""

from dash import dcc, html
import dash_leaflet as dl

from components.traffic_incidents_legend import build_traffic_incidents_legend
from utils.map_utils import (
    ONEMAP_TILES_URL,
    SG_MAP_BOUNDS,
    SG_MAP_CENTER,
    SG_MAP_DEFAULT_ZOOM,
    get_onemap_attribution,
)
LAYER_CHIP_LABELS = {
    "taxi": "Taxi",
    "cctv": "Cameras",
    "erp": "ERP",
    "incidents": "Road alerts",
    "vms": "VMS",
    "speed": "Speed",
    "ev": "EV",
    "bus": "Bus stops",
}

_CHIP_STYLE = {
    "backgroundColor": "transparent",
    "borderRadius": "0.25rem",
    "cursor": "pointer",
    "padding": "0.2rem 0.5rem",
    "fontSize": "0.75rem",
    "fontWeight": "600",
}


def _metric_tile(card_id, label, value_id, value_color, extra=None):
    """Compact label-plus-value tile used in the two-column grid."""
    children = [
        html.Span(label, className="transport-metric-label"),
        html.Div(
            id=value_id,
            className="transport-metric-value",
            style={"color": value_color},
            children=[
                html.Span("--", style={"color": "#94a3b8"}),
            ],
        ),
    ]
    if extra:
        children.extend(extra)
    return html.Div(id=card_id, className="transport-metric-tile", children=children)


def _metrics_grid():
    return html.Div(
        className="transport-metrics-grid",
        children=[
            _metric_tile(
                "taxi-availability-card",
                "Taxi / stands",
                "taxi-count-value",
                "#FFD700",
            ),
            _metric_tile("cctv-card", "Cameras", "cctv-count-value", "#4CAF50"),
            _metric_tile(
                "speed-camera-card",
                "Speed cams",
                "speed-camera-count-value",
                "#A5D6A7",
            ),
            _metric_tile("erp-card", "ERP", "erp-count-value", "#FF6B6B"),
            _metric_tile("vms-card", "VMS", "vms-count-value", "#C0C0C0"),
            _metric_tile(
                "ev-charging-points-card",
                "EV points",
                "ev-charging-points-count-value",
                "#87CEEB",
            ),
            _metric_tile(
                "traffic-incidents-card",
                "Road alerts",
                "traffic-incidents-count-value",
                "#FF9800",
                extra=[
                    dcc.RadioItems(
                        id="traffic-alert-filter",
                        options=[
                            {"label": "All", "value": "all"},
                            {"label": "Incidents", "value": "incidents"},
                            {"label": "Faults", "value": "fault"},
                            {"label": "Maintenance", "value": "maintenance"},
                        ],
                        value="all",
                        inline=True,
                        className="traffic-alert-filters",
                        inputClassName="traffic-alert-filter-input",
                        labelClassName="traffic-alert-filter-label",
                    ),
                    html.Div(
                        id="traffic-incidents-messages",
                        className="traffic-alert-list",
                        style={"display": "none"},
                    ),
                    html.Div(
                        id="traffic-alerts-freshness",
                        className="traffic-alerts-freshness",
                    ),
                ],
            ),
            _metric_tile(
                "bus-stops-card",
                "Bus stops",
                "bus-stops-count-value",
                "#4169E1",
                extra=[
                    html.Div(
                        id="bus-stops-disclaimer",
                        style={"display": "none"},
                        children=[
                            html.P(
                                "Bus stop markers may sit off the kerb during road works.",
                                className="transport-metric-note",
                            )
                        ],
                    )
                ],
            ),
            _metric_tile(
                "bus-services-card",
                "Bus services",
                "bus-services-count-value",
                "#4169E1",
            ),
        ],
    )


def _advisory_block():
    return dcc.Loading(
        id="train-advisory-loading",
        type="circle",
        color="#60a5fa",
        parent_style={"flex": "1", "minHeight": "8rem", "display": "flex"},
        children=html.Div(
            id="train-advisory-panel",
            className="transport-advisory-panel",
            children=[
                html.Div(
                    id="train-service-alerts-card",
                    className="transport-advisory-card",
                    children=[
                        html.Span(
                            "Train advisories",
                            className="transport-advisory-title",
                        ),
                        html.Div(
                            id="train-service-alerts-content",
                            className="transport-advisory-body",
                            children=[
                                html.P(
                                    "All service running fine",
                                    className="transport-advisory-empty",
                                )
                            ],
                        ),
                    ],
                )
            ],
        ),
    )


def _metrics_rail():
    return html.Div(
        className="transport-metrics-rail-wrap",
        children=dcc.Loading(
            id="transport-metrics-loading",
            type="circle",
            color="#60a5fa",
            children=html.Div(
                id="transport-info-panel",
                className="transport-metrics-rail",
                children=[_metrics_grid(), _advisory_block()],
            ),
        ),
    )


def _layer_chip(label, button_id, color, title):
    return html.Button(
        label,
        id=button_id,
        n_clicks=0,
        title=title,
        className="transport-layer-chip",
        style={**_CHIP_STYLE, "border": f"0.125rem solid {color}", "color": color},
    )


def _layer_toggles():
    return html.Div(
        id="transport-toggle-buttons-container",
        className="transport-layer-chips",
        children=[
            _layer_chip(
                LAYER_CHIP_LABELS["taxi"],
                "taxi-toggle-btn",
                "#FFD700",
                "Show Current Taxi Availability/Stands",
            ),
            _layer_chip(
                LAYER_CHIP_LABELS["cctv"],
                "cctv-toggle-btn",
                "#4CAF50",
                "Show LTA Traffic Cameras Location",
            ),
            _layer_chip(
                LAYER_CHIP_LABELS["erp"],
                "erp-toggle-btn",
                "#FF6B6B",
                "Show ERP Gantries Location",
            ),
            _layer_chip(
                LAYER_CHIP_LABELS["incidents"],
                "traffic-incidents-toggle-btn",
                "#FF9800",
                "Show road incidents and traffic signal alerts",
            ),
            _layer_chip(
                LAYER_CHIP_LABELS["vms"],
                "vms-toggle-btn",
                "#C0C0C0",
                "Show VMS Display boards Locations",
            ),
            _layer_chip(
                LAYER_CHIP_LABELS["speed"],
                "speed-camera-toggle-btn",
                "#81C784",
                "Show SPF Speed Camera Locations",
            ),
            _layer_chip(
                LAYER_CHIP_LABELS["ev"],
                "ev-charging-toggle-btn",
                "#87CEEB",
                "Show EV Charging Points",
            ),
            _layer_chip(
                LAYER_CHIP_LABELS["bus"],
                "transport-bus-stops-toggle-btn",
                "#4169E1",
                "Show Bus Stop Locations",
            ),
        ],
    )


def _taxi_legend():
    return html.Div(
        id="taxi-legend",
        className="transport-map-legend",
        style={"display": "none"},
        children=[
            html.Div("Taxi Legend", className="transport-map-legend-title"),
            html.Div(
                className="transport-map-legend-row",
                children=[
                    html.Div(className="transport-map-legend-dot"),
                    html.Span("Taxi Locations"),
                ],
            ),
            html.Div(
                className="transport-map-legend-row",
                children=[
                    html.Div(className="transport-map-legend-stand"),
                    html.Span("Taxi Stands"),
                ],
            ),
        ],
    )


def _map_panel():
    return html.Div(
        id="transport-map-panel",
        className="transport-map-panel",
        children=[
            _layer_toggles(),
            html.Div(
                className="transport-map-frame",
                children=[
                    dl.Map(
                        id="transport-map",
                        center=SG_MAP_CENTER,
                        zoom=SG_MAP_DEFAULT_ZOOM,
                        minZoom=10,
                        maxZoom=18,
                        maxBounds=SG_MAP_BOUNDS,
                        maxBoundsViscosity=1.0,
                        style={"width": "100%", "height": "100%", "backgroundColor": "#1a2a3a"},
                        children=[
                            dl.TileLayer(
                                url=ONEMAP_TILES_URL,
                                attribution=get_onemap_attribution(),
                                maxNativeZoom=18,
                            ),
                            dl.LayerGroup(id="taxi-markers"),
                            dl.LayerGroup(id="cctv-markers"),
                            dl.LayerGroup(id="erp-markers"),
                            dl.LayerGroup(id="speed-camera-markers"),
                            dl.LayerGroup(id="traffic-incidents-markers"),
                            dl.LayerGroup(id="vms-markers"),
                            dl.LayerGroup(id="ev-charging-markers"),
                            dl.LayerGroup(id="transport-bus-stops-markers"),
                        ],
                        zoomControl=True,
                        dragging=True,
                        scrollWheelZoom=True,
                    ),
                    _taxi_legend(),
                    build_traffic_incidents_legend("traffic-incidents-legend"),
                    html.Div(
                        id="transport-bus-stop-zoom-message",
                        className="transport-bus-stop-zoom",
                        style={"display": "none"},
                        children="Zoom in to level 15+ to view bus stops",
                    ),
                ],
            ),
        ],
    )


def transport_metrics_view():
    """Build the two-column Metrics & Map view."""
    return html.Div(
        id="transport-metrics-view",
        className="transport-metrics-view",
        style={
            "display": "flex",
            "flex": "1",
            "minHeight": "0",
            "flexDirection": "column",
        },
        children=[
            html.Div(
                id="transport-content",
                className="transport-metrics-content",
                children=[_metrics_rail(), _map_panel()],
            )
        ],
    )
