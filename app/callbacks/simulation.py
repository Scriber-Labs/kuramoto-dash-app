"""Simulation execution and reset callbacks."""

from __future__ import annotations

from typing import Any

from dash import Dash, Input, Output, State, ctx, html

from app.services import (
    check_nyquist_sampling,
    collect_config,
    generate_dataset,
    generate_frequencies,
    package_simulation_payload,
)


def render_nyquist_banner(
    dt: float | None,
    coupling: float | None,
    frequency_distribution: str | None,
    frequency_mean: float | None,
    frequency_std: float | None,
    custom_frequencies: str | None,
    n_oscillators: int | None,
    seed: int | None,
    solver: str | None = None,
) -> html.Div:
    """Render illuminated Nyquist theorem status banner."""
    dt_val = float(dt if dt is not None else 0.05)
    coupling_val = float(coupling if coupling is not None else 2.0)
    mean_val = float(frequency_mean if frequency_mean is not None else 0.0)
    std_val = float(frequency_std if frequency_std is not None else 1.0)
    n_val = int(n_oscillators if n_oscillators is not None else 24)
    seed_val = int(seed if seed is not None else 27)
    solver_val = str(solver or "RK45")

    try:
        freqs = generate_frequencies(
            n=n_val,
            distribution=frequency_distribution or "Normal",
            seed=seed_val,
            mean=mean_val,
            std=std_val,
            custom_values=custom_frequencies or "",
        )
    except Exception:
        freqs = None

    nyquist = check_nyquist_sampling(
        dt=dt_val,
        frequencies=freqs,
        coupling=coupling_val,
        mean_freq=mean_val,
        std_freq=std_val,
        solver=solver_val,
    )

    status_class = f"nyquist-banner nyquist-{nyquist['level']}"
    icon = "⚠️" if nyquist["status"] in {"undersampled", "marginal"} else ("ℹ️" if nyquist["status"] == "oversampled" else "✓")

    return html.Div(
        [
            html.Div(
                [
                    html.Span(icon, className="nyquist-icon"),
                    html.Span(
                        f"Nyquist Criterion: {nyquist['status'].upper()}",
                        className="nyquist-title",
                    ),
                ],
                className="nyquist-header",
            ),
            html.P(nyquist["message"], className="nyquist-text"),
            html.Div(
                [
                    html.Span(f"f_s = {nyquist['sampling_rate']:.1f} Hz", className="nyquist-stat"),
                    html.Span("·", className="nyquist-dot"),
                    html.Span(f"2·f_max = {nyquist['nyquist_rate']:.1f} Hz", className="nyquist-stat"),
                    html.Span("·", className="nyquist-dot"),
                    html.Span(f"Ratio = {nyquist['sampling_ratio']:.1f}×", className="nyquist-stat"),
                ],
                className="nyquist-metrics",
            ),
        ],
        className=status_class,
    )


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
    track_symmetries: list[str] | bool | str | None = None,
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
            track_symmetries=track_symmetries,
        )
        dataset = generate_dataset(**config)
        payload = package_simulation_payload(dataset, config)
        n_frames = len(payload["time"])
        sym_note = " · Lie symmetries tracked" if payload.get("symmetries") else ""
        status_msg = (
            f"Generated {n_frames} frames · {config['solver']}{sym_note} · seed {config['seed']}"
        )
        return payload, n_frames - 1, 0, status_msg
    except (TypeError, ValueError) as error:
        return None, 1, 0, f"Could not run: {error}"


def register_simulation_callbacks(app: Dash) -> None:
    """Register simulation execution and state management callbacks."""

    @app.callback(
        Output("nyquist-warning-banner", "children"),
        Input("dt", "value"),
        Input("coupling", "value"),
        Input("frequency-distribution", "value"),
        Input("frequency-mean", "value"),
        Input("frequency-std", "value"),
        Input("custom-frequencies", "value"),
        Input("n-oscillators", "value"),
        Input("seed", "value"),
        Input("solver", "value"),
    )
    def update_nyquist_warning(
        dt: float | None,
        coupling: float | None,
        frequency_distribution: str | None,
        frequency_mean: float | None,
        frequency_std: float | None,
        custom_frequencies: str | None,
        n_oscillators: int | None,
        seed: int | None,
        solver: str | None,
    ) -> html.Div:
        return render_nyquist_banner(
            dt=dt,
            coupling=coupling,
            frequency_distribution=frequency_distribution,
            frequency_mean=frequency_mean,
            frequency_std=frequency_std,
            custom_frequencies=custom_frequencies,
            n_oscillators=n_oscillators,
            seed=seed,
            solver=solver,
        )

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
        State("track-symmetries", "value"),
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
        track_symmetries: list[str] | bool | str | None,
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
            track_symmetries=track_symmetries,
        )
