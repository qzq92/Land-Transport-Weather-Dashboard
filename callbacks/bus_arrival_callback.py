"""
Callback functions for handling bus arrival information.
"""
import re
import os
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from dash import Input, Output, State, html, callback_context, no_update, ALL
import dash_leaflet as dl
from utils.async_fetcher import run_in_thread
# Import fetch_bus_stops_data from transport_callback to avoid circular import
# This is done inside the function to prevent circular import issues

from conf.api_urls import BUS_ARRIVAL_URL


@run_in_thread
def fetch_bus_arrival_data_async(bus_stop_code: str) -> Optional[Dict[str, Any]]:
    """
    Fetch bus arrival data asynchronously for a specific bus stop from LTA DataMall API.
    
    Args:
        bus_stop_code: Bus stop code (e.g., "83139")
    
    Returns:
        Future object. Call .result() to get the data.
    """
    api_key = os.getenv("LTA_API_KEY")
    if not api_key:
        print("Warning: LTA_API_KEY not found")
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "AccountKey": api_key,
        "Content-Type": "application/json"
    }
    
    params = {
        "BusStopCode": bus_stop_code
    }
    
    try:
        import requests
        response = requests.get(BUS_ARRIVAL_URL, headers=headers, params=params, timeout=10)
        if 200 <= response.status_code < 300:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching bus arrival data for stop {bus_stop_code}: {e}")
        return None


_LOAD_LABELS = {
    "SEA": "Seats",
    "SDA": "Standing",
    "LSD": "Crowded",
}
_WAIT_STYLES = {
    "soon": {"backgroundColor": "#2E7D32", "color": "#fff"},
    "mid": {"backgroundColor": "#C9A227", "color": "#111827"},
    "later": {"backgroundColor": "#5B6B7A", "color": "#fff"},
    "gone": {"backgroundColor": "#666", "color": "#ddd"},
}


def parse_arrival_wait_seconds(estimated_arrival: str) -> Optional[float]:
    """Return seconds until arrival, or None when the timestamp cannot be parsed."""
    if not estimated_arrival:
        return None
    try:
        if isinstance(estimated_arrival, str):
            arrival_str = estimated_arrival.replace("+08:00", "").replace("Z", "")
            arrival_dt = datetime.strptime(arrival_str, "%Y-%m-%dT%H:%M:%S")
        else:
            arrival_dt = estimated_arrival
        return (arrival_dt - datetime.now()).total_seconds()
    except (ValueError, TypeError, AttributeError) as error:
        print(f"Error formatting arrival time '{estimated_arrival}': {error}")
        return None


def format_arrival_time_minutes(estimated_arrival: str) -> str:
    """Format arrival time as Arriving, N minutes, Departed, or N/A."""
    total_seconds = parse_arrival_wait_seconds(estimated_arrival)
    if total_seconds is None:
        return "N/A"
    if total_seconds < 0:
        return "Departed"
    if total_seconds < 60:
        return "Arriving"
    return f"{int(total_seconds / 60)} min"


def wait_urgency(label: str) -> str:
    """Map a wait label to a colour band for the next-bus time."""
    if label in ("N/A", "Departed"):
        return "gone"
    if label == "Arriving":
        return "soon"
    if label.endswith(" min"):
        try:
            minutes = int(label.split(" ")[0])
        except (TypeError, ValueError):
            return "later"
        if minutes <= 7:
            return "soon" if minutes < 2 else "mid"
        return "later"
    return "later"


def load_label(load_code: Optional[str]) -> Optional[str]:
    """Return a commuter-facing crowding label."""
    if not load_code:
        return None
    return _LOAD_LABELS.get(str(load_code).upper())


def service_number_sort_key(service_no: str) -> Tuple[float, str]:
    """Sort service numbers by numeric portion, then the raw code."""
    if not service_no or service_no == "N/A":
        return (float("inf"), "")
    match = re.search(r"\d+", str(service_no))
    numeric = int(match.group()) if match else float("inf")
    return (numeric, str(service_no))


def next_bus_wait_seconds(service: Dict[str, Any]) -> float:
    """Soonest known wait for a service; missing times sort last."""
    next_bus = service.get("NextBus") or {}
    wait = parse_arrival_wait_seconds(next_bus.get("EstimatedArrival", ""))
    if wait is None:
        return float("inf")
    return wait


