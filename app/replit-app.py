"""Dash application for exploring and benchmarking the Kuramoto model."""

from __future__ import annotations

import json
from typing import Any

import networkx as nx
import numpy as np
import plotly.graph_objects as go
from benchmark_generator import (
    build_adjacency,
    generate_dataset,
    generate_frequencies,
)
from dash import Dash, Input, Output, State, dcc, html, no_update
from plotly.colors import sample_colorscale

app = Dash(__name__, title="Kuramoto Lab")
app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        <link rel="icon" type="image/png" href="/assets/favicon.png">
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""
server = app.server


DEFAULTS = {
    "n_oscillators": 24,
    "coupling": 2.0,
    "simulation_time": 20.0,
    "dt": 0.05,
    "seed": 42,
    "frequency_distribution": "Normal",
    "network_type": "All-to-All",
    "solver": "RK45",
    "frequency_mean": 0.0,
    "frequency_std": 1.0,
    "frequency_low": -1.0,
    "frequency_high": 1.0,
    "bimodal_left": -1.0,
    "bimodal_right": 1.0,
    "custom_frequencies": "-2, -1, -0.5, 0, 0.5, 1, 2",
}

NETWORK_COLORSCALE = [
    [0.0, "#7652f5"],
    [0.35, "#5280ff"],
    [0.7, "#14b5ff"],
    [1.0, "#22f792"],
]


def _empty_figure(title: str, message: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        title={"text": title, "font": {"size": 16, "color": "#14b5ff"}},
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(20,16,43,.22)",
        font={"family": "Aclonica, sans-serif", "color": "#8b949e"},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": "#91a4c4"},
            }
        ],
        margin={"l": 28, "r": 18, "t": 54, "b": 28},
    )
    return figure


def _base_figure(title: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        title={"text": title, "x": 0.02, "font": {"size": 16, "color": "#14b5ff"}},
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(20, 16, 43, .76)",
        font={"family": "Aclonica, sans-serif", "color": "#8b949e"},
        margin={"l": 48, "r": 18, "t": 54, "b": 42},
        legend={"orientation": "h", "y": 1.02, "x": 0},
        hoverlabel={"bgcolor": "#2a2050", "font": {"family": "Aclonica"}},
    )
    return figure


def _unit_circle_figure(
    theta: np.ndarray,
    order: float,
    order_phase: float,
    oscillator_colors: list[str] | None = None,
    history_theta: np.ndarray | None = None,
) -> go.Figure:
    figure = _base_figure("Phase field")
    circle = np.linspace(0, 2 * np.pi, 160)
    figure.add_trace(
        go.Scatter(
            x=np.cos(circle),
            y=np.sin(circle),
            mode="lines",
            line={"color": "rgba(20, 181, 255, .72)", "width": 2},
            name="unit circle",
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[-1, 1, None, 0, 0],
            y=[0, 0, None, -1, 1],
            mode="lines",
            line={"color": "rgba(158, 178, 215, .25)", "width": 1},
            name="axes",
            hoverinfo="skip",
            showlegend=False,
        )
    )
    if len(theta):
        oscillator_colors = oscillator_colors or [
            f"hsl({int(i * 300 / max(len(theta), 1))}, 88%, 66%)"
            for i in range(len(theta))
        ]

        # Render trailing shadow dots if history is provided
        if history_theta is not None and len(history_theta) > 0:
            trail_len = len(history_theta)
            for step_idx, past_phase in enumerate(history_theta):
                weight = (step_idx + 1) / (trail_len + 1)
                trail_opacity = 0.10 + 0.50 * (weight ** 1.5)
                trail_size = max(4.0, 11 * (0.45 + 0.45 * weight))

                figure.add_trace(
                    go.Scatter(
                        x=np.cos(past_phase),
                        y=np.sin(past_phase),
                        mode="markers",
                        marker={
                            "size": trail_size,
                            "color": oscillator_colors,
                            "opacity": trail_opacity,
                            "line": {"width": 0},
                        },
                        hoverinfo="skip",
                        showlegend=False,
                        name=f"trail_{step_idx}",
                    )
                )

        figure.add_trace(
            go.Scatter(
                x=np.cos(theta),
                y=np.sin(theta),
                mode="markers",
                marker={
                    "size": 11,
                    "color": oscillator_colors,
                    "line": {"color": "rgba(255,255,255,.65)", "width": 1},
                },
                text=[f"Oscillator {i + 1}" for i in range(len(theta))],
                hovertemplate="%{text}<br>phase: %{customdata:.3f} rad<extra></extra>",
                customdata=theta,
                name="oscillators",
            )
        )
    if order > 0:
        figure.add_trace(
            go.Scatter(
                x=[0, order * np.cos(order_phase)],
                y=[0, order * np.sin(order_phase)],
                mode="lines+markers",
                line={"color": "#00f5db", "width": 4},
                marker={"size": [2, 10], "color": "#00f5db"},
                name=f"mean field r={order:.3f}",
                hoverinfo="skip",
            )
        )
    figure.update_xaxes(
        range=[-1.18, 1.18], visible=False, scaleanchor="y", scaleratio=1
    )
    figure.update_yaxes(range=[-1.18, 1.18], visible=False)
    figure.update_layout(showlegend=False, height=390)
    return figure


