// Map invalidation fix for Leaflet maps in Dash
// This handles grey tiles issue when switching tabs or after hot reload

if (!window.dash_clientside) {
    window.dash_clientside = {};
}

window.dash_clientside.map_utils = {
    invalidate_map: function(n_intervals, map_id) {
        if (!n_intervals) {
            return window.dash_clientside.no_update;
        }
        
        // Small delay to ensure container is fully rendered
        setTimeout(function() {
            // Find the Leaflet map instance
            const mapElement = document.getElementById(map_id);
            if (mapElement && mapElement._leaflet_id) {
                // Access Leaflet's internal map registry
                if (window.L && window.L.Map) {
                    const maps = window.L.Map._maps || {};
                    const map = maps[mapElement._leaflet_id];
                    if (map) {
                        map.invalidateSize();
                        console.log('Map invalidated:', map_id);
                    }
                }
            }
        }, 100);
        
        return window.dash_clientside.no_update;
    }
};

