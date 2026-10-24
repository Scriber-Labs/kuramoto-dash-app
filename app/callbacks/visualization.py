"""Visualization update callbacks for Plotly figures and metric cards."""

from __future__ import annotations

from typing import Any

import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output

from app.components.cards import metric_cards
from app.components.plots import (
    empty_figure,
    frequency_distribution_figure,
    network_colors,
    network_figure,
    order_figure,
    phase_heatmap_figure,
    phase_trajectories_figure,
    unit_circle_figure,
)


def handle_update_animation_visuals(
    data: dict[str, Any] | None,
    frame: int | None,
) -> tuple[go.Figure, go.Figure, Any]:
    """Compute animated figures (Unit circle, Order parameter) and metric cards."""
    if not data or "time" not in data or not data["time"]:
        return (
            empty_figure(
                "Phase field", "Run a simulation to explore oscillator phases."
            ),
            empty_figure("Synchronization strength", "Run a simulation to chart r(t)."),
            [],
        )

    time = np.asarray(data["time"], dtype=float)
    theta = np.asarray(data["theta"], dtype=float)
    order = np.asarray(data["order_parameter"], dtype=float)
    frequencies = np.asarray(data["frequencies"], dtype=float)

    index = max(0, min(int(frame or 0), len(time) - 1))
    phase = theta[index]
    mean_field = np.mean(np.exp(1j * phase))
    osc_colors = network_colors(frequencies)

    return (
        unit_circle_figure(
            phase,
            float(abs(mean_field)),
            float(np.angle(mean_field)),
            osc_colors,
        ),
        order_figure(time, order, index),
        metric_cards(data, index),
    )


def handle_update_static_visuals(
    data: dict[str, Any] | None,
) -> tuple[go.Figure, go.Figure, go.Figure, go.Figure]:
    """Compute static simulation figures (Heatmap, Trajectories, Network, Distribution)."""
    if not data or "time" not in data or not data["time"]:
        return (
            empty_figure(
                "Oscillator phase history", "The phase heatmap appears after a run."
            ),
            empty_figure(
                "Individual phase trajectories",
                "Each oscillator gets a color-matched phase trace after a run.",
            ),
            empty_figure("Coupling network", "Network structure appears after a run."),
            empty_figure(
                "Natural frequency distribution", "The sampled ω values appear here."
            ),
        )

    time = np.asarray(data["time"], dtype=float)
    theta = np.asarray(data["theta"], dtype=float)
    frequencies = np.asarray(data["frequencies"], dtype=float)
    adjacency = np.asarray(data["adjacency"], dtype=float)

    config = data.get("config", {})
    seed_val = int(config.get("seed", 27))
    network_type = str(config.get("network_type", "All-to-All"))

    return (
        phase_heatmap_figure(time, theta),
        phase_trajectories_figure(time, theta, frequencies),
        network_figure(adjacency, frequencies, seed_val, network_type=network_type),
        frequency_distribution_figure(frequencies),
    )


def handle_update_visuals(
    data: dict[str, Any] | None,
    frame: int | None,
) -> tuple[go.Figure, go.Figure, go.Figure, go.Figure, go.Figure, go.Figure, Any]:
    """Compute and return all 6 Plotly figures and metric cards for current frame."""
    circle_fig, order_fig, cards = handle_update_animation_visuals(data, frame)
    heatmap_fig, traj_fig, net_fig, freq_fig = handle_update_static_visuals(data)
    return (
        circle_fig,
        order_fig,
        heatmap_fig,
        traj_fig,
        net_fig,
        freq_fig,
        cards,
    )


def register_visualization_callbacks(app: Dash) -> None:
    """Register reactive visual callbacks responding to simulation store and slider changes."""

    @app.callback(
        Output("unit-circle", "figure"),
        Output("order-plot", "figure"),
        Output("metric-cards", "children"),
        Input("simulation-store", "data"),
        Input("time-slider", "value"),
    )
    def update_animation_visuals(
        data: dict[str, Any] | None,
        frame: int | None,
    ) -> tuple[go.Figure, go.Figure, Any]:
        return handle_update_animation_visuals(data, frame)

    @app.callback(
        Output("phase-history", "figure"),
        Output("phase-trajectories", "figure"),
        Output("network-graph", "figure"),
        Output("frequency-plot", "figure"),
        Input("simulation-store", "data"),
    )
    def update_static_visuals(
        data: dict[str, Any] | None,
    ) -> tuple[go.Figure, go.Figure, go.Figure, go.Figure]:
        return handle_update_static_visuals(data)