def _order_figure(time: np.ndarray, order: np.ndarray, frame: int) -> go.Figure:
    figure = _base_figure("Synchronization strength")
    frame = max(0, min(int(frame), len(order) - 1))
    glow_layers = [
        ("rgba(255, 126, 38, 0.15)", 18),
        ("rgba(255, 154, 68, 0.22)", 12),
        ("rgba(255, 173, 102, 0.32)", 7),
    ]
    for color, width in glow_layers:
        figure.add_trace(
            go.Scatter(
                x=time,
                y=order,
                mode="lines",
                line={
                    "color": color,
                    "width": width,
                    "shape": "spline",
                    "smoothing": 0.55,
                },
                hoverinfo="skip",
                showlegend=False,
            )
        )
    figure.add_trace(
        go.Scatter(
            x=time,
            y=order,
            mode="lines",
            line={"color": "#ffad66", "width": 3, "shape": "spline", "smoothing": 0.55},
            fill="tozeroy",
            fillcolor="rgba(255, 126, 38, 0.14)",
            name="r(t)",
            hovertemplate="t=%{x:.2f}<br>r=%{y:.3f}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[time[frame]],
            y=[order[frame]],
            mode="markers",
            marker={
                "size": 12,
                "color": "#22f792",
                "line": {"color": "rgba(255, 255, 255, 0.95)", "width": 2},
            },
            name="current frame",
            hovertemplate="t=%{x:.2f}<br>r=%{y:.3f}<extra></extra>",
        )
    )
    figure.update_yaxes(
        title="order parameter r", range=[0, 1.02], gridcolor="rgba(160,180,220,.12)"
    )
    figure.update_xaxes(title="time", gridcolor="rgba(160,180,220,.12)")
    figure.update_layout(
        height=300,
        shapes=[
            {
                "type": "line",
                "x0": time[frame],
                "x1": time[frame],
                "y0": 0,
                "y1": 1,
                "line": {"color": "rgba(34, 247, 146, 0.8)", "width": 2, "dash": "dot"},
            }
        ],
    )
    return figure


def _phase_figure(time: np.ndarray, theta: np.ndarray) -> go.Figure:
    figure = _base_figure("Oscillator phase history")
    figure.add_trace(
        go.Heatmap(
            x=time,
            y=np.arange(1, theta.shape[1] + 1),
            z=np.mod(theta.T, 2 * np.pi),
            colorscale=[
                [0.0, "#161b22"],
                [0.25, "#7652f5"],
                [0.55, "#14b5ff"],
                [0.8, "#00e8ff"],
                [1.0, "#00f5db"],
            ],
            colorbar={"title": "phase", "tickvals": [0, np.pi, 2 * np.pi]},
            hovertemplate="t=%{x:.2f}<br>oscillator=%{y}<br>phase=%{z:.2f} rad<extra></extra>",
        )
    )
    figure.update_xaxes(title="time", gridcolor="rgba(160,180,220,.12)")
    figure.update_yaxes(title="oscillator", gridcolor="rgba(160,180,220,.12)")
    figure.update_layout(height=340)
    return figure


