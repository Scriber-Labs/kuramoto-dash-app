"""Application layout composition for Kuramoto Lab."""

from __future__ import annotations

from dash import dcc, html

from app.components.cards import footer_section, header_section, hero_section
from app.components.controls import sidebar_controls, timeline_controls
from app.components.plots import empty_figure


def create_layout() -> html.Div:
    """Build and return the top-level Dash application layout tree."""
    return html.Div(
        [
            dcc.Store(id="simulation-store"),
            dcc.Download(id="dataset-download"),
            dcc.Interval(id="heartbeat", interval=120, n_intervals=0, disabled=False),
            header_section(),
            html.Main(
                [
                    hero_section(),
                    html.Div(
                        [
                            sidebar_controls(),
                            html.Section(
                                [
                                    html.Div(
                                        id="metric-cards", className="metrics-wrapper"
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                dcc.Graph(
                                                    id="unit-circle",
                                                    figure=empty_figure(
                                                        "Phase field",
                                                        "Run a simulation to render oscillator phases.",
                                                    ),
                                                    config={"displayModeBar": False},
                                                ),
                                                className="chart-card",
                                            ),
                                            html.Div(
                                                dcc.Graph(
                                                    id="order-plot",
                                                    figure=empty_figure(
                                                        "Synchronization strength",
                                                        "Run a simulation to chart r(t).",
                                                    ),
                                                    config={"displayModeBar": False},
                                                ),
                                                className="chart-card",
                                            ),
                                        ],
                                        className="chart-grid chart-grid-top",
                                    ),
                                    timeline_controls(),
                                    html.Div(
                                        [
                                            html.Div(
                                                dcc.Graph(
                                                    id="network-graph",
                                                    figure=empty_figure(
                                                        "Coupling network",
                                                        "Network structure appears after a run.",
                                                    ),
                                                    config={"displayModeBar": False},
                                                ),
                                                className="chart-card",
                                            ),
                                            html.Div(
                                                dcc.Graph(
                                                    id="frequency-plot",
                                                    figure=empty_figure(
                                                        "Natural frequency distribution",
                                                        "The sampled ω values appear here.",
                                                    ),
                                                    config={"displayModeBar": False},
                                                ),
                                                className="chart-card",
                                            ),
                                        ],
                                        className="chart-grid",
                                    ),
                                    html.Div(
                                        dcc.Graph(
                                            id="phase-history",
                                            figure=empty_figure(
                                                "Oscillator phase history",
                                                "The phase heatmap appears after a run.",
                                            ),
                                            config={"displayModeBar": False},
                                        ),
                                        className="chart-card",
                                    ),
                                    html.Div(
                                        dcc.Graph(
                                            id="phase-trajectories",
                                            figure=empty_figure(
                                                "Individual phase trajectories",
                                                "Each oscillator gets a color-matched phase trace after a run.",
                                            ),
                                            config={"displayModeBar": False},
                                        ),
                                        className="chart-card",
                                    ),
                                    # Advanced Invariant, Symmetry, Spectral & Quantum Diagnostics Panel
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.P(
                                                        "Benchmark & Invariant Diagnostics Suite",
                                                        className="eyebrow",
                                                    ),
                                                    html.H3("Lie Symmetries, Spectral Dynamics & Quantum SCF"),
                                                ],
                                                className="panel-heading",
                                                style={"marginBottom": "12px"},
                                            ),
                                            dcc.Tabs(
                                                id="diagnostic-tabs",
                                                value="lie-symmetry-tab",
                                                className="diagnostic-tabs",
                                                children=[
                                                    dcc.Tab(
                                                        label="Lie Invariants & Reversibility",
                                                        value="lie-symmetry-tab",
                                                        className="custom-tab",
                                                        selected_className="custom-tab--selected",
                                                        children=[
                                                            dcc.Graph(
                                                                id="symmetry-plot",
                                                                figure=empty_figure(
                                                                    "Lie Symmetry & Invariant Diagnostics",
                                                                    "Select a Lie group/Rotor solver or enable Lie symmetry tracking to view U(1) and Noether curves.",
                                                                ),
                                                                config={"displayModeBar": False},
                                                            ),
                                                        ],
                                                    ),
                                                    dcc.Tab(
                                                        label="Continuous U(1) Invariance",
                                                        value="u1-tab",
                                                        className="custom-tab",
                                                        selected_className="custom-tab--selected",
                                                        children=[
                                                            dcc.Graph(
                                                                id="u1-invariance-plot",
                                                                figure=empty_figure(
                                                                    "Continuous U(1) Lie Rotation Invariance",
                                                                    "Continuous U(1) rotation invariance data is generated during simulation runs.",
                                                                ),
                                                                config={"displayModeBar": False},
                                                            ),
                                                        ],
                                                    ),
                                                    dcc.Tab(
                                                        label="Spectral Dynamics (PSD / FFT)",
                                                        value="spectral-tab",
                                                        className="custom-tab",
                                                        selected_className="custom-tab--selected",
                                                        children=[
                                                            dcc.Graph(
                                                                id="spectral-plot",
                                                                figure=empty_figure(
                                                                    "Spectral Dynamics: PSD (Welch) & Fourier FFT",
                                                                    "Spectral dynamics will render after running a simulation.",
                                                                ),
                                                                config={"displayModeBar": False},
                                                            ),
                                                        ],
                                                    ),
                                                    dcc.Tab(
                                                        label="Quantum Mode Comparison",
                                                        value="quantum-tab",
                                                        className="custom-tab",
                                                        selected_className="custom-tab--selected",
                                                        children=[
                                                            dcc.Graph(
                                                                id="quantum-comparison-plot",
                                                                figure=empty_figure(
                                                                    "Quantum Mode: Statevector Baseline vs NISQ Shot Sampling",
                                                                    "Select a Quantum SCF solver to display statevector vs shot sampling with dispersion.",
                                                                ),
                                                                config={"displayModeBar": False},
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                        ],
                                        id="symmetry-card-container",
                                        className="chart-card diagnostic-suite-card",
                                    ),
                                ],
                                className="visual-panel",
                            ),
                        ],
                        className="workspace-grid",
                    ),
                ],
                className="page-shell",
            ),
            footer_section(),
        ],
        className="app-shell",
    )
