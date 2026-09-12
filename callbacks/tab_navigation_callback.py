"""
Callback for handling tab navigation between dashboard pages.
"""
from dash import Input, Output, State, no_update

from components.realtime_weather_page import realtime_weather_page
from components.weather_indices_page import weather_indices_page
from components.transport_page import transport_page
from components.transit_page import transit_page
from components.nearby_transport_page import nearby_transport_page


# Ordered list of tab values and their corresponding page builder functions.
# Index N in _TAB_KEYS maps to index N in _PAGE_BUILDERS.
_TAB_KEYS = [
    "realtime-weather",
    "weather-indices",
    "transport",
    "transit",
    "nearby-transport",
]
_PAGE_BUILDERS = [
    realtime_weather_page,
    weather_indices_page,
    transport_page,
    transit_page,
    nearby_transport_page,
]

_TRANSPORT_SUBVIEW_VISIBLE_STYLE = {
    "display": "flex",
    "flex": "1",
    "minHeight": "0",
    "flexDirection": "column",
}
_TRANSPORT_SUBVIEW_HIDDEN_STYLE = {"display": "none"}


def get_transit_sub_tab_state(sub_tab_value):
    """Return Transit view styles and bus interval disabled states."""
    hidden = _TRANSPORT_SUBVIEW_HIDDEN_STYLE
    visible = _TRANSPORT_SUBVIEW_VISIBLE_STYLE
    if sub_tab_value == "transit-bus":
        return hidden, visible, False, False
    return visible, hidden, True, True


