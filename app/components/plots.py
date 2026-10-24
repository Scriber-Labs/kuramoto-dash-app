"""Plotly figure generators for the Kuramoto model visualization."""

from __future__ import annotations

from typing import Any

import networkx as nx
import numpy as np
import plotly.graph_objects as go
from plotly.colors import sample_colorscale

from app.config import NETWORK_COLORSCALE
from app.services.topology import TopologyRegistry

# High-contrast ADHD semantic palette for individual oscillators and multi-trace plots
OSCILLATOR_PALETTE = [
    "#00e8ff",  # Bright Cyan
    "#22f792",  # Neon Emerald Green
    "#9b7dff",  # Cosmic Violet
    "#f78166",  # Coral Orange
    "#ec4899",  # Hot Pink / Magenta
    "#f5ce62",  # Warm Gold / Amber
    "#14b5ff",  # Electric Blue
    "#a78bfa",  # Light Lavender Purple
    "#34d399",  # Emerald Mint
    "#fb923c",  # Vivid Orange
    "#f472b6",  # Rose Pink
    "#38bdf8",  # Sky Blue
]


def empty_figure(title: str, message: str) -> go.Figure:
    """Return an empty placeholder figure styled with a diagnostic message."""
    figure = go.Figure()
    figure.update_layout(
        title={"text": title, "font": {"size": 16, "color": "#00e8ff"}},
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 12, 35, 0.45)",
        font={"family": "Aclonica, sans-serif", "color": "#8b949e"},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": "#c5f8ff"},
            }
        ],
        margin={"l": 28, "r": 18, "t": 54, "b": 28},
    )
    return figure


