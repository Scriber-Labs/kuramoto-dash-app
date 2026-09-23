"""UI Components package for Kuramoto Dash application."""

from app.components.cards import (
    equation_card,
    footer_section,
    header_section,
    hero_section,
    metric_cards,
)
from app.components.controls import (
    control_group,
    sidebar_controls,
    timeline_controls,
)
from app.components.plots import (
    base_figure,
    empty_figure,
    frequency_distribution_figure,
    network_colors,
    network_figure,
    order_figure,
    phase_heatmap_figure,
    phase_trajectories_figure,
    unit_circle_figure,
)

__all__ = [
    "empty_figure",
    "base_figure",
    "network_colors",
    "unit_circle_figure",
    "order_figure",
    "phase_heatmap_figure",
    "phase_trajectories_figure",
    "network_figure",
    "frequency_distribution_figure",
    "metric_cards",
    "equation_card",
    "hero_section",
    "header_section",
    "footer_section",
    "control_group",
    "sidebar_controls",
    "timeline_controls",
]
