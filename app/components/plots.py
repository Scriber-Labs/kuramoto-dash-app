"""Plotly figure generators for the Kuramoto model visualization."""

from __future__ import annotations

import networkx as nx
import numpy as np
import plotly.graph_objects as go
from plotly.colors import sample_colorscale

from app.config import NETWORK_COLORSCALE
from app.services.topology import TopologyRegistry


def empty_figure(title: str, message: str) -> go.Figure:
    """Return an empty placeholder figure styled with a diagnostic message."""
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


def base_figure(title: str) -> go.Figure:
    """Return a base figure configured with theme typography and styling."""
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


def network_colors(frequencies: np.ndarray) -> list[str]:
    """Sample continuous hex colors matching natural frequency values."""
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


def unit_circle_figure(
    theta: np.ndarray,
    order: float,
    order_phase: float,
    oscillator_colors: list[str] | None = None,
) -> go.Figure:
    """Render the unit circle phase diagram with individual oscillators and order phasor."""
    figure = base_figure("Phase field")
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
    figure.update_xaxes(range=[-1.18, 1.18], visible=False, scaleanchor="y", scaleratio=1)
    figure.update_yaxes(range=[-1.18, 1.18], visible=False)
    figure.update_layout(showlegend=False, height=390)
    return figure


def order_figure(time: np.ndarray, order: np.ndarray, frame: int) -> go.Figure:
    """Render the Kuramoto order parameter r(t) time series with glow and frame marker."""
    figure = base_figure("Synchronization strength")
    if not len(order):
        return figure
    frame = max(0, min(int(frame), len(order) - 1))
    glow_layers = [
        ("rgba(118, 82, 245, .12)", 18),
        ("rgba(0, 232, 255, .14)", 12),
        ("rgba(0, 245, 219, .2)", 7),
    ]
    for color, width in glow_layers:
        figure.add_trace(
            go.Scatter(
                x=time,
                y=order,
                mode="lines",
                line={"color": color, "width": width, "shape": "spline", "smoothing": 0.55},
                hoverinfo="skip",
                showlegend=False,
            )
        )
    figure.add_trace(
        go.Scatter(
            x=time,
            y=order,
            mode="lines",
            line={"color": "#00f5db", "width": 3, "shape": "spline", "smoothing": 0.55},
            fill="tozeroy",
            fillcolor="rgba(0,245,219,.09)",
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
                "size": 11,
                "color": "#00f5db",
                "line": {"color": "#f5f3ff", "width": 2},
            },
            name="current frame",
            hovertemplate="t=%{x:.2f}<br>r=%{y:.3f}<extra></extra>",
        )
    )
    figure.update_yaxes(title="order parameter r", range=[0, 1.02], gridcolor="rgba(160,180,220,.12)")
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
                "line": {"color": "rgba(0,245,219,.28)", "width": 1, "dash": "dot"},
            }
        ],
    )
    return figure


def phase_heatmap_figure(time: np.ndarray, theta: np.ndarray) -> go.Figure:
    """Render phase heatmap across all oscillators and time steps."""
    figure = base_figure("Oscillator phase history")
    if not len(theta):
        return figure
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


def phase_trajectories_figure(
    time: np.ndarray,
    theta: np.ndarray,
    frequencies: np.ndarray,
) -> go.Figure:
    """Render unwrapped individual phase trajectories over time."""
    figure = base_figure("Individual phase trajectories")
    if not len(theta):
        return figure
    colors = network_colors(frequencies)
    unwrapped = np.unwrap(theta, axis=0)
    for index in range(theta.shape[1]):
        figure.add_trace(
            go.Scatter(
                x=time,
                y=unwrapped[:, index],
                mode="lines",
                line={"color": colors[index] if index < len(colors) else "#14b5ff", "width": 2},
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


def network_figure(
    adjacency: np.ndarray,
    frequencies: np.ndarray,
    seed: int,
    network_type: str = "all_to_all",
) -> go.Figure:
    """Render network coupling graph layout with nodes colored by intrinsic frequency."""
    graph = nx.from_numpy_array(adjacency)
    n = len(graph)
    net_key = (network_type or "all_to_all").strip().lower().replace(" ", "_").replace("-", "_")

    if net_key in {"tree_of_life", "etz_hayim"}:
        positions = TopologyRegistry.get_layout("tree_of_life", n, adjacency)
        node_labels = TopologyRegistry.get_labels("tree_of_life", n)
    elif n <= 28:
        positions = nx.spring_layout(graph, seed=seed, scale=1.0)
        node_labels = {i: str(i + 1) for i in graph.nodes()}
    else:
        positions = nx.circular_layout(graph)
        node_labels = {i: str(i + 1) for i in graph.nodes()}

    figure = base_figure("Coupling network")
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for left, right in graph.edges():
        if left in positions and right in positions:
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
    node_x = [positions[i][0] for i in graph.nodes() if i in positions]
    node_y = [positions[i][1] for i in graph.nodes() if i in positions]
    display_texts = [str(node_labels.get(i, i + 1)) for i in graph.nodes() if i in positions]

    figure.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=display_texts,
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
            hovertemplate="Node: %{text}<br>ω=%{customdata:.3f}<extra></extra>",
            name="oscillators",
        )
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    figure.update_layout(height=330, showlegend=False)
    return figure


def frequency_distribution_figure(frequencies: np.ndarray) -> go.Figure:
    """Render frequency distribution histogram."""
    figure = base_figure("Natural frequency distribution")
    if not len(frequencies):
        return figure
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
