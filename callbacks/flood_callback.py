"""
Callback functions for handling flood alerts API integration.
Reference: https://data.gov.sg/datasets?formats=API&resultId=d_f1404e08587ce555b9ea3f565e2eb9a3
"""
from dash import Input, Output, html
from callbacks.realtime_weather_callback import fetch_flood_alerts_async


def format_flood_alerts(data):
    """
    Format flood alert data for display in banner.

    Args:
        data: JSON response from flood alerts API

    Returns:
        HTML Div containing flood alert banner, or None if no alerts
    """
    if not data:
        return None

    # Handle different possible response structures
    items = data.get('items', [])
    if not items:
        return None

    # Get the most recent flood alert item
    alert_item = items[0]
    
    # Check for alerts in various possible formats
    alerts = alert_item.get('alerts', [])
    if not alerts:
        # Try alternative field names
        alerts = alert_item.get('flood_alerts', [])
        if not alerts:
            alerts = alert_item.get('data', [])
    
    if not alerts:
        return None

    # Build alert messages
    alert_messages = []
    for alert in alerts:
        # Handle different possible alert structures
        if isinstance(alert, str):
            alert_messages.append(alert)
        elif isinstance(alert, dict):
            area = alert.get('area') or alert.get('location') or alert.get('name', 'Unknown Area')
            level = alert.get('level') or alert.get('severity', '')
            message = alert.get('message') or alert.get('description', '')
            
            # Format the alert message
            alert_text = f"{area}"
            if level:
                alert_text += f" ({level})"
            if message:
                alert_text += f" - {message}"
            
            alert_messages.append(alert_text)

    if not alert_messages:
        return None

    # Create banner with alert information
    return html.Div(
        [
            html.Div(
                [
                    html.Strong("⚠️ FLOOD ALERT", style={"fontSize": "16px", "marginRight": "10px"}),
                    html.Span(" | ".join(alert_messages), style={"fontSize": "14px"})
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "padding": "10px 20px",
                }
            )
        ],
        style={
            "backgroundColor": "#ff4444",
            "color": "#fff",
            "width": "100%",
            "margin": "0",
            "borderBottom": "2px solid #cc0000",
            "fontWeight": "600",
        }
    )


def register_flood_callbacks(app):
    """
    Register flood alert callbacks for the dashboard.

    Args:
        app: Dash app instance
    """
    @app.callback(
        Output('flood-alert-banner', 'children'),
        Input('interval-component', 'n_intervals')
    )
    def update_flood_alert_banner(n_intervals):
        """
        Update flood alert banner periodically.

        Args:
            n_intervals: Number of intervals (from dcc.Interval component)

        Returns:
            HTML content for flood alert banner, or empty div if no alerts
        """
        # n_intervals is required by the callback but not used directly
        _ = n_intervals

        # Fetch flood alerts asynchronously
        future = fetch_flood_alerts_async()
        flood_data = future.result() if future else None
        flood_banner = format_flood_alerts(flood_data)

        if flood_banner:
            return flood_banner
        
        # Return empty div if no alerts (banner will be hidden)
        return html.Div(style={"display": "none"})

