"""Always-visible expressway travel-time timetable."""

from collections import defaultdict

from dash import html

EXPRESSWAY_NAMES = {
    "AYE": "Ayer Rajah",
    "BKE": "Bukit Timah",
    "CTE": "Central",
    "ECP": "East Coast",
    "KJE": "Kranji",
    "KPE": "Kallang–Paya Lebar",
    "MCE": "Marina Coastal",
    "PIE": "Pan Island",
    "SLE": "Seletar",
    "TPE": "Tampines",
}
EXPRESSWAY_FILTER_OPTIONS = (
    [{"label": "All expressways", "value": "all"}]
    + [
        {"label": f"{code} · {name}", "value": code}
        for code, name in EXPRESSWAY_NAMES.items()
    ]
)
_DIRECTION_RANK = {"West": 0, "East": 1, "North": 0, "South": 1}


def format_expressway_exit_label(expressway, exit_name):
    """Return 'ECP (ROCHOR RD)' from an expressway code and exit."""
    code = str(expressway or "").strip() or "N/A"
    exit_text = str(exit_name or "").strip() or "N/A"
    return f"{code} ({exit_text})"


def format_route_destination_label(destination, direction_text):
    """Return a destination line such as 'to MAXWELL RD · (East)'."""
    dest = str(destination or "").strip() or "N/A"
    direction = str(direction_text or "").strip()
    if direction:
        return f"to {dest} · ({direction})"
    return f"to {dest}"


def congestion_level(est_time):
    """Classify one stretch: clear (<5 min), slower (5-10), slow (>10)."""
    try:
        duration = float(est_time)
    except (ValueError, TypeError):
        return "slower"
    if duration < 5:
        return "clear"
    if duration <= 10:
        return "slower"
    return "slow"


def group_summaries_by_expressway(summaries):
    """Group direction summaries by expressway code, then West/East or North/South."""
    buckets = defaultdict(list)
    for summary in summaries:
        buckets[summary["expressway"]].append(summary)

    known = [code for code in EXPRESSWAY_NAMES if code in buckets]
    extra = sorted(code for code in buckets if code not in EXPRESSWAY_NAMES)
    grouped = []
    for code in known + extra:
        routes = sorted(
            buckets[code],
            key=lambda item: (
                _DIRECTION_RANK.get(item.get("direction_text"), 99),
                str(item.get("direction_text", "")),
            ),
        )
        grouped.append((code, routes))
    return grouped


def _format_minutes(est_time):
    try:
        return f"{float(est_time):.0f} min"
    except (ValueError, TypeError):
        return f"{est_time} min"


def _timeline(summary):
    """Render origin plus hop pills for every chain on a direction."""
    expressway = summary["expressway"]
    nodes = []
    for chain_index, chain in enumerate(summary.get("chains") or []):
        if chain_index:
            nodes.append(html.Span(className="travel-times-chain-break"))
        for hop_index, segment in enumerate(chain):
            if hop_index == 0:
                nodes.append(
                    html.Span(
                        format_expressway_exit_label(
                            expressway,
                            segment.get("StartPoint", "N/A"),
                        ),
                        className="travel-times-exit travel-times-exit--origin",
                    )
                )
            level = congestion_level(segment.get("EstTime"))
            nodes.append(
                html.Span(
                    _format_minutes(segment.get("EstTime", "N/A")),
                    className=f"travel-times-pill travel-times-pill--{level}",
                )
            )
            nodes.append(
                html.Span(
                    segment.get("EndPoint", "N/A"),
                    className="travel-times-exit",
                )
            )
    return html.Div(nodes, className="travel-times-timeline")


def _direction_row(summary):
    return html.Div(
        className="travel-times-direction",
        children=[
            html.Span(
                summary.get("direction_text") or summary.get("direction") or "—",
                className="travel-times-direction-label",
            ),
            _timeline(summary),
            html.Span(
                f"{summary.get('total_time', 0):.0f} min",
                className="travel-times-total",
            ),
        ],
    )


def _expressway_section(code, routes):
    full_name = EXPRESSWAY_NAMES.get(code, "")
    return html.Div(
        className="travel-times-section",
        children=[
            html.Div(
                className="travel-times-section-header",
                children=[
                    html.Span(code, className="travel-times-section-code"),
                    html.Span(full_name, className="travel-times-section-name")
                    if full_name
                    else None,
                ],
            ),
            html.Div(
                [_direction_row(route) for route in routes],
                className="travel-times-directions",
            ),
        ],
    )


def build_travel_times_legend():
    """Quiet sample pills that explain stretch colours."""
    return html.Div(
        className="travel-times-legend",
        children=[
            html.Span("2 min", className="travel-times-pill travel-times-pill--clear"),
            html.Span("clear", className="travel-times-legend-label"),
            html.Span("6 min", className="travel-times-pill travel-times-pill--slower"),
            html.Span("slower", className="travel-times-legend-label"),
            html.Span("12 min", className="travel-times-pill travel-times-pill--slow"),
            html.Span("slow", className="travel-times-legend-label"),
        ],
    )


def build_travel_times_board(summaries):
    """Render grouped, always-visible direction timelines."""
    sections = [
        _expressway_section(code, routes)
        for code, routes in group_summaries_by_expressway(summaries)
    ]
    return html.Div(
        className="travel-times-board",
        children=[
            build_travel_times_legend(),
            html.Div(sections, className="travel-times-sections"),
        ],
    )
