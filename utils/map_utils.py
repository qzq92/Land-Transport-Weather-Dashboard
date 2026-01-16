"""
Map utility functions for common map configurations.
"""

# Standardized Singapore map configuration constants
# Used across all map components for consistency
SG_MAP_CENTER = [1.36, 103.82]  # Singapore center coordinates
SG_MAP_DEFAULT_ZOOM = 12  # Default zoom level
SG_MAP_BOUNDS = [[1.1304753, 103.6020882], [1.492007, 104.145897]]  # Map bounds to restrict view to Singapore area
SG_MAP_MIN_ZOOM = 11  # Minimum zoom level
SG_MAP_MAX_ZOOM = 20  # Maximum zoom level
ONEMAP_TILES_URL = "https://www.onemap.gov.sg/maps/tiles/Night/{z}/{x}/{y}.png"


def get_onemap_attribution() -> str:
    """
    Get the standard OneMap attribution string used across all maps.
    
    Returns:
        String containing HTML attribution with OneMap logo, link, and SLA link
    """
    return '''<img src="/assets/img/om_logo.png" style="height:20px;width:20px;"/>&nbsp;<a href="https://www.onemap.gov.sg/" target="_blank" rel="noopener noreferrer">OneMap</a>&nbsp;&copy;&nbsp;contributors&nbsp;&#124;&nbsp;<a href="https://www.sla.gov.sg/" target="_blank" rel="noopener noreferrer">Singapore Land Authority</a>'''

