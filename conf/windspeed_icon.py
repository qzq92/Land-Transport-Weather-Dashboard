"""
Wind speed icons configuration.
Maps wind speed values to appropriate icons/emojis based on intensity.
Reference: Beaufort Wind Scale
"""
from typing import Optional, Union

# Wind speed thresholds (in km/h) and corresponding icons
# Based on Beaufort scale with continuous ranges (upper bound exclusive)
# Format: (min_speed, max_speed_exclusive, icon, description)
WINDSPEED_THRESHOLDS = [
    (0, 1, "🍃", "Calm"),              # Calm: 0 to < 1 km/h
    (1, 6, "🍃", "Light Air"),          # Light air: 1 to < 6 km/h
    (6, 12, "🌿", "Light Breeze"),      # Light breeze: 6 to < 12 km/h
    (12, 20, "🌬️", "Gentle Breeze"),    # Gentle breeze: 12 to < 20 km/h
    (20, 29, "🌬️", "Moderate Breeze"),  # Moderate breeze: 20 to < 29 km/h
    (29, 39, "💨", "Fresh Breeze"),     # Fresh breeze: 29 to < 39 km/h
    (39, 50, "💨", "Strong Breeze"),    # Strong breeze: 39 to < 50 km/h
    (50, 62, "🌀", "Near Gale"),        # Near gale: 50 to < 62 km/h
    (62, 75, "🌀", "Gale"),             # Gale: 62 to < 75 km/h
    (75, 89, "🌪️", "Strong Gale"),      # Strong gale: 75 to < 89 km/h
    (89, 103, "🌪️", "Storm"),           # Storm: 89 to < 103 km/h
    (103, 118, "🌪️", "Violent Storm"),  # Violent storm: 103 to < 118 km/h
    (118, 9999, "🌪️", "Hurricane"),     # Hurricane: >= 118 km/h
]

# Default icon
DEFAULT_WINDSPEED_ICON = "🌬️"


def get_windspeed_icon(speed_kmh: Optional[Union[int, float]]) -> str:
    """
    Get the wind speed icon based on speed in km/h.

    Args:
        speed_kmh: Wind speed in kilometers per hour (int or float)

    Returns:
        String containing the appropriate wind icon/emoji
    """
    if speed_kmh is None:
        return DEFAULT_WINDSPEED_ICON

    try:
        speed = float(speed_kmh)
    except (ValueError, TypeError):
        return DEFAULT_WINDSPEED_ICON

    if speed < 0:
        return DEFAULT_WINDSPEED_ICON

    # Use min <= speed < max for continuous ranges
    for min_speed, max_speed, icon, _ in WINDSPEED_THRESHOLDS:
        if min_speed <= speed < max_speed:
            return icon

    return DEFAULT_WINDSPEED_ICON


def get_windspeed_description(speed_kmh: Optional[Union[int, float]]) -> str:
    """
    Get the wind speed description based on speed in km/h.

    Args:
        speed_kmh: Wind speed in kilometers per hour (int or float)

    Returns:
        String containing the wind condition description
    """
    if speed_kmh is None:
        return "Unknown"

    try:
        speed = float(speed_kmh)
    except (ValueError, TypeError):
        return "Unknown"

    if speed < 0:
        return "Unknown"

    # Use min <= speed < max for continuous ranges
    for min_speed, max_speed, _, description in WINDSPEED_THRESHOLDS:
        if min_speed <= speed < max_speed:
            return description

    return "Unknown"


