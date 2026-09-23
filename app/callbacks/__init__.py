"""Callbacks package for Kuramoto Dash application."""

from __future__ import annotations

from dash import Dash

from app.callbacks.dataset import register_dataset_callbacks
from app.callbacks.simulation import register_simulation_callbacks
from app.callbacks.visualization import register_visualization_callbacks


def register_callbacks(app: Dash) -> None:
    """Register all domain callbacks with the Dash application instance."""
    register_simulation_callbacks(app)
    register_visualization_callbacks(app)
    register_dataset_callbacks(app)


__all__ = [
    "register_callbacks",
    "register_simulation_callbacks",
    "register_visualization_callbacks",
    "register_dataset_callbacks",
]
