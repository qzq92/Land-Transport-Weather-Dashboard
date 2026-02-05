from dash import html, dcc

# Glossy tab styling
TAB_STYLE = {
    "padding": "0.375rem 0.875rem",
    "background": "linear-gradient(180deg, #1a1a1a 0%, #808080 100%)",
    "border": "none",
    "borderRadius": "0.375rem",
    "color": "#ffffff",
    "fontWeight": "500",
    "fontSize": "0.75rem",
    "cursor": "pointer",
    "transition": "all 0.3s ease",
    "marginRight": "0.375rem",
    "boxShadow": "0 0.125rem 0.25rem rgba(0, 0, 0, 0.3)",
}

TAB_SELECTED_STYLE = {
    "padding": "0.375rem 0.875rem",
    "background": "linear-gradient(180deg, #667eea 0%, #764ba2 100%)",
    "border": "none",
    "borderRadius": "0.375rem",
    "color": "#ffffff",
    "fontWeight": "600",
    "fontSize": "0.75rem",
    "boxShadow": "0 0.25rem 0.9375rem rgba(102, 126, 234, 0.4)",
    "cursor": "pointer",
    "marginRight": "0.375rem",
}


def build_dashboard_banner():
    return html.Div(
        id="banner",
        className="banner",
        children=[
            # Navigation tabs with glossy styling
            html.Div(
                dcc.Tabs(
                    id="navigation-tabs",
                    value="main",
                    className="glossy-tabs",
                    children=[
                        dcc.Tab(
                            label="🏠 Main Dashboard",
                            value="main",
                            style=TAB_STYLE,
                            selected_style=TAB_SELECTED_STYLE,
                        ),
                        dcc.Tab(
                            label="📍 Weather metrics and sensor locations",
                            value="realtime-weather",
                            style=TAB_STYLE,
                            selected_style=TAB_SELECTED_STYLE,
                        ),
                        dcc.Tab(
                            label="📊 Daily Health and Environmental Watch",
                            value="weather-indices",
                            style=TAB_STYLE,
                            selected_style=TAB_SELECTED_STYLE,
                        ),
                        dcc.Tab(
                            label="🚦 Road & Transport Information",
                            value="transport",
                            style=TAB_STYLE,
                            selected_style=TAB_SELECTED_STYLE,
                        ),
                        dcc.Tab(
                            label="🗺️ Nearby Facilities",
                            value="nearby-transport",
                            style=TAB_STYLE,
                            selected_style=TAB_SELECTED_STYLE,
                        ),
                        dcc.Tab(
                            label="⏱️ Estimated Travel Times",
                            value="travel-times",
                            style=TAB_STYLE,
                            selected_style=TAB_SELECTED_STYLE,
                        ),
                        dcc.Tab(
                            label="📊 Analytics and Forecast",
                            value="analytics-forecast",
                            style=TAB_STYLE,
                            selected_style=TAB_SELECTED_STYLE,
                        ),
                        dcc.Tab(
                            label="📹 Traffic Conditions",
                            value="traffic-conditions",
                            style=TAB_STYLE,
                            selected_style=TAB_SELECTED_STYLE,
                        ),
                    ],
                    style={
                        "height": "auto",
                        "border": "none",
                    }
                ),
                style={
                    "flex": "1",
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "padding": "0.375rem 0",
                }
            ),
        ],
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "0 1.25rem",
            "background": "linear-gradient(180deg, #1a202c 0%, #2d3748 100%)",
            "borderBottom": "0.0625rem solid #4a5568",
        },
    )