def _network_colors(frequencies: np.ndarray) -> list[str]:
    values = np.asarray(frequencies, dtype=float)
    if not len(values):
        return []
    lower = float(np.min(values))
    upper = float(np.max(values))
    if np.isclose(lower, upper):
        normalized = np.full(len(values), 0.5)
    else:
        normalized = (values - lower) / (upper - lower)
    return sample_colorscale(NETWORK_COLORSCALE, normalized.tolist())


def _phase_trajectories_figure(
    time: np.ndarray,
    theta: np.ndarray,
    frequencies: np.ndarray,
) -> go.Figure:
    figure = _base_figure("Individual phase trajectories")
    colors = _network_colors(frequencies)
    unwrapped = np.unwrap(theta, axis=0)
    for index in range(theta.shape[1]):
        figure.add_trace(
            go.Scatter(
                x=time,
                y=unwrapped[:, index],
                mode="lines",
                line={"color": colors[index], "width": 2},
                name=f"Oscillator {index + 1}",
                hovertemplate=(
                    f"Oscillator {index + 1}<br>"
                    "t=%{x:.2f}<br>phase=%{y:.3f} rad<extra></extra>"
                ),
            )
        )
    figure.update_xaxes(title="time", gridcolor="rgba(160,180,220,.12)")
    figure.update_yaxes(title="unwrapped phase θᵢ", gridcolor="rgba(160,180,220,.12)")
    figure.update_layout(
        height=380,
        legend={
            "orientation": "h",
            "y": -0.24,
            "x": 0,
            "font": {"size": 9},
        },
        margin={"l": 58, "r": 18, "t": 54, "b": 88},
    )
    return figure


def _network_figure(
    adjacency: np.ndarray, frequencies: np.ndarray, seed: int
) -> go.Figure:
    graph = nx.from_numpy_array(adjacency)
    if len(graph) <= 28:
        positions = nx.spring_layout(graph, seed=seed, scale=1.0)
    else:
        positions = nx.circular_layout(graph)

    figure = _base_figure("Coupling network")
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for left, right in graph.edges():
        edge_x.extend([positions[left][0], positions[right][0], None])
        edge_y.extend([positions[left][1], positions[right][1], None])
    figure.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line={"color": "rgba(95, 132, 189, .35)", "width": 1},
            hoverinfo="skip",
            showlegend=False,
        )
    )
    node_x = [positions[i][0] for i in graph.nodes()]
    node_y = [positions[i][1] for i in graph.nodes()]
    figure.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=[str(i + 1) for i in graph.nodes()],
            textposition="middle center",
            textfont={"size": 9, "color": "#06101f"},
            marker={
                "size": 22,
                "color": frequencies,
                "cmin": float(np.min(frequencies)) if len(frequencies) else 0,
                "cmax": float(np.max(frequencies)) if len(frequencies) else 1,
                "colorscale": NETWORK_COLORSCALE,
                "colorbar": {"title": "ω"},
                "line": {"color": "rgba(255,255,255,.75)", "width": 1},
            },
            customdata=frequencies,
            hovertemplate="oscillator %{text}<br>ω=%{customdata:.3f}<extra></extra>",
            name="oscillators",
        )
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    figure.update_layout(height=330, showlegend=False)
    return figure


