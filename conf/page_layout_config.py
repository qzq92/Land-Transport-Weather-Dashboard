"""
Common page layout configuration for consistent styling across all dashboard pages.
Provides standardized styles for full-width content containers.
"""

# Standard page padding
PAGE_PADDING = "0.5rem"

# Standard page height calculation (accounts for header/banner)
PAGE_HEIGHT = "calc(100vh - 7.5rem)"

# Main dashboard height (different header height)
MAIN_DASHBOARD_HEIGHT = "calc(100vh - 6.25rem)"

# Content container base style - full width, no maxWidth constraint, no centering
def get_content_container_style(gap="0.5rem", height="calc(100% - 3.125rem)"):
    """
    Get standardized content container style for full-width layout.
    
    Args:
        gap: Gap between flex items (default: "0.5rem")
        height: Container height (default: "calc(100% - 3.125rem)")
    
    Returns:
        Dictionary of style properties
    """
    return {
        "display": "flex",
        "width": "100%",
        "margin": "0",
        "gap": gap,
        "height": height,
    }

# Standard gap between flex items
STANDARD_GAP = "0.5rem"

# Alternative gap (for pages that need more spacing)
LARGE_GAP = "1.25rem"

