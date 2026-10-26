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
    quantum_mode_comparison_figure,
    spectral_dynamics_figure,
    symmetry_figure,
    u1_rotation_invariance_figure,
    unit_circle_figure,
)
from app.services.diagnostics import (
    analyze_lie_symmetries,
    analyze_spectral_dynamics,
    compute_quantum_mode_comparison,
)


def handle_update_animation_visuals(
    data: dict[str, Any] | None,
    frame: int | None,
) -> tuple[go.Figure, go.Figure, Any]:
    """Compute animated figures (Unit circle phasor compass, Order parameter) and metric cards."""
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

    # Extract trailing history frames for shadow dots effect
    trail_length = 6
    start_idx = max(0, index - trail_length)
    history_theta = theta[start_idx:index] if index > start_idx else None

    return (
        unit_circle_figure(
            phase,
            float(abs(mean_field)),
            float(np.angle(mean_field)),
            osc_colors,
            history_theta=history_theta,
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


def handle_update_symmetry_visual(
    data: dict[str, Any] | None,
    frame: int | None = None,
) -> go.Figure:
    """Compute and render Lie symmetry and Noether diagnostic figure."""
    if not data or "time" not in data or not data["time"]:
        return empty_figure(
            "Lie Symmetry & Invariant Diagnostics",
            "Select a Lie group/Rotor solver or enable Lie symmetry tracking to view U(1) and Noether curves.",
        )

    symmetries = data.get("symmetries")
    if not symmetries:
        # Compute on-the-fly if not packaged
        time = np.asarray(data["time"], dtype=float)
        theta = np.asarray(data["theta"], dtype=float)
        adj = np.asarray(data["adjacency"], dtype=float)
        freqs = np.asarray(data["frequencies"], dtype=float)
        k = float(data.get("config", {}).get("coupling", 2.0))
        dt = float(data.get("config", {}).get("dt", 0.05))
        symmetries = analyze_lie_symmetries(
            times=time,
            phases=theta,
            adj_matrix=adj,
            coupling=k,
            omega=freqs,
            dt=dt,
        )

    time = np.asarray(data["time"], dtype=float)
    index = max(0, min(int(frame or 0), len(time) - 1)) if frame is not None else None
    return symmetry_figure(time, symmetries, current_index=index)


def handle_update_u1_visual(data: dict[str, Any] | None) -> go.Figure:
    """Compute and render Continuous U(1) phase rotation invariance figure."""
    if not data or "time" not in data or not data["time"]:
        return empty_figure(
            "Continuous U(1) Lie Rotation Invariance",
            "Continuous U(1) rotation invariance data is generated during simulation runs.",
        )

    symmetries = data.get("symmetries")
    if not symmetries or "u1_alphas" not in symmetries:
        time = np.asarray(data["time"], dtype=float)
        theta = np.asarray(data["theta"], dtype=float)
        adj = np.asarray(data["adjacency"], dtype=float)
        freqs = np.asarray(data["frequencies"], dtype=float)
        k = float(data.get("config", {}).get("coupling", 2.0))
        dt = float(data.get("config", {}).get("dt", 0.05))
        symmetries = analyze_lie_symmetries(
            times=time,
            phases=theta,
            adj_matrix=adj,
            coupling=k,
            omega=freqs,
            dt=dt,
        )

    return u1_rotation_invariance_figure(symmetries)


def handle_update_spectral_visual(data: dict[str, Any] | None) -> go.Figure:
    """Compute and render Power Spectral Density (PSD) and Fourier FFT spectrum."""
    if not data or "time" not in data or not data["time"]:
        return empty_figure(
            "Spectral Dynamics: PSD (Welch) & Fourier FFT",
            "Spectral dynamics will render after running a simulation.",
        )

    time = np.asarray(data["time"], dtype=float)
    order = np.asarray(data["order_parameter"], dtype=float)
    dt = float(data.get("config", {}).get("dt", 0.05))

    spectral_data = analyze_spectral_dynamics(times=time, order_param=order, dt=dt)
    return spectral_dynamics_figure(spectral_data)


def handle_update_quantum_comparison_visual(data: dict[str, Any] | None) -> go.Figure:
    """Compute and render Quantum Statevector vs NISQ Shot Sampling comparison."""
    if not data or "time" not in data or not data["time"]:
        return empty_figure(
            "Quantum Mode: Statevector Baseline vs NISQ Shot Sampling",
            "Select a Quantum SCF solver to display statevector vs shot sampling with dispersion.",
        )

    config = data.get("config", {})
    freqs = np.asarray(data["frequencies"], dtype=float)
    adj = np.asarray(data["adjacency"], dtype=float)
    k = float(config.get("coupling", 2.0))
    t_span = float(config.get("simulation_time", 20.0))
    dt = float(config.get("dt", 0.05))
    seed = int(config.get("seed", 27))
    shots = int(config.get("shots", 1024))

    # Cap oscillator count and time span for responsive quantum comparison if large
    n_osc = min(len(freqs), 6)
    sub_freqs = freqs[:n_osc]
    sub_adj = adj[:n_osc, :n_osc]
    sub_t_span = min(t_span, 15.0)

    try:
        quantum_data = compute_quantum_mode_comparison(
            omega=sub_freqs,
            adj_matrix=sub_adj,
            k_coupling=k,
            t_span=sub_t_span,
            dt=dt,
            seed=seed,
            shots=shots,
        )
        return quantum_mode_comparison_figure(quantum_data)
    except Exception as exc:
        return empty_figure(
            "Quantum Mode Comparison",
            f"Quantum SCF simulation note: {exc}",
        )


def handle_update_visuals(
    data: dict[str, Any] | None,
    frame: int | None,
) -> tuple[go.Figure, go.Figure, go.Figure, go.Figure, go.Figure, go.Figure, Any]:
    """Compute and return all 6 primary Plotly figures and metric cards for current frame."""
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

    @app.callback(
        Output("symmetry-plot", "figure"),
        Input("simulation-store", "data"),
        Input("time-slider", "value"),
    )
    def update_symmetry_visual(
        data: dict[str, Any] | None,
        frame: int | None,
    ) -> go.Figure:
        return handle_update_symmetry_visual(data, frame)

    @app.callback(
        Output("u1-invariance-plot", "figure"),
        Input("simulation-store", "data"),
    )
    def update_u1_visual(data: dict[str, Any] | None) -> go.Figure:
        return handle_update_u1_visual(data)

    @app.callback(
        Output("spectral-plot", "figure"),
        Input("simulation-store", "data"),
    )
    def update_spectral_visual(data: dict[str, Any] | None) -> go.Figure:
        return handle_update_spectral_visual(data)

    @app.callback(
        Output("quantum-comparison-plot", "figure"),
        Input("simulation-store", "data"),
    )
    def update_quantum_comparison_visual(data: dict[str, Any] | None) -> go.Figure:
        return handle_update_quantum_comparison_visual(data)
