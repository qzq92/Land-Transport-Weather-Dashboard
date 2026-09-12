"""
Configuration for the Daily Health and Environmental Watch tab.

Holds PSI/pollutant/WBGT category bands, units, and display column labels.
Information-source URLs live in conf.api_urls.
"""

PSI_REGIONS = ("north", "south", "east", "west", "central")

UNKNOWN_CATEGORY_COLOR = "#888"
UNKNOWN_CATEGORY_LABEL = "Unknown"
UNKNOWN_CATEGORY = (UNKNOWN_CATEGORY_COLOR, UNKNOWN_CATEGORY_LABEL)

AIR_QUALITY_BAND_LABELS = (
    "Good",
    "Moderate",
    "Unhealthy",
    "Very Unhealthy",
    "Hazardous",
)
AIR_QUALITY_BAND_COLORS = (
    "#3ea72d",
    "#fff300",
    "#f18b00",
    "#e53210",
    "#b567a4",
)


def _air_quality_categories(ranges):
    """Pair numeric ranges with the shared five-band colours and labels."""
    return tuple(
        (low, high, color, label)
        for (low, high), color, label in zip(
            ranges, AIR_QUALITY_BAND_COLORS, AIR_QUALITY_BAND_LABELS
        )
    )


def _range_labels(categories):
    """Build legend range text from inclusive (low, high) category tuples."""
    last_index = len(categories) - 1
    labels = []
    for index, (low, high, _color, _label) in enumerate(categories):
        if index == last_index:
            labels.append(f"{low}+")
        else:
            labels.append(f"{low}-{high}")
    return tuple(labels)


# PSI uses NEA bands (non-overlapping integer ranges).
PSI_CATEGORIES = _air_quality_categories(
    ((0, 50), (51, 100), (101, 200), (201, 300), (301, 999))
)

# Pollutant cutoffs follow WHO/EPA bands (adjacent ranges share a boundary).
PM25_CATEGORIES = _air_quality_categories(
    ((0, 15), (15, 35), (35, 55), (55, 150), (150, 9999))
)
PM10_CATEGORIES = _air_quality_categories(
    ((0, 45), (45, 100), (100, 200), (200, 300), (300, 9999))
)
SO2_CATEGORIES = _air_quality_categories(
    ((0, 20), (20, 50), (50, 125), (125, 250), (250, 9999))
)
CO_CATEGORIES = _air_quality_categories(
    ((0, 4), (4, 9), (9, 15), (15, 30), (30, 9999))
)
O3_CATEGORIES = _air_quality_categories(
    ((0, 100), (100, 160), (160, 240), (240, 300), (300, 9999))
)
NO2_CATEGORIES = _air_quality_categories(
    ((0, 200), (200, 400), (400, 1000), (1000, 2000), (2000, 9999))
)

# key, map-marker label, PSI table header, unit
POLLUTANT_READING_FIELDS = (
    ("psi_twenty_four_hourly", "PSI (24H Avg)", "24H Mean PSI", ""),
    (
        "pm25_twenty_four_hourly",
        "PM2.5 (24H Avg)",
        "24H Mean PM2.5 Particulate Matter",
        "µg/m³",
    ),
    (
        "pm10_twenty_four_hourly",
        "PM10 (24H Avg)",
        "24H Mean PM10 Particulate Matter",
        "µg/m³",
    ),
    (
        "so2_twenty_four_hourly",
        "SO₂ (Max 24H Avg)",
        "24H Mean Sulphur Dioxide",
        "µg/m³",
    ),
    (
        "co_eight_hour_max",
        "CO (Max 8H Avg)",
        "8H Mean Carbon Monoxide",
        "mg/m³",
    ),
    (
        "o3_eight_hour_max",
        "O₃ (Max 8H Avg)",
        "8H Mean Ozone",
        "µg/m³",
    ),
    (
        "no2_one_hour_max",
        "NO₂ (Max 1H)",
        "1H Max Nitrogen Dioxide",
        "µg/m³",
    ),
)

POLLUTANT_UNITS = {
    key: unit for key, _map_label, _table_label, unit in POLLUTANT_READING_FIELDS
}
PSI_MAP_COLUMNS = tuple(
    (key, map_label) for key, map_label, _table_label, _unit in POLLUTANT_READING_FIELDS
)
PSI_TABLE_COLUMNS = tuple(
    (key, table_label)
    for key, _map_label, table_label, _unit in POLLUTANT_READING_FIELDS
)

POLLUTANT_CATEGORY_MAP = {
    "psi_twenty_four_hourly": PSI_CATEGORIES,
    "pm25_twenty_four_hourly": PM25_CATEGORIES,
    "pm10_twenty_four_hourly": PM10_CATEGORIES,
    "so2_twenty_four_hourly": SO2_CATEGORIES,
    "co_eight_hour_max": CO_CATEGORIES,
    "o3_eight_hour_max": O3_CATEGORIES,
    "no2_one_hour_max": NO2_CATEGORIES,
}

POLLUTANT_LEGEND_ITEMS = (
    ("PM2.5", "pm25_twenty_four_hourly"),
    ("PM10", "pm10_twenty_four_hourly"),
    ("SO₂", "so2_twenty_four_hourly"),
    ("CO", "co_eight_hour_max"),
    ("O₃", "o3_eight_hour_max"),
    ("NO₂", "no2_one_hour_max"),
)

POLLUTANT_THRESHOLD_ROWS = tuple(
    (
        name,
        POLLUTANT_UNITS[key],
        _range_labels(POLLUTANT_CATEGORY_MAP[key]),
    )
    for name, key in POLLUTANT_LEGEND_ITEMS
)

AIR_QUALITY_BANDS = tuple(
    (label, range_text, color)
    for (_low, _high, color, label), range_text in zip(
        PSI_CATEGORIES, _range_labels(PSI_CATEGORIES)
    )
)

POLLUTANT_ABBREVIATIONS = (
    ("PSI", "Pollutant Standards Index"),
    ("PM2.5", "Particulate Matter ≤2.5µm"),
    ("PM10", "Particulate Matter ≤10µm"),
    ("SO₂", "Sulphur Dioxide"),
    ("CO", "Carbon Monoxide"),
    ("O₃", "Ozone"),
    ("NO₂", "Nitrogen Dioxide"),
)

# WBGT heat-stress bands use a different label set from PSI.
WBGT_CATEGORIES = (
    (0, 28, "#3ea72d", "Low"),
    (28, 30, "#fff300", "Moderate"),
    (30, 32, "#f18b00", "High"),
    (32, 34, "#e53210", "Very High"),
    (34, 999, "#1a1a1a", "Extreme"),
)
