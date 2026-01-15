"""
Reusable metric card component for displaying metrics across the dashboard.
Used in main page, weather metrics page, and transport page.
"""
from dash import html
from typing import Optional, List


def create_metric_card(
    card_id: str,
    label: str,
    value_id: str,
    initial_value: str = "--",
    additional_children: Optional[List] = None
) -> html.Div:
    """
    Create a standardized metric card component.
    
    Args:
        card_id: Unique identifier for the card container
        label: Display label (can include emoji)
        value_id: ID for the value div (used by callbacks to update the metric)
        initial_value: Initial display value (default: "--")
        additional_children: Optional list of additional child components (e.g., disclaimers)
    
    Returns:
        HTML Div containing the metric card with consistent styling
    
    Example:
        >>> create_metric_card(
        ...     card_id="bus-stops-card",
        ...     label="🚏 Bus Stops",
        ...     value_id="bus-stops-count-value",
        ...     initial_value="--"
        ... )
    """
    # Build the children list for the card
    card_children = [
        html.Div(
            style={
                "display": "flex",
                "flexDirection": "row",
                "alignItems": "center",
                "justifyContent": "space-between",
            },
            children=[
                html.Span(
                    label,
                    style={
                        "color": "#fff",
                        "fontWeight": "600",
                        "fontSize": "0.8125rem"
                    }
                ),
                html.Div(
                    id=value_id,
                    style={
                        "color": "#4169E1",
                        "fontSize": "1.125rem",
                        "fontWeight": "700",
                    },
                    children=[
                        html.Div(
                            html.Span(initial_value, style={"color": "#999"}),
                            style={
                                "backgroundColor": "rgb(58, 74, 90)",
                                "padding": "0.25rem 0.5rem",
                                "borderRadius": "0.25rem",
                            }
                        )
                    ],
                ),
            ]
        ),
    ]
    
    # Add any additional children (e.g., disclaimers)
    if additional_children:
        card_children.extend(additional_children)
    
    return html.Div(
        id=card_id,
        style={
            "backgroundColor": "#4a5a6a",
            "borderRadius": "0.5rem",
            "padding": "0.625rem",
            "display": "flex",
            "flexDirection": "column",
            "gap": "0.5rem",
            "flexShrink": "0",
        },
        children=card_children
    )


def create_metric_value_display(value: str, color: str = "#999") -> html.Div:
    """
    Create a standardized metric value display (used in callbacks).
    
    Args:
        value: The value to display
        color: Text color (default: "#999")
    
    Returns:
        HTML Div containing the formatted value
    
    Example:
        >>> create_metric_value_display("42", color="#4169E1")
    """
    return html.Div(
        html.Span(value, style={"color": color}),
        style={
            "backgroundColor": "rgb(58, 74, 90)",
            "padding": "0.25rem 0.5rem",
            "borderRadius": "0.25rem",
        }
    )

