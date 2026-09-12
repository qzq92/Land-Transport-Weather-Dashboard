"""Callbacks for the Traffic Conditions page."""

from datetime import datetime

from dash import Input, Output, html, no_update

from utils.transport.cameras import fetch_traffic_cameras, parse_traffic_camera_data
from utils.transport.cache import load_lta_camera_id_mapping


def register_traffic_conditions_callbacks(app):
    """Register callbacks for the traffic conditions page."""

    @app.callback(
        Output("traffic-conditions-content", "children"),
        [Input("traffic-conditions-interval", "n_intervals"),
         Input("navigation-tabs", "value"),
         Input("transport-sub-tabs", "value")],
    )
    def update_traffic_conditions_grid(n_intervals: int, tab_value: str, sub_tab: str) -> html.Div:
        """Update traffic conditions grid with all available LTA camera feeds."""
        _ = n_intervals
        if tab_value != "transport" or sub_tab != "transport-cameras":
            return no_update

        try:
            data = fetch_traffic_cameras()
            camera_data = parse_traffic_camera_data(data)
            if not camera_data:
                return _message("No traffic camera data available")
        except Exception as error:
            print(f"Error fetching traffic camera data: {error}")
            return _message(f"Error loading traffic camera data: {error}", color="#ff6b6b")

        camera_id_mapping = load_lta_camera_id_mapping()
        camera_cards = []

        for camera_id, info in sorted(camera_data.items(), key=lambda item: item[0]):
            image_url = info.get("image_url", "")
            timestamp = info.get("timestamp", "")
            location_desc = camera_id_mapping.get(str(camera_id), f"Camera {camera_id}")
            datetime_text = _format_timestamp(timestamp)

            camera_cards.append(
                html.Div(
                    style={
                        "backgroundColor": "#1a2a3a",
                        "borderRadius": "0.5rem",
                        "padding": "0.5rem",
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "0.5rem",
                        "border": "0.125rem solid #3a4a5a",
                    },
                    children=[
                        html.Div(
                            style={
                                "width": "100%",
                                "backgroundColor": "#000",
                                "borderRadius": "0.25rem",
                                "overflow": "hidden",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                            },
                            children=[
                                html.Img(
                                    src=image_url if image_url else _no_image_svg(),
                                    alt=f"Camera {camera_id}",
                                    style={
                                        "width": "100%",
                                        "height": "auto",
                                        "display": "block",
                                    },
                                )
                            ],
                        ),
                        html.Div(
                            location_desc,
                            style={
                                "color": "#fff",
                                "fontSize": "0.75rem",
                                "fontWeight": "500",
                                "textAlign": "center",
                                "lineHeight": "1.3",
                                "minHeight": "2.5rem",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                            },
                        ),
                        html.Div(
                            datetime_text if datetime_text else "Time: N/A",
                            style={
                                "color": "#999",
                                "fontSize": "0.625rem",
                                "textAlign": "center",
                            },
                        ),
                    ],
                )
            )

        return html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(4, 1fr)",
                "gap": "1rem",
                "width": "100%",
            },
            children=camera_cards,
        )


def _format_timestamp(timestamp) -> str:
    if not timestamp:
        return ""
    try:
        parsed_datetime = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        return parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return str(timestamp)


def _message(text: str, color: str = "#999") -> html.Div:
    return html.Div(
        html.P(
            text,
            style={
                "textAlign": "center",
                "color": color,
                "padding": "2rem",
                "fontSize": "0.875rem",
            },
        )
    )


def _no_image_svg() -> str:
    return (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
        "width='100' height='100'%3E%3Ctext x='50%25' y='50%25' "
        "text-anchor='middle' dy='.3em' fill='%23999'%3ENo Image%3C/text%3E%3C/svg%3E"
    )