def register_tab_navigation_callback(app):
    """
    Register callback to handle navigation between tabs.

    Args:
        app: Dash app instance
    """
    @app.callback(
        [Output('main-content-area', 'style'),
         Output('realtime-weather-page', 'style'),
         Output('weather-indices-page', 'style'),
         Output('transport-page', 'style'),
         Output('transit-page', 'style'),
         Output('nearby-transport-page', 'style'),
         Output('search-bar-section', 'style')],
        Input('navigation-tabs', 'value')
    )
    def switch_page(tab_value):
        """
        Switch between dashboard pages.

        Args:
            tab_value: Selected tab value
                ('main', 'realtime-weather', 'weather-indices', 'transport',
                 'transit', 'nearby-transport')

        Returns:
            Tuple of style dictionaries for each page and search bar
        """
        # Default hidden styles
        main_style = {'display': 'none'}
        realtime_style = {'display': 'none'}
        indices_style = {'display': 'none'}
        transport_style = {'display': 'none'}
        transit_style = {'display': 'none'}
        nearby_transport_style = {'display': 'none'}
        search_bar_style = {'display': 'none'}

        visible_page_style = {
            "display": "block",
            "padding": "0.5rem",
            "height": "calc(100vh - 7.5rem)",
            "width": "100%",
        }

        if tab_value == 'realtime-weather':
            realtime_style = visible_page_style
        elif tab_value == 'weather-indices':
            indices_style = visible_page_style
        elif tab_value == 'transport':
            transport_style = {
                **visible_page_style,
                "display": "flex",
                "flexDirection": "column",
            }
        elif tab_value == 'transit':
            transit_style = {
                **visible_page_style,
                "display": "flex",
                "flexDirection": "column",
            }
        elif tab_value == 'nearby-transport':
            nearby_transport_style = visible_page_style
        else:
            # Main dashboard (search bar is now inside map container)
            main_style = {
                "display": "flex",
                "width": "100%",
                "gap": "0.5rem",
                "padding": "0.25rem 0.5rem",
                "height": "calc(100vh - 7.5rem)",
                "alignItems": "stretch",
            }
            # Keep search bar section hidden (placeholder for callback compatibility)
            search_bar_style = {"display": "none"}

        return (main_style, realtime_style, indices_style, transport_style,
                transit_style, nearby_transport_style, search_bar_style)

    @app.callback(
        [Output("realtime-weather-page", "children"),
         Output("weather-indices-page", "children"),
         Output("transport-page", "children"),
         Output("transit-page", "children"),
         Output("nearby-transport-page", "children"),
         Output("initialized-tabs", "data")],
        Input("navigation-tabs", "value"),
        State("initialized-tabs", "data"),
        prevent_initial_call=True,
    )
    def lazy_load_tab(tab_value, initialized_tabs):
        """
        Populate a tab page's children the first time the user visits it.
        Subsequent visits return no_update so the built layout is preserved.
        """
        if tab_value == "main" or tab_value in initialized_tabs:
            return [no_update] * 6  # 5 page children + store

        results = [no_update] * 5
        if tab_value in _TAB_KEYS:
            idx = _TAB_KEYS.index(tab_value)
            # Build only the inner children, not the outer wrapper div
            # (the wrapper div with its id already exists as the placeholder).
            results[idx] = _PAGE_BUILDERS[idx]().children

        return results + [initialized_tabs + [tab_value]]

    @app.callback(
        [
            Output("transport-metrics-view", "style"),
            Output("transport-travel-times-view", "style"),
            Output("transport-cameras-view", "style"),
            Output("transport-interval", "disabled"),
            Output("ev-charging-interval", "disabled"),
            Output("travel-times-interval", "disabled"),
            Output("traffic-conditions-interval", "disabled"),
        ],
        Input("transport-sub-tabs", "value"),
    )
    def switch_transport_sub_tab(sub_tab_value):
        """Show one Road & Transport sub-view and pause unused refresh intervals."""
        hidden = _TRANSPORT_SUBVIEW_HIDDEN_STYLE
        visible = _TRANSPORT_SUBVIEW_VISIBLE_STYLE

        if sub_tab_value == "transport-travel-times":
            return hidden, visible, hidden, True, True, False, True
        if sub_tab_value == "transport-cameras":
            return hidden, hidden, visible, True, True, True, False
        return visible, hidden, hidden, False, False, True, True

    @app.callback(
        [
            Output("transit-crowd-view", "style"),
            Output("transit-bus-view", "style"),
            Output("bus-arrival-page-interval", "disabled"),
            Output("bus-arrival-interval", "disabled"),
        ],
        Input("transit-sub-tabs", "value"),
    )
    def switch_transit_sub_tab(sub_tab_value):
        """Show one Transit view and pause bus refreshes while it is hidden."""
        return get_transit_sub_tab_state(sub_tab_value)

    # Clientside callback to fix map rendering after tab switch
    # This triggers invalidateSize() on Leaflet maps when tabs change
    app.clientside_callback(
        """
        function(tab_value) {
            // Map ID for each tab
            var tabMapIds = {
                'main': 'sg-map',
                'realtime-weather': 'realtime-weather-map',
                'weather-indices': 'weather-indices-map',
                'transport': 'transport-map',
                'nearby-transport': 'nearby-transport-map'
            };
            
            var targetMapId = tabMapIds[tab_value];
            if (!targetMapId) {
                return window.dash_clientside.no_update;
            }
            
            // Function to invalidate map size
            function invalidateMapSize() {
                var mapContainer = document.getElementById(targetMapId);
                if (mapContainer) {
                    // Try to find the Leaflet map instance
                    // Leaflet stores the map instance on the container element
                    if (mapContainer._leaflet_map) {
                        mapContainer._leaflet_map.invalidateSize();
                    } else {
                        // Fallback: trigger window resize event which Leaflet listens to
                        window.dispatchEvent(new Event('resize'));
                    }
                }
            }
            
            // Delay to ensure DOM is fully updated after display:none -> display:flex/block
            setTimeout(invalidateMapSize, 100);
            setTimeout(invalidateMapSize, 300);
            setTimeout(invalidateMapSize, 500);
            
            return window.dash_clientside.no_update;
        }
        """,
        Output('bus-arrival-map', 'id'),
        Input('navigation-tabs', 'value'),
        prevent_initial_call=True
    )

    app.clientside_callback(
        """
        function(sub_tab_value) {
            if (sub_tab_value !== 'transit-bus') {
                return window.dash_clientside.no_update;
            }
            setTimeout(function() { window.dispatchEvent(new Event('resize')); }, 100);
            setTimeout(function() { window.dispatchEvent(new Event('resize')); }, 300);
            return window.dash_clientside.no_update;
        }
        """,
        Output('bus-arrival-map', 'id', allow_duplicate=True),
        Input('transit-sub-tabs', 'value'),
        prevent_initial_call=True
    )
