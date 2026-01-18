"""
Configuration for Singapore MRT and LRT lines.
Contains official line codes, names, and color codes for all train lines.
"""

# Singapore MRT lines with official colors
MRT_LINES = [
    {"code": "NSL", "name": "North South Line", "color": "#E31937"},
    {"code": "EWL", "name": "East West Line", "color": "#009645"},
    {"code": "CCL", "name": "Circle Line", "color": "#FFA500"},
    {"code": "DTL", "name": "Downtown Line", "color": "#005EC4"},
    {"code": "NEL", "name": "North East Line", "color": "#9900AA"},
    {"code": "TEL", "name": "Thomson-East Coast Line", "color": "#9D5B25"},
]

# LRT lines (all share grey color)
LRT_LINES = [
    {"code": "PGL", "name": "Punggol LRT", "color": "#808080"},
    {"code": "SKL", "name": "Sengkang LRT", "color": "#808080"},
    {"code": "BPL", "name": "Bukit Panjang LRT", "color": "#808080"},
]

# Combined list of all train lines (MRT + LRT)
ALL_TRAIN_LINES = MRT_LINES + LRT_LINES

# Dictionary mapping line codes to line info for quick lookup
LINE_INFO_MAP = {line["code"]: line for line in ALL_TRAIN_LINES}

# Dictionary mapping line codes to colors only
LINE_COLOR_MAP = {line["code"]: line["color"] for line in ALL_TRAIN_LINES}

# Dictionary mapping line codes to names only
LINE_NAME_MAP = {line["code"]: line["name"] for line in ALL_TRAIN_LINES}