def base_figure(title: str) -> go.Figure:
    """Return a base figure configured with theme typography and styling."""
    figure = go.Figure()
    figure.update_layout(
        title={"text": title, "x": 0.02, "font": {"size": 16, "color": "#00e8ff"}},
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13, 17, 28, 0.65)",
        font={"family": "Aclonica, sans-serif", "color": "#8b949e"},
        margin={"l": 48, "r": 18, "t": 54, "b": 42},
        legend={"orientation": "h", "y": 1.02, "x": 0},
        hoverlabel={"bgcolor": "#1e1642", "font": {"family": "Aclonica", "color": "#f0f6fc"}},
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
            line={"color": "rgba(0, 232, 255, 0.75)", "width": 2.5},
            name="unit circle",
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[-1, 1, None, 0, 0],
            y=[0, 0, None, -1, 1],
            mode="lines",
            line={"color": "rgba(158, 178, 215, 0.3)", "width": 1},
            name="axes",
            hoverinfo="skip",
            showlegend=False,
        )
    )
    if len(theta):
        oscillator_colors = oscillator_colors or [
            f"hsl({int(i * 360 / max(len(theta), 1))}, 92%, 65%)"
            for i in range(len(theta))
        ]
        figure.add_trace(
            go.Scatter(
                x=np.cos(theta),
                y=np.sin(theta),
                mode="markers",
                marker={
                    "size": 12,
                    "color": oscillator_colors,
                    "line": {"color": "#ffffff", "width": 1.5},
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
                line={"color": "#ffad66", "width": 4},
                marker={"size": [3, 12], "color": "#ffad66", "line": {"color": "#ffffff", "width": 1.5}},
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


def order_figure(time: np.ndarray, order: np.ndarray, frame: int) -> go.Figure:
    """Render the Kuramoto order parameter r(t) time series with glow and frame marker."""
    figure = base_figure("Synchronization strength")
    if not len(order):
        return figure
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
                "color": "#ff9a44",
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
        height=390,
        shapes=[
            {
                "type": "line",
                "x0": time[frame],
                "x1": time[frame],
                "y0": 0,
                "y1": 1,
                "line": {"color": "rgba(255, 173, 102, 0.75)", "width": 2, "dash": "dot"},
            }
        ],
    )
    return figure


def phase_heatmap_figure(time: np.ndarray, theta: np.ndarray) -> go.Figure:
    """Render phase heatmap across all oscillators and time steps with cyclic colormap."""
    figure = base_figure("Oscillator phase history")
    if not len(theta):
        return figure

    # High-contrast cyclic colormap (no green, yellow, or orange)
    # Seamlessly continuous from magenta at 0 rad through cosmic violet, deep blue, electric cyan (at π), and back to magenta (at 2π)
    cyclic_phase_colorscale = [
        [0.0, "#0070eb"],
        [0.2, "#0A95EB"],
        [0.35, "#14B5FF"],
        [0.5, "#00f0ff"],
        [0.65, "#A855F7"],
        [0.8, "#5E17EB"],
        [1.0, "#0070eb"],

    ]

    figure.add_trace(
        go.Heatmap(
            x=time,
            y=np.arange(1, theta.shape[1] + 1),
            z=np.mod(theta.T, 2 * np.pi),
            zmin=0.0,
            zmax=2 * np.pi,
            colorscale=cyclic_phase_colorscale,
            colorbar={
                "title": "phase",
                "tickvals": [0, np.pi, 2 * np.pi],
                "ticktext": ["0", "π", "2π"],
            },
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
    n_oscillators = theta.shape[1]
    if len(frequencies) == n_oscillators:
        colors = network_colors(frequencies)
    else:
        colors = [OSCILLATOR_PALETTE[i % len(OSCILLATOR_PALETTE)] for i in range(n_oscillators)]

    unwrapped = np.unwrap(theta, axis=0)
    for index in range(n_oscillators):
        osc_color = colors[index] if index < len(colors) else OSCILLATOR_PALETTE[index % len(OSCILLATOR_PALETTE)]
        figure.add_trace(
            go.Scatter(
                x=time,
                y=unwrapped[:, index],
                mode="lines",
                line={
                    "color": osc_color,
                    "width": 2.2,
                },
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


# Threshold above which node index labels are hidden to avoid unreadable clutter
NODE_LABEL_CUTOFF: int = 35


def network_figure(
    adjacency: np.ndarray,
    frequencies: np.ndarray,
    seed: int,
    network_type: str = "all_to_all",
) -> go.Figure:
    """Render network coupling graph layout with nodes colored by intrinsic frequency."""
    graph = nx.from_numpy_array(adjacency)
    n = len(graph)
    net_key = (
        (network_type or "all_to_all")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

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

    # Dynamically scale edge width and opacity with number of nodes
    if n <= 30:
        edge_width = 1.2
        edge_color = "rgba(0, 232, 255, 0.28)"
    elif n <= 100:
        edge_width = 0.8
        edge_color = "rgba(0, 232, 255, 0.20)"
    else:
        edge_width = 0.4
        edge_color = "rgba(0, 232, 255, 0.12)"

    figure.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line={"color": edge_color, "width": edge_width},
            hoverinfo="skip",
            showlegend=False,
        )
    )
    node_x = [positions[i][0] for i in graph.nodes() if i in positions]
    node_y = [positions[i][1] for i in graph.nodes() if i in positions]

    # Dynamically scale node size with population count N (between 4 and 22 px)
    if n <= 10:
        node_size = 22.0
        border_width = 1.5
    elif n <= 30:
        node_size = max(14.0, 22.0 - (n - 10) * 0.4)
        border_width = 1.2
    elif n <= 100:
        node_size = max(8.0, 14.0 - (n - 30) * 0.085)
        border_width = 0.8
    else:
        node_size = max(4.0, 8.0 - (n - 100) * 0.01)
        border_width = 0.5

    # Determine whether node numbers / labels should be displayed
    show_labels = n <= NODE_LABEL_CUTOFF or net_key in {"tree_of_life", "etz_hayim"}

    display_texts = [
        str(node_labels.get(i, i + 1)) for i in graph.nodes() if i in positions
    ]

    figure.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text" if show_labels else "markers",
            text=display_texts if show_labels else None,
            textposition="middle center",
            textfont={"size": max(7, min(9, int(node_size * 0.45))), "color": "#06101f"},
            marker={
                "size": node_size,
                "color": frequencies,
                "cmin": float(np.min(frequencies)) if len(frequencies) else 0,
                "cmax": float(np.max(frequencies)) if len(frequencies) else 1,
                "colorscale": NETWORK_COLORSCALE,
                "colorbar": {"title": "ω"},
                "line": {"color": "rgba(255,255,255,.85)", "width": border_width},
            },
            customdata=frequencies,
            hovertemplate=(
                "Node: %{text}<br>ω=%{customdata:.3f}<extra></extra>"
                if show_labels
                else "Node %{pointIndex}<br>ω=%{customdata:.3f}<extra></extra>"
            ),
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
            marker={
                "color": "rgba(34, 247, 146, 0.65)",
                "line": {"color": "#22f792", "width": 1.2},
            },
            hovertemplate="ω range: %{x}<br>count: %{y}<extra></extra>",
            name="frequency",
        )
    )
    figure.update_xaxes(title="natural frequency ω", gridcolor="rgba(160,180,220,.12)")
    figure.update_yaxes(title="count", gridcolor="rgba(160,180,220,.12)")
    figure.update_layout(height=280, bargap=0.08)
    return figure


def symmetry_figure(
    times: np.ndarray,
    symmetries: dict[str, Any] | None,
    current_index: int | None = None,
) -> go.Figure:
    """Render Lie symmetry and Noether conservation curves (Hamiltonian Energy, U(1) Charge, Cl(2) Unitarity)."""
    figure = base_figure("Lie Symmetry & Noether Diagnostics")
    if not symmetries or "interaction_energy" not in symmetries:
        return empty_figure(
            "Lie Symmetry & Noether Diagnostics",
            "Select Rotor solver or enable Lie symmetry tracking to view U(1) and Noether curves.",
        )

    t_arr = np.asarray(times, dtype=float)
    energy = np.asarray(symmetries["interaction_energy"], dtype=float)
    noether = np.asarray(symmetries["noether_charge"], dtype=float)
    unitarity = np.asarray(symmetries["rotor_unitarity"], dtype=float)

    # 1. Hamiltonian Interaction Energy E(t)
    figure.add_trace(
        go.Scatter(
            x=t_arr,
            y=energy,
            mode="lines",
            line={"color": "#00e8ff", "width": 2.2},
            name="Interaction Energy E(t)",
            hovertemplate="t=%{x:.2f}s<br>E(t)=%{y:.4f}<extra></extra>",
        )
    )

    # 2. Noether Charge / Invariant Q(t)
    figure.add_trace(
        go.Scatter(
            x=t_arr,
            y=noether,
            mode="lines",
            line={"color": "#9b7dff", "width": 1.8, "dash": "dash"},
            name="Noether Invariant Q(t)",
            hovertemplate="t=%{x:.2f}s<br>Q(t)=%{y:.4f}<extra></extra>",
        )
    )

    # 3. Rotor Cl(2) Unitarity |R(t)|^2
    figure.add_trace(
        go.Scatter(
            x=t_arr,
            y=unitarity,
            mode="lines",
            line={"color": "#22f792", "width": 1.8, "dash": "dot"},
            name="Rotor Unitarity |R|²",
            hovertemplate="t=%{x:.2f}s<br>|R|²=%{y:.4f}<extra></extra>",
        )
    )

    # Timeline scrubber vertical line
    if current_index is not None and 0 <= current_index < len(t_arr):
        current_time = float(t_arr[current_index])
        figure.add_vline(
            x=current_time,
            line_width=1.5,
            line_dash="dot",
            line_color="#f5ce62",
            annotation_text=f"t={current_time:.2f}s",
            annotation_position="top right",
            annotation_font_color="#f5ce62",
            annotation_font_size=10,
        )

    figure.update_xaxes(title="time t (s)", gridcolor="rgba(160,180,220,.12)")
    figure.update_yaxes(title="diagnostic amplitude", gridcolor="rgba(160,180,220,.12)")
    figure.update_layout(
        height=290,
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.12, "x": 0.0},
    )
    return figure
