"""Simulation execution and reset callbacks."""

from __future__ import annotations

from typing import Any

from dash import Dash, Input, Output, State, ctx

from app.services import collect_config, generate_dataset, package_simulation_payload


def handle_run_or_reset(
    triggered_id: str | None,
    n_oscillators: int | None,
    coupling: float | None,
    simulation_time: float | None,
    dt: float | None,
    seed: int | None,
    frequency_distribution: str | None,
    network_type: str | None,
    solver: str | None,
    frequency_mean: float | None,
    frequency_std: float | None,
    custom_frequencies: str | None,
    custom_adjacency: str | None = None,
) -> tuple[dict[str, Any] | None, int, int, str]:
    """Execute simulation run or reset state."""
    if triggered_id == "reset-btn":
        return None, 1, 0, "Ready for a new run."

    try:
        config = collect_config(
            n_oscillators=n_oscillators,
            coupling=coupling,
            simulation_time=simulation_time,
            dt=dt,
            seed=seed,
            frequency_distribution=frequency_distribution,
            network_type=network_type,
            solver=solver,
            frequency_mean=frequency_mean,
            frequency_std=frequency_std,
            custom_frequencies=custom_frequencies,
            custom_adjacency=custom_adjacency,
        )
        dataset = generate_dataset(**config)
        payload = package_simulation_payload(dataset, config)
        n_frames = len(payload["time"])
        status_msg = (
            f"Generated {n_frames} frames · {config['solver']} · seed {config['seed']}"
        )
        return payload, n_frames - 1, 0, status_msg
    except (TypeError, ValueError) as error:
        return None, 1, 0, f"Could not run: {error}"


def register_simulation_callbacks(app: Dash) -> None:
    """Register simulation execution and state management callbacks."""

    @app.callback(
        Output("simulation-store", "data"),
        Output("time-slider", "max"),
        Output("time-slider", "value", allow_duplicate=True),
        Output("run-status", "children"),
        Input("run-btn", "n_clicks"),
        Input("reset-btn", "n_clicks"),
        State("n-oscillators", "value"),
        State("coupling", "value"),
        State("simulation-time", "value"),
        State("dt", "value"),
        State("seed", "value"),
        State("frequency-distribution", "value"),
        State("network-type", "value"),
        State("solver", "value"),
        State("frequency-mean", "value"),
        State("frequency-std", "value"),
        State("custom-frequencies", "value"),
        State("custom-adjacency", "value"),
        prevent_initial_call="initial_duplicate",
    )
    def run_or_reset(
        run_clicks: int | None,
        reset_clicks: int | None,
        n_oscillators: int | None,
        coupling: float | None,
        simulation_time: float | None,
        dt: float | None,
        seed: int | None,
        frequency_distribution: str | None,
        network_type: str | None,
        solver: str | None,
        frequency_mean: float | None,
        frequency_std: float | None,
        custom_frequencies: str | None,
        custom_adjacency: str | None,
    ) -> tuple[dict[str, Any] | None, int, int, str]:
        return handle_run_or_reset(
            triggered_id=getattr(ctx, "triggered_id", None),
            n_oscillators=n_oscillators,
            coupling=coupling,
            simulation_time=simulation_time,
            dt=dt,
            seed=seed,
            frequency_distribution=frequency_distribution,
            network_type=network_type,
            solver=solver,
            frequency_mean=frequency_mean,
            frequency_std=frequency_std,
            custom_frequencies=custom_frequencies,
            custom_adjacency=custom_adjacency,
        )