def opposite_search_input_updates(
    trigger_id: str,
    bus_stop_value=no_update,
):
    """Clear the search field opposite the search that was submitted."""
    if "bus-service-search-" in trigger_id:
        return "", no_update
    if "bus-stop-search-" in trigger_id:
        return bus_stop_value, ""
    return bus_stop_value, no_update


def _bus_stop_name_map(bus_stops_data: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Map bus stop codes to descriptions."""
    if bus_stops_data is None:
        from utils.transport.bus import fetch_bus_stops_data
        bus_stops_data = fetch_bus_stops_data()
    name_map: Dict[str, str] = {}
    if not bus_stops_data or "value" not in bus_stops_data:
        return name_map
    for stop in bus_stops_data.get("value", []):
        code = stop.get("BusStopCode")
        if code:
            name_map[str(code)] = stop.get("Description") or ""
    return name_map


def _service_meta_marks(next_bus: Dict[str, Any]) -> List[str]:
    """Crowding, wheelchair, and vehicle marks for the next bus."""
    marks: List[str] = []
    crowding = load_label(next_bus.get("Load"))
    if crowding:
        marks.append(crowding)
    if str(next_bus.get("Feature", "")).upper() == "WAB":
        marks.append("Wheelchair")
    vehicle_type = str(next_bus.get("Type", "")).upper()
    if vehicle_type == "DD":
        marks.append("Double deck")
    elif vehicle_type == "BD":
        marks.append("Bendy")
    return marks


def _arrival_time_chip(label: str, is_next: bool) -> html.Span:
    """Render one arrival time, with stronger colour only on the next bus."""
    urgency = wait_urgency(label) if is_next else ("gone" if label in ("N/A", "Departed") else "later")
    chip_style = {
        **_WAIT_STYLES[urgency],
        "padding": "0.2rem 0.5rem",
        "borderRadius": "0.25rem",
        "fontWeight": "700",
        "fontSize": "0.95rem" if is_next else "0.7rem",
    }
    return html.Span(label, className=f"bus-arrival-time bus-arrival-time--{urgency}", style=chip_style)


def format_bus_arrival_display(
    arrival_data: Optional[Dict[str, Any]],
    bus_stop_code: str,
    stop_map: Optional[Dict[str, str]] = None,
    sort_mode: str = "soonest",
) -> html.Div:
    """Format stop arrivals as glanceable service rows."""
    if not arrival_data:
        return html.Div(
            html.P(
                "Unable to fetch bus arrival data. Please try again.",
                style={
                    "color": "#999",
                    "textAlign": "center",
                    "fontSize": "0.75rem",
                    "margin": "0.5rem 0",
                },
            )
        )

    services = list(arrival_data.get("Services") or [])
    if not services:
        return html.Div(
            html.P(
                "No bus services available at this stop.",
                style={
                    "color": "#999",
                    "textAlign": "center",
                    "fontSize": "0.75rem",
                    "margin": "0.5rem 0",
                },
            )
        )

    names = stop_map if stop_map is not None else _bus_stop_name_map()
    stop_name = names.get(str(bus_stop_code), "")
    stop_title = f"{stop_name} ({bus_stop_code})" if stop_name else f"Bus stop {bus_stop_code}"
    updated_at = datetime.now().strftime("%H:%M")

    if sort_mode == "service":
        services = sorted(services, key=lambda item: service_number_sort_key(item.get("ServiceNo", "N/A")))
    else:
        services = sorted(
            services,
            key=lambda item: (
                next_bus_wait_seconds(item),
                service_number_sort_key(item.get("ServiceNo", "N/A")),
            ),
        )

    rows = []
    for service in services:
        service_no = service.get("ServiceNo", "N/A")
        operator = service.get("Operator", "")
        next_bus = service.get("NextBus") or {}
        next_bus2 = service.get("NextBus2") or {}
        next_bus3 = service.get("NextBus3") or {}

        labels = [
            format_arrival_time_minutes(next_bus.get("EstimatedArrival", "")),
            format_arrival_time_minutes(next_bus2.get("EstimatedArrival", "")),
            format_arrival_time_minutes(next_bus3.get("EstimatedArrival", "")),
        ]
        chips = [_arrival_time_chip(labels[0], is_next=True)]
        chips.extend(
            _arrival_time_chip(label, is_next=False)
            for label in labels[1:]
            if label != "N/A"
        )

        destination_code = str(next_bus.get("DestinationCode") or "")
        destination_name = names.get(destination_code, "")
        destination_text = (
            f"Towards {destination_name}"
            if destination_name
            else (f"Towards {destination_code}" if destination_code else "")
        )
        marks = _service_meta_marks(next_bus)

        rows.append(
            html.Div(
                className="bus-arrival-row",
                **{"data-service": str(service_no)},
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "0.75rem",
                    "padding": "0.65rem 0.75rem",
                    "backgroundColor": "#1f2d3a",
                    "borderRadius": "0.5rem",
                    "border": "0.0625rem solid #4a5a6a",
                },
                children=[
                    html.Span(
                        str(service_no),
                        title=operator or None,
                        style={
                            "minWidth": "3.25rem",
                            "textAlign": "center",
                            "backgroundColor": "#4169E1",
                            "color": "#fff",
                            "fontWeight": "800",
                            "fontSize": "1.05rem",
                            "padding": "0.35rem 0.4rem",
                            "borderRadius": "0.4rem",
                        },
                    ),
                    html.Div(
                        style={"flex": "1", "minWidth": "0"},
                        children=[
                            html.Div(
                                destination_text or "Next buses",
                                style={
                                    "color": "#fff",
                                    "fontWeight": "600",
                                    "fontSize": "0.8125rem",
                                    "whiteSpace": "nowrap",
                                    "overflow": "hidden",
                                    "textOverflow": "ellipsis",
                                },
                            ),
                            html.Div(
                                " · ".join(marks) if marks else "Live arrival",
                                style={
                                    "color": "#9fb0c0",
                                    "fontSize": "0.7rem",
                                    "marginTop": "0.15rem",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        chips,
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "gap": "0.35rem",
                            "flexWrap": "wrap",
                            "justifyContent": "flex-end",
                        },
                    ),
                ],
            )
        )

    return html.Div(
        className="bus-arrival-board",
        children=[
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "baseline",
                    "gap": "0.75rem",
                    "marginBottom": "0.75rem",
                },
                children=[
                    html.Div(
                        [
                            html.Div(
                                "Stop arrivals",
                                style={
                                    "color": "#9fc5ff",
                                    "fontSize": "0.7rem",
                                    "fontWeight": "700",
                                    "letterSpacing": "0.04rem",
                                    "textTransform": "uppercase",
                                },
                            ),
                            html.Div(
                                stop_title,
                                style={
                                    "color": "#fff",
                                    "fontWeight": "700",
                                    "fontSize": "0.95rem",
                                },
                            ),
                        ]
                    ),
                    html.Span(
                        f"Updated {updated_at}",
                        style={"color": "#9fb0c0", "fontSize": "0.7rem", "whiteSpace": "nowrap"},
                    ),
                ],
            ),
            html.Div(rows, style={"display": "flex", "flexDirection": "column", "gap": "0.5rem"}),
        ]
    )


def register_bus_arrival_callbacks(app):
    """
    Register all bus arrival related callbacks.
    
    Args:
        app: Dash application instance
    """
    @app.callback(
        Output('current-bus-stop-code', 'data'),
        [Input('bus-stop-search-btn', 'n_clicks'),
         Input('bus-stop-search-input', 'n_submit'),
         Input({'type': 'bus-stop-marker', 'index': ALL}, 'n_clicks')],
        [State('bus-stop-search-input', 'value')],
        prevent_initial_call=True
    )
    def update_current_bus_stop_code(
        _search_clicks, _search_submit, _marker_clicks, search_value
    ):
        """Store the current bus stop code for auto-refresh."""
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        
        trigger_id = ctx.triggered[0]['prop_id']
        trigger_value = ctx.triggered[0]['value']
        bus_stop_code = None
        
        # Check if a bus stop marker was clicked
        if 'bus-stop-marker' in trigger_id:
            if trigger_value is None or trigger_value == 0:
                return no_update
            marker_id_str = trigger_id.split('.')[0]
            marker_id = json.loads(marker_id_str)
            bus_stop_code = marker_id['index']
        # Check if search button was clicked
        elif 'bus-stop-search-' in trigger_id:
            if search_value and search_value.strip().isdigit() and len(search_value.strip()) == 5:
                bus_stop_code = search_value.strip()
        
        return bus_stop_code if bus_stop_code else no_update

    @app.callback(
        [Output('bus-search-results', 'children'),
         Output('bus-arrival-popup-layer', 'children'),
         Output('bus-stop-search-input', 'value'),
         Output('bus-service-search-input', 'value'),
         Output('bus-arrival-results-store', 'data')],
        [Input('bus-stop-search-btn', 'n_clicks'),
         Input('bus-service-search-btn', 'n_clicks'),
         Input('bus-stop-search-input', 'n_submit'),
         Input('bus-service-search-input', 'n_submit'),
         Input({'type': 'bus-stop-marker', 'index': ALL}, 'n_clicks'),
         Input('bus-arrival-interval', 'n_intervals'),
         Input('bus-arrival-sort-mode', 'value')],
        [State('bus-stop-search-input', 'value'),
         State('bus-service-search-input', 'value'),
         State('bus-stops-toggle-state', 'data'),
         State('current-bus-stop-code', 'data'),
         State('navigation-tabs', 'value'),
         State('transit-sub-tabs', 'value'),
         State('bus-arrival-results-store', 'data')],
        prevent_initial_call=True
    )
    def update_bus_search_display(
        _bus_stop_clicks,
        _bus_service_clicks,
        _bus_stop_submit,
        _bus_service_submit,
        _marker_clicks,
        _interval_n,
        sort_mode,
        bus_stop_value,
        bus_service_value,
        _bus_stops_visible,
        stored_bus_stop_code,
        active_tab,
        transit_sub_tab,
        store_data,
    ):
        """
        Update bus search display when bus stop or bus service search is performed,
        a bus stop marker is clicked, or interval triggers.
        """
        ctx = callback_context
        if not ctx.triggered:
            return no_update, [], no_update, no_update, no_update
        trigger_id = ctx.triggered[0]['prop_id']
        if (
            'bus-arrival-interval' in trigger_id
            and (active_tab != 'transit' or transit_sub_tab != 'transit-bus')
        ):
            return no_update, no_update, no_update, no_update, no_update
        if 'bus-arrival-sort-mode' in trigger_id:
            if not isinstance(store_data, dict) or store_data.get("type") != "arrivals":
                return no_update, no_update, no_update, no_update, no_update
            return (
                format_bus_arrival_display(
                    store_data.get("payload"),
                    store_data.get("bus_stop_code", ""),
                    stop_map=store_data.get("stop_map") or {},
                    sort_mode=sort_mode or "soonest",
                ),
                no_update,
                no_update,
                no_update,
                no_update,
            )

        trigger_value = ctx.triggered[0]['value']

        if 'bus-service-search-' in trigger_id:
            bus_stop_input, service_input = opposite_search_input_updates(trigger_id)
            if not bus_service_value:
                return html.P(
                    "Please enter a bus service number",
                    style={
                        "color": "#ff6b6b",
                        "textAlign": "center",
                        "fontSize": "0.75rem",
                        "margin": "0.5rem 0",
                    }
                ), [], bus_stop_input, service_input, {"type": "route"}

            service_no = bus_service_value.strip().upper()
            if not service_no:
                return html.P(
                    "Invalid bus service number. Please enter a valid service number.",
                    style={
                        "color": "#ff6b6b",
                        "textAlign": "center",
                        "fontSize": "0.75rem",
                        "margin": "0.5rem 0",
                    }
                ), [], bus_stop_input, service_input, {"type": "route"}

            from callbacks.bus_service_callback import format_bus_service_search_display
            from utils.transport.bus import fetch_bus_routes_data
            routes_data = fetch_bus_routes_data()
            formatted_service = format_bus_service_search_display(service_no, routes_data)
            return (
                formatted_service,
                [],
                bus_stop_input,
                service_input,
                {"type": "route"},
            )

        bus_stop_code = None
        if 'bus-arrival-interval' in trigger_id:
            if stored_bus_stop_code:
                bus_stop_code = stored_bus_stop_code
            else:
                return no_update, [], no_update, no_update, no_update
        elif 'bus-stop-marker' in trigger_id:
            if trigger_value is None or trigger_value == 0:
                return no_update, [], no_update, no_update, no_update
            marker_id_str = trigger_id.split('.')[0]
            marker_id = json.loads(marker_id_str)
            bus_stop_code = marker_id['index']
        elif 'bus-stop-search-' in trigger_id:
            if not bus_stop_value:
                bus_stop_input, service_input = opposite_search_input_updates(trigger_id)
                return html.P(
                    "Enter a 5-digit stop code, or zoom the map and click a stop.",
                    style={
                        "color": "#ff6b6b",
                        "textAlign": "center",
                        "fontSize": "0.75rem",
                        "margin": "0.5rem 0",
                    }
                ), [], bus_stop_input, service_input, no_update

            bus_stop_value = bus_stop_value.strip()
            if not bus_stop_value.isdigit() or len(bus_stop_value) != 5:
                bus_stop_input, service_input = opposite_search_input_updates(trigger_id)
                return html.P(
                    "Invalid bus stop code. Please enter a 5-digit number.",
                    style={
                        "color": "#ff6b6b",
                        "textAlign": "center",
                        "fontSize": "0.75rem",
                        "margin": "0.5rem 0",
                    }
                ), [], bus_stop_input, service_input, no_update
            bus_stop_code = bus_stop_value

        if not bus_stop_code:
            return no_update, [], no_update, no_update, no_update

        future = fetch_bus_arrival_data_async(bus_stop_code)
        arrival_data = future.result() if future else None

        lat, lon = None, None
        from utils.transport.bus import fetch_bus_stops_data
        bus_stops_data = fetch_bus_stops_data()
        stop_map = _bus_stop_name_map(bus_stops_data)
        needed_codes = {str(bus_stop_code)}
        for service in (arrival_data or {}).get("Services") or []:
            destination_code = (service.get("NextBus") or {}).get("DestinationCode")
            if destination_code:
                needed_codes.add(str(destination_code))
        compact_stop_map = {
            code: name for code, name in stop_map.items() if code in needed_codes
        }
        if bus_stops_data and 'value' in bus_stops_data:
            for bs in bus_stops_data['value']:
                if str(bs.get('BusStopCode')) == str(bus_stop_code):
                    lat = float(bs.get('Latitude', 0))
                    lon = float(bs.get('Longitude', 0))
                    break

        formatted_arrival = format_bus_arrival_display(
            arrival_data,
            bus_stop_code,
            stop_map=compact_stop_map,
            sort_mode=sort_mode or "soonest",
        )
        store_data = {
            "type": "arrivals",
            "bus_stop_code": bus_stop_code,
            "payload": arrival_data,
            "stop_map": compact_stop_map,
        }
        bus_stop_input, service_input = opposite_search_input_updates(
            trigger_id,
            bus_stop_code,
        )

        if lat and lon:
            highlight_circle = dl.Circle(
                center=[lat, lon],
                radius=30,
                color="#FF4136",
                fill=True,
                fillColor="#FF4136",
                fillOpacity=0.2,
                weight=2,
                dashArray="5, 5",
            )
            return (
                formatted_arrival,
                [highlight_circle],
                bus_stop_input,
                service_input,
                store_data,
            )

        return formatted_arrival, [], bus_stop_input, service_input, store_data

    app.clientside_callback(
        """
        function(query) {
            var filter = (query || '').trim().toUpperCase();
            var rows = document.querySelectorAll('.bus-arrival-row');
            rows.forEach(function(row) {
                var service = (row.getAttribute('data-service') || '').toUpperCase();
                row.style.display = (!filter || service.indexOf(filter) !== -1) ? '' : 'none';
            });
            return window.dash_clientside.no_update;
        }
        """,
        Output('bus-arrival-filter-status', 'data'),
        Input('bus-arrival-service-filter', 'value'),
        prevent_initial_call=True,
    )