def _frequency_figure(frequencies: np.ndarray) -> go.Figure:
    figure = _base_figure("Natural frequency distribution")
    figure.add_trace(
        go.Histogram(
            x=frequencies,
            nbinsx=min(18, max(6, len(frequencies) // 2)),
            marker={"color": "#7652f5", "line": {"color": "#00e8ff", "width": 1}},
            hovertemplate="ω range: %{x}<br>count: %{y}<extra></extra>",
            name="frequency",
        )
    )
    figure.update_xaxes(title="natural frequency ω", gridcolor="rgba(160,180,220,.12)")
    figure.update_yaxes(title="count", gridcolor="rgba(160,180,220,.12)")
    figure.update_layout(height=280, bargap=0.08)
    return figure


def _metrics(data: dict[str, Any], frame: int) -> html.Div:
    order = np.asarray(data["order_parameter"])
    theta = np.asarray(data["theta"])
    frame = max(0, min(frame, len(order) - 1))
    cards = [
        ("Current r", f"{order[frame]:.3f}"),
        ("Peak r", f"{np.max(order):.3f}"),
        ("Time", f"{float(data['time'][frame]):.2f}s"),
        ("Oscillators", f"{theta.shape[1]}"),
    ]
    return html.Div(
        [
            html.Div(
                [html.Span(label, className="metric-label"), html.Strong(value)],
                className="metric-card",
            )
            for label, value in cards
        ],
        className="metric-grid",
    )


def _control_group(label: str, component: Any, hint: str | None = None) -> html.Div:
    children = [html.Label(label, className="field-label"), component]
    if hint:
        children.append(html.Small(hint, className="field-hint"))
    return html.Div(children, className="field")


def _layout() -> html.Div:
    return html.Div(
        [
            dcc.Store(id="simulation-store"),
            dcc.Download(id="dataset-download"),
            dcc.Interval(id="heartbeat", interval=160, n_intervals=0, disabled=True),
            html.Header(
                [
                    html.Div(
                        [
                            html.Img(
                                src="/assets/tse-logo.png",
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
            ),
            html.Main(
                [
                    html.Section(
                        [
                            html.Div(
                                [
                                    html.P(
                                        "Interactive Kuramoto model explorer",
                                        className="eyebrow",
                                    ),
                                    html.H2("Tune a network. Watch coherence emerge."),
                                    html.P(
                                        "Use the controls to compare coupling regimes, inspect oscillator phases, "
                                        "and export a reproducible benchmark dataset.",
                                        className="hero-copy",
                                    ),
                                ],
                                className="hero-copy-block",
                            ),
                            html.Div(
                                [
                                    html.Div("MODEL", className="eyebrow"),
                                    html.Div(
                                        "dθᵢ/dt = ωᵢ + K/N Σ Aᵢⱼ sin(θⱼ − θᵢ)",
                                        className="equation",
                                    ),
                                    html.Div(
                                        "Adaptive RK45 or fixed-step Euler",
                                        className="hero-footnote",
                                    ),
                                ],
                                className="equation-card",
                            ),
                        ],
                        className="hero",
                    ),
                    html.Div(
                        [
                            html.Aside(
                                [
                                    html.Div(
                                        [
                                            html.P(
                                                "Simulation parameters",
                                                className="eyebrow",
                                            ),
                                            html.H3("Configure a run"),
                                        ],
                                        className="panel-heading",
                                    ),
                                    _control_group(
                                        "Network",
                                        dcc.Dropdown(
                                            id="network-type",
                                            className="dash-dropdown",
                                            options=[
                                                {
                                                    "label": "All-to-all",
                                                    "value": "All-to-All",
                                                },
                                                {
                                                    "label": "Ring / nearest neighbor",
                                                    "value": "Ring",
                                                },
                                                {
                                                    "label": "Random sparse",
                                                    "value": "Random",
                                                },
                                            ],
                                            value=DEFAULTS["network_type"],
                                            clearable=False,
                                        ),
                                    ),
                                    html.Div(
                                        [
                                            _control_group(
                                                "Oscillators",
                                                dcc.Input(
                                                    id="n-oscillators",
                                                    type="number",
                                                    min=2,
                                                    max=100,
                                                    step=1,
                                                    value=DEFAULTS["n_oscillators"],
                                                ),
                                            ),
                                            _control_group(
                                                "Coupling K",
                                                dcc.Input(
                                                    id="coupling",
                                                    type="number",
                                                    min=0,
                                                    max=20,
                                                    step=0.1,
                                                    value=DEFAULTS["coupling"],
                                                ),
                                            ),
                                        ],
                                        className="field-row",
                                    ),
                                    html.Div(
                                        [
                                            _control_group(
                                                "Simulation time",
                                                dcc.Input(
                                                    id="simulation-time",
                                                    type="number",
                                                    min=1,
                                                    max=200,
                                                    step=1,
                                                    value=DEFAULTS["simulation_time"],
                                                ),
                                            ),
                                            _control_group(
                                                "Time step",
                                                dcc.Input(
                                                    id="dt",
                                                    type="number",
                                                    min=0.005,
                                                    max=0.2,
                                                    step=0.005,
                                                    value=DEFAULTS["dt"],
                                                ),
                                            ),
                                        ],
                                        className="field-row",
                                    ),
                                    _control_group(
                                        "Solver",
                                        dcc.RadioItems(
                                            id="solver",
                                            options=[
                                                {"label": "RK45", "value": "RK45"},
                                                {"label": "Euler", "value": "Euler"},
                                            ],
                                            value=DEFAULTS["solver"],
                                            className="radio-row",
                                            inputClassName="radio-input",
                                        ),
                                    ),
                                    _control_group(
                                        "Natural frequencies",
                                        dcc.Dropdown(
                                            id="frequency-distribution",
                                            className="dash-dropdown",
                                            options=[
                                                {"label": "Normal", "value": "Normal"},
                                                {
                                                    "label": "Uniform",
                                                    "value": "Uniform",
                                                },
                                                {
                                                    "label": "Bimodal",
                                                    "value": "Bimodal",
                                                },
                                                {
                                                    "label": "Golden ratio sequence",
                                                    "value": "Golden Ratio",
                                                },
                                                {
                                                    "label": "Custom values",
                                                    "value": "Custom",
                                                },
                                            ],
                                            value=DEFAULTS["frequency_distribution"],
                                            clearable=False,
                                        ),
                                    ),
                                    html.Div(
                                        [
                                            _control_group(
                                                "Mean",
                                                dcc.Input(
                                                    id="frequency-mean",
                                                    type="number",
                                                    step=0.1,
                                                    value=0.0,
                                                ),
                                            ),
                                            _control_group(
                                                "Std. dev.",
                                                dcc.Input(
                                                    id="frequency-std",
                                                    type="number",
                                                    min=0.01,
                                                    step=0.1,
                                                    value=1.0,
                                                ),
                                            ),
                                        ],
                                        className="field-row",
                                    ),
                                    _control_group(
                                        "Custom values (comma-separated)",
                                        dcc.Input(
                                            id="custom-frequencies",
                                            type="text",
                                            value=DEFAULTS["custom_frequencies"],
                                        ),
                                        "Used when Custom values is selected.",
                                    ),
                                    _control_group(
                                        "Random seed",
                                        dcc.Input(
                                            id="seed",
                                            type="number",
                                            min=0,
                                            max=999999,
                                            step=1,
                                            value=DEFAULTS["seed"],
                                        ),
                                        "Same seed = same dataset.",
                                    ),
                                    html.Div(
                                        [
                                            html.Button(
                                                "Run simulation",
                                                id="run-btn",
                                                className="button button-primary",
                                            ),
                                            html.Button(
                                                "Reset",
                                                id="reset-btn",
                                                className="button button-quiet",
                                            ),
                                        ],
                                        className="button-row",
                                    ),
                                    html.Div(id="run-status", className="run-status"),
                                    html.Div(
                                        [
                                            html.P(
                                                "Benchmark export", className="eyebrow"
                                            ),
                                            html.P(
                                                "The current run uses the benchmark-suite schema and can be downloaded "
                                                "as a compressed NumPy archive.",
                                                className="panel-note",
                                            ),
                                            html.Button(
                                                "Download .npz dataset",
                                                id="download-btn",
                                                className="button button-secondary",
                                            ),
                                        ],
                                        className="export-card",
                                    ),
                                ],
                                className="control-panel",
                            ),
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
                                                    figure=_empty_figure(
                                                        "Phase field",
                                                        "Run a simulation to render oscillator phases.",
                                                    ),
                                                    config={"displayModeBar": False},
                                                ),
                                                className="chart-card chart-large",
                                            ),
                                            html.Div(
                                                dcc.Graph(
                                                    id="network-graph",
                                                    figure=_empty_figure(
                                                        "Coupling network",
                                                        "Network structure appears after a run.",
                                                    ),
                                                    config={"displayModeBar": False},
                                                ),
                                                className="chart-card",
                                            ),
                                        ],
                                        className="chart-grid chart-grid-top",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                dcc.Graph(
                                                    id="order-plot",
                                                    figure=_empty_figure(
                                                        "Synchronization strength",
                                                        "Run a simulation to chart r(t).",
                                                    ),
                                                    config={"displayModeBar": False},
                                                ),
                                                className="chart-card",
                                            ),
                                            html.Div(
                                                dcc.Graph(
                                                    id="frequency-plot",
                                                    figure=_empty_figure(
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
                                            figure=_empty_figure(
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
                                            figure=_empty_figure(
                                                "Individual phase trajectories",
                                                "Each oscillator gets a color-matched phase trace after a run.",
                                            ),
                                            config={"displayModeBar": False},
                                        ),
                                        className="chart-card",
                                    ),
                                    html.Div(
                                        [
                                            html.Label(
                                                "Inspect time slice",
                                                className="field-label",
                                            ),
                                            html.Div(
                                                [
                                                    dcc.Slider(
                                                        id="time-slider",
                                                        min=0,
                                                        max=1,
                                                        value=0,
                                                        step=1,
                                                        updatemode="drag",
                                                        tooltip={
                                                            "placement": "bottom",
                                                            "always_visible": False,
                                                        },
                                                    ),
                                                    html.Button(
                                                        "Play animation",
                                                        id="play-btn",
                                                        className="button button-quiet animation-button",
                                                    ),
                                                ],
                                                className="timeline-controls",
                                            ),
                                        ],
                                        className="timeline-card",
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
            html.Footer(
                "Kuramoto Lab · Dash interface · reproducible simulation exports",
                className="footer",
            ),
        ],
        className="app-shell",
    )


app.layout = _layout


def _collect_config(
    n_oscillators: int,
    coupling: float,
    simulation_time: float,
    dt: float,
    seed: int,
    frequency_distribution: str,
    network_type: str,
    solver: str,
    frequency_mean: float,
    frequency_std: float,
    custom_frequencies: str,
) -> dict[str, Any]:
    n = int(n_oscillators or DEFAULTS["n_oscillators"])
    if n < 2:
        raise ValueError("The model needs at least 2 oscillators.")
    if n > 100:
        raise ValueError("The dashboard supports at most 100 oscillators per run.")
    total_time = float(simulation_time or DEFAULTS["simulation_time"])
    step = float(dt or DEFAULTS["dt"])
    if total_time <= 0 or step <= 0:
        raise ValueError("Simulation time and time step must be positive.")
    frequencies = generate_frequencies(
        n,
        distribution=frequency_distribution or "Normal",
        seed=int(seed or 0),
        mean=float(frequency_mean or 0.0),
        std=float(frequency_std or 1.0),
        custom_values=custom_frequencies,
    )
    adjacency = build_adjacency(network_type or "All-to-All", n, int(seed or 0))
    return {
        "n_oscillators": n,
        "coupling": float(coupling if coupling is not None else DEFAULTS["coupling"]),
        "simulation_time": total_time,
        "dt": step,
        "seed": int(seed or 0),
        "solver": solver or "RK45",
        "frequencies": frequencies,
        "adjacency": adjacency,
        "network_type": network_type or "All-to-All",
        "frequency_distribution": frequency_distribution or "Normal",
    }


@app.callback(
    Output("simulation-store", "data"),
    Output("time-slider", "max"),
    Output("time-slider", "value"),
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
    prevent_initial_call=True,
)
def run_or_reset(
    run_clicks: int | None,
    reset_clicks: int | None,
    n_oscillators: int,
    coupling: float,
    simulation_time: float,
    dt: float,
    seed: int,
    frequency_distribution: str,
    network_type: str,
    solver: str,
    frequency_mean: float,
    frequency_std: float,
    custom_frequencies: str,
):
    from dash import ctx

    if ctx.triggered_id == "reset-btn":
        return None, 1, 0, "Ready for a new run."
    try:
        config = _collect_config(
            n_oscillators,
            coupling,
            simulation_time,
            dt,
            seed,
            frequency_distribution,
            network_type,
            solver,
            frequency_mean,
            frequency_std,
            custom_frequencies,
        )
        dataset = generate_dataset(**config)
        payload = {
            "time": dataset["time"].tolist(),
            "theta": dataset["theta"].tolist(),
            "order_parameter": dataset["order_parameter"].tolist(),
            "frequencies": dataset["frequencies"].tolist(),
            "adjacency": dataset["adjacency"].tolist(),
            "config": {
                "solver": config["solver"],
                "network_type": config["network_type"],
                "frequency_distribution": config["frequency_distribution"],
                "coupling": config["coupling"],
                "dt": config["dt"],
                "seed": config["seed"],
            },
        }
        n_frames = len(dataset["time"])
        return (
            payload,
            n_frames - 1,
            0,
            f"Generated {n_frames} frames · {config['solver']} · seed {config['seed']}",
        )
    except (TypeError, ValueError) as error:
        return None, 1, 0, f"Could not run: {error}"


@app.callback(
    Output("time-slider", "value", allow_duplicate=True),
    Input("heartbeat", "n_intervals"),
    State("simulation-store", "data"),
    State("time-slider", "value"),
    prevent_initial_call=True,
)
def advance_animation(
    _: int | None,
    stored_data: dict[str, Any] | None,
    current_frame: int | None,
):
    if not stored_data:
        return no_update
    max_frame = max(0, len(stored_data.get("time", [])) - 1)
    current = max(0, min(int(current_frame or 0), max_frame))
    return 0 if current >= max_frame else current + 1


@app.callback(
    Output("heartbeat", "disabled"),
    Output("play-btn", "children"),
    Input("play-btn", "n_clicks"),
    Input("run-btn", "n_clicks"),
    Input("reset-btn", "n_clicks"),
    State("heartbeat", "disabled"),
    prevent_initial_call=True,
)
def toggle_animation(
    _: int | None,
    __: int | None,
    ___: int | None,
    is_disabled: bool,
):
    from dash import ctx

    if ctx.triggered_id == "run-btn":
        return False, "Pause animation"
    if ctx.triggered_id == "reset-btn":
        return True, "Play animation"
    next_disabled = not bool(is_disabled)
    return next_disabled, "Play animation" if next_disabled else "Pause animation"


@app.callback(
    Output("unit-circle", "figure"),
    Output("order-plot", "figure"),
    Output("phase-history", "figure"),
    Output("phase-trajectories", "figure"),
    Output("network-graph", "figure"),
    Output("frequency-plot", "figure"),
    Output("metric-cards", "children"),
    Input("simulation-store", "data"),
    Input("time-slider", "value"),
)
def update_visuals(data: dict[str, Any] | None, frame: int | None):
    if not data:
        return (
            _empty_figure(
                "Phase field", "Run a simulation to explore oscillator phases."
            ),
            _empty_figure(
                "Synchronization strength", "Run a simulation to chart r(t)."
            ),
            _empty_figure(
                "Oscillator phase history", "The phase heatmap appears after a run."
            ),
            _empty_figure(
                "Individual phase trajectories",
                "Each oscillator gets a color-matched phase trace after a run.",
            ),
            _empty_figure("Coupling network", "Network structure appears after a run."),
            _empty_figure(
                "Natural frequency distribution", "The sampled ω values appear here."
            ),
            [],
        )
    time = np.asarray(data["time"], dtype=float)
    theta = np.asarray(data["theta"], dtype=float)
    order = np.asarray(data["order_parameter"], dtype=float)
    frequencies = np.asarray(data["frequencies"], dtype=float)
    adjacency = np.asarray(data["adjacency"], dtype=float)
    index = int(frame or 0)
    index = max(0, min(index, len(time) - 1))
    phase = theta[index]
    mean_field = np.mean(np.exp(1j * phase))
    oscillator_colors = _network_colors(frequencies)

    trail_length = 6
    start_idx = max(0, index - trail_length)
    history_theta = theta[start_idx:index] if index > start_idx else None

    return (
        _unit_circle_figure(
            phase,
            float(abs(mean_field)),
            float(np.angle(mean_field)),
            oscillator_colors,
            history_theta=history_theta,
        ),
        _order_figure(time, order, index),
        _phase_figure(time, theta),
        _phase_trajectories_figure(time, theta, frequencies),
        _network_figure(adjacency, frequencies, int(data["config"]["seed"])),
        _frequency_figure(frequencies),
        _metrics(data, index),
    )


@app.callback(
    Output("dataset-download", "data"),
    Input("download-btn", "n_clicks"),
    State("simulation-store", "data"),
    prevent_initial_call=True,
)
def download_dataset(_: int | None, data: dict[str, Any] | None):
    if not data:
        return None

    def write_dataset(file_object):
        np.savez_compressed(
            file_object,
            time=np.asarray(data["time"]),
            theta=np.asarray(data["theta"]),
            order_parameter=np.asarray(data["order_parameter"]),
            natural_frequencies=np.asarray(data["frequencies"]),
            adjacency=np.asarray(data["adjacency"]),
            metadata=json.dumps(data["config"]),
        )

    return dcc.send_bytes(write_dataset, "kuramoto_benchmark.npz")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
