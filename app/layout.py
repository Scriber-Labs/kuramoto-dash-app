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
                                        id="metric-cards", className="metric-grid"
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
