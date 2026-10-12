"""Present normalized road and traffic-signal alerts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from dash import html


def format_alert_time(value: Optional[datetime]) -> str:
    """Format an LTA timestamp compactly for Singapore dashboard users."""
    if not value:
        return "time unavailable"
    return value.strftime("%d %b %Y, %H:%M")


def build_signal_alert_card(alert: Dict[str, Any]) -> html.Div:
    """Build a compact detail card for a normalized signal alert."""
    status = alert.get("status", "fault")
    status_label = "Maintenance" if status == "maintenance" else "Fault"
    timing = f"Since {format_alert_time(alert.get('start'))}"
    if status == "maintenance" and alert.get("end"):
        timing = (
            f"{format_alert_time(alert.get('start'))} – "
            f"{format_alert_time(alert.get('end'))}"
        )

    meta = [alert.get("type_label") or "Signal fault", timing]
    if alert.get("node_id"):
        meta.append(f"Node {alert['node_id']}")
    if alert.get("location_is_approximate"):
        meta.append("Approximate map location")

    return html.Div(
        className="traffic-alert-card",
        children=[
            html.Div(
                children=[
                    html.Span(
                        status_label,
                        className=(
                            "traffic-alert-badge "
                            f"traffic-alert-badge--{status}"
                        ),
                    ),
                    html.Span(
                        alert.get("location") or "Location unavailable",
                        className="traffic-alert-card-title",
                    ),
                ]
            ),
            html.Div(" · ".join(meta), className="traffic-alert-card-meta"),
        ],
    )


def build_incident_card(message: str) -> html.Div:
    """Build a compact road-incident card matching signal alert cards."""
    return html.Div(
        className="traffic-alert-card",
        children=[
            html.Div(
                children=[
                    html.Span(
                        "Incident",
                        className=(
                            "traffic-alert-badge traffic-alert-badge--maintenance"
                        ),
                    ),
                    html.Span(message, className="traffic-alert-card-title"),
                ]
            )
        ],
    )


def filter_alert_content(
    incidents: Iterable[Dict[str, Any]],
    signal_alerts: Iterable[Dict[str, Any]],
    selected_filter: str,
) -> List[html.Div]:
    """Build detail cards for the selected road-alert filter."""
    cards: List[html.Div] = []
    if selected_filter in ("all", "incidents"):
        for incident in incidents:
            if not isinstance(incident, dict):
                continue
            message = (
                incident.get("Message")
                or incident.get("Type")
                or "Unknown traffic incident"
            )
            cards.append(build_incident_card(str(message)))

    if selected_filter in ("all", "fault", "maintenance"):
        for alert in signal_alerts:
            if selected_filter in ("fault", "maintenance"):
                if alert.get("status") != selected_filter:
                    continue
            cards.append(build_signal_alert_card(alert))
    return cards
