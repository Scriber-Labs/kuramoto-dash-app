"""Metric, equation, and informational cards for Kuramoto Dash UI."""

from __future__ import annotations

from typing import Any

import numpy as np
from dash import html


def metric_cards(data: dict[str, Any] | None, frame: int | None) -> html.Div | list:
    """Generate responsive metric cards summarizing current synchronization state."""
    if not data or "order_parameter" not in data or "theta" not in data:
        return []

    order = np.asarray(data["order_parameter"])
    theta = np.asarray(data["theta"])
    time = np.asarray(data["time"])
    idx = max(0, min(int(frame or 0), len(order) - 1))

    cards = [
        ("Current r", f"{order[idx]:.3f}"),
        ("Peak r", f"{np.max(order):.3f}"),
        ("Time", f"{float(time[idx]):.2f}s"),
        ("Oscillators", f"{theta.shape[1]}"),
    ]

    return html.Div(
        [
            html.Div(
                [
                    html.Span(label, className="metric-label"),
                    html.Strong(value),
                ],
                className="metric-card",
            )
            for label, value in cards
        ],
        className="metric-grid",
    )


def equation_card() -> html.Div:
    """Generate the mathematical model equation card."""
    return html.Div(
        [
            html.Div("MODEL", className="eyebrow"),
            html.Div("dθᵢ/dt = ωᵢ + K/N Σ Aᵢⱼ sin(θⱼ − θᵢ)", className="equation"),
            html.Div("Adaptive RK45 or fixed-step Euler", className="hero-footnote"),
        ],
        className="equation-card",
    )


def hero_section() -> html.Section:
    """Generate the hero banner section with problem summary and model equation."""
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
                        src="/assets/images/logo.png",
                        alt="The Scriber Experience logo",
                        className="brand-mark",
                    ),
                    html.Div(
                        [
                            html.P("KURAMOTO LAB", className="eyebrow"),
                            html.H1("Synchrony, made visible."),
                        ]
                    ),
                ],
                className="brand-lockup",
            ),
            html.Div(
                [
                    html.Span("DASH WORKBENCH", className="status-pill"),
                    html.Span("benchmark-ready", className="header-note"),
                ],
                className="header-meta",
            ),
        ],
        className="topbar",
    )


def footer_section() -> html.Footer:
    """Generate the application footer."""
    return html.Footer("Kuramoto Lab · Dash interface · reproducible simulation exports", className="footer")
