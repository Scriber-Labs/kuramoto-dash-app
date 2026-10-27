"""Metric, equation, and informational cards for Kuramoto Dash UI."""

from __future__ import annotations

from typing import Any

import numpy as np
import dash
from dash import dcc, html


def _asset_url(filename: str) -> str:
    """Safely obtain asset URL respecting Dash pathname prefix configuration."""
    try:
        return dash.get_asset_url(filename)
    except Exception:
        clean = filename.lstrip("/")
        return f"/assets/{clean}"


def metric_cards(data: dict[str, Any] | None, frame: int | None) -> html.Div | list:
    """Generate responsive metric cards summarizing current synchronization state."""
    if not data or "order_parameter" not in data or "theta" not in data:
        return []

    order = np.asarray(data["order_parameter"])
    theta = np.asarray(data["theta"])
    time = np.asarray(data["time"])
    idx = max(0, min(int(frame or 0), len(order) - 1))

    card_items = [
        (
            "Current r",
            f"{float(order[idx]):.3f}",
            "Phase coherence",
            "r(t)",
            "metric-card metric-current",
        ),
        (
            "Peak r",
            f"{float(np.max(order)):.3f}",
            "Max coherence",
            "max(r)",
            "metric-card metric-peak",
        ),
        (
            "Time",
            f"{float(time[idx]):.2f}s",
            "Elapsed timeline",
            "t",
            "metric-card metric-time",
        ),
        (
            "Oscillators",
            f"{theta.shape[1]}",
            "Active ensemble",
            "N",
            "metric-card metric-oscillators",
        ),
    ]

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("LIVE TELEMETRY", className="eyebrow metrics-eyebrow"),
                            html.H4("Synchronization State & Metrics", className="metrics-panel-title"),
                        ],
                        className="metrics-panel-heading",
                    ),
                    html.Div(
                        [
                            html.Span(
                                f"FRAME {idx + 1} / {len(time)}",
                                className="status-pill status-pill-cyan metrics-status-pill",
                            ),
                        ],
                        className="metrics-panel-meta",
                    ),
                ],
                className="metrics-panel-header",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span(label, className="metric-label"),
                                    html.Span(badge, className="metric-badge"),
                                ],
                                className="metric-card-top",
                            ),
                            html.Strong(value, className="metric-value"),
                            html.Span(subtext, className="metric-subtext"),
                        ],
                        className=css_class,
                    )
                    for label, value, subtext, badge, css_class in card_items
                ],
                className="metric-grid",
            ),
        ],
        className="metrics-container-card",
    )


def equation_card() -> html.Div:
    """Generate the mathematical model equation card."""
    return html.Div(
        [
            html.Div("MODEL", className="eyebrow"),
            html.Div("dθᵢ/dt = ωᵢ + K/N Σ Aᵢⱼ sin(θⱼ − θᵢ)", className="equation"),
            html.Div(
                "Adaptive RK45, fixed-step Euler, or GA Cl(2) Rotors",
                className="hero-footnote",
            ),
        ],
        className="equation-card",
    )


def hero_section() -> html.Section:
    """Generate the hero banner section with problem summary, model equation, and solver selector."""
    from app.services.solvers import SolverRegistry
    solver_options = SolverRegistry.get_grouped_options()
    
    return html.Section(
        [
            html.Div(
                [
                    html.P("Interactive Kuramoto model explorer", className="eyebrow"),
                    html.H2("Tune a network. Watch coherence emerge."),
                    html.P(
                        "Use the controls to compare coupling regimes, inspect oscillator phases, "
                        "and export a reproducible benchmark dataset.",
                        className="hero-copy",
                    ),
                ],
                className="hero-copy-block",
            ),
            # Solver Selector - Prominent at the top
            html.Div(
                [
                    html.Label(
                        "🔬 Integration Scheme",
                        className="field-label hero-solver-label",
                    ),
                    dcc.Dropdown(
                        id="solver-hero",
                        options=solver_options,
                        value="rk45",
                        className="dash-dropdown hero-solver-dropdown",
                        clearable=False,
                    ),
                ],
                className="hero-solver-selector",
            ),
            equation_card(),
        ],
        className="hero",
    )


def header_section() -> html.Header:
    """Generate the top navigation branding header."""
    return html.Header(
        [
            html.Div(
                [
                    html.Img(
                        src=_asset_url("images/logo.png"),
                        alt="Scriber Labs logo",
                        className="brand-mark",
                    ),
                    html.Div(
                        [
                            html.P("SCRIBER LABS", className="eyebrow"),
                            html.H1("Kuramoto Benchmark Suite"),
                        ]
                    ),
                ],
                className="brand-lockup",
            ),
            html.Div(
                [
                    html.Span("DASH WORKBENCH", className="status-pill status-pill-cyan"),
                    html.Span("BENCHMARK-READY", className="status-pill status-pill-green"),
                ],
                className="header-meta",
            ),
        ],
        className="topbar",
    )


def footer_section() -> html.Footer:
    """Generate the professional application footer."""
    return html.Footer(
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Img(
                                    src=_asset_url("images/logo.png"),
                                    alt="Scriber Labs logo",
                                    className="footer-logo",
                                ),
                                html.Div(
                                    [
                                        html.H4("Scriber Labs", className="footer-title"),
                                        html.P(
                                            "Kuramoto Benchmark Suite & Interactive Research Lab",
                                            className="footer-subtitle",
                                        ),
                                    ]
                                ),
                            ],
                            className="footer-brand",
                        ),
                        html.Div(
                            [
                                html.A(
                                    "GitHub Repository",
                                    href="https://github.com/Scriber-Labs/kuramoto-benchmark-suite",
                                    target="_blank",
                                    rel="noopener noreferrer",
                                    className="footer-link",
                                ),
                                html.Span("•", className="footer-dot"),
                                html.A(
                                    "Documentation",
                                    href="#",
                                    className="footer-link",
                                ),
                                html.Span("•", className="footer-dot"),
                                html.A(
                                    "MIT License",
                                    href="https://opensource.org/licenses/MIT",
                                    target="_blank",
                                    rel="noopener noreferrer",
                                    className="footer-link",
                                ),
                            ],
                            className="footer-links",
                        ),
                    ],
                    className="footer-main",
                ),
                html.Div(
                    [
                        html.P(
                            "© 2026 Scriber Labs · Numerical simulation, Geometric Algebra rotors & complex network dynamics.",
                            className="footer-copy",
                        ),
                        html.Div(
                            [
                                html.Span("v1.0.0", className="footer-badge"),
                                html.Span("Python 3.12+", className="footer-badge"),
                                html.Span("Plotly / Dash", className="footer-badge"),
                            ],
                            className="footer-badges",
                        ),
                    ],
                    className="footer-bottom",
                ),
            ],
            className="footer-card",
        ),
        className="footer",
    )
