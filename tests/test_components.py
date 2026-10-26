"""Unit tests for UI components and Plotly figures."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from app.components import (
    empty_figure,
    equation_card,
    footer_section,
    frequency_distribution_figure,
    header_section,
    hero_section,
    metric_cards,
    network_colors,
    network_figure,
    order_figure,
    phase_heatmap_figure,
    phase_trajectories_figure,
    sidebar_controls,
    symmetry_figure,
    timeline_controls,
    unit_circle_figure,
)
from app.components.plots import (
    quantum_mode_comparison_figure,
    spectral_dynamics_figure,
    u1_rotation_invariance_figure,
)


def test_empty_figure() -> None:
    fig = empty_figure("Phase field", "Run simulation to render.")
    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text == "Phase field"
    assert len(fig.layout.annotations) == 1
    assert fig.layout.annotations[0].text == "Run simulation to render."


def test_network_colors() -> None:
    freqs = np.array([-1.0, 0.0, 1.0])
    colors = network_colors(freqs)
    assert len(colors) == 3
    assert all(isinstance(c, str) for c in colors)

    empty_colors = network_colors(np.array([]))
    assert empty_colors == []


def test_unit_circle_figure() -> None:
    theta = np.array([0.0, np.pi / 2, np.pi])
    fig = unit_circle_figure(theta, order=0.75, order_phase=0.5)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 3  # unit circle line, axes, oscillators, order vector

    # Test with history for trailing shadow dots
    history = np.array([[0.0, 0.1, 0.2], [0.1, 0.2, 0.3]])
    fig_trail = unit_circle_figure(
        theta, order=0.75, order_phase=0.5, history_theta=history
    )
    assert isinstance(fig_trail, go.Figure)
    assert len(fig_trail.data) == len(fig.data) + len(history)


def test_order_figure() -> None:
    time = np.linspace(0, 10, 50)
    order = np.linspace(0.1, 0.95, 50)
    fig = order_figure(time, order, frame=10)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 4  # glow layers, main line, current frame marker


def test_phase_heatmap_figure() -> None:
    time = np.linspace(0, 5, 25)
    theta = np.zeros((25, 4))
    fig = phase_heatmap_figure(time, theta)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert isinstance(fig.data[0], go.Heatmap)
    heatmap = fig.data[0]
    colorscale = heatmap.colorscale
    assert colorscale[0][1] == colorscale[-1][1]  # 0 and 2π map to identical color
    assert list(heatmap.colorbar.tickvals) == [0, np.pi, 2 * np.pi]
    assert list(heatmap.colorbar.ticktext) == ["0", "π", "2π"]


def test_phase_trajectories_figure() -> None:
    time = np.linspace(0, 5, 25)
    theta = np.ones((25, 4))
    freqs = np.array([0.1, 0.2, 0.3, 0.4])
    fig = phase_trajectories_figure(time, theta, freqs)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 4  # 4 oscillators


def test_network_figure() -> None:
    adj = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
    freqs = np.array([-0.5, 0.0, 0.5])
    fig = network_figure(adj, freqs, seed=42)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    node_trace = fig.data[1]
    assert node_trace.mode == "markers+text"
    assert node_trace.marker.size == 22.0
    assert node_trace.text is not None


def test_frequency_distribution_figure() -> None:
    freqs = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
    fig = frequency_distribution_figure(freqs)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert isinstance(fig.data[0], go.Histogram)


def test_symmetry_figure() -> None:
    empty_sym_fig = symmetry_figure(np.array([]), None)
    assert isinstance(empty_sym_fig, go.Figure)
    assert "Lie Symmetry" in empty_sym_fig.layout.title.text

    times = np.linspace(0, 10, 50)
    symmetries = {
        "interaction_energy": [-1.2] * 50,
        "noether_charge": [0.0] * 50,
        "rotor_unitarity": [1.0] * 50,
        "reversibility_residuals": [1e-6] * 50,
    }
    fig = symmetry_figure(times, symmetries, current_index=12)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 4  # Energy, Noether, Unitarity, Reversibility
    assert fig.data[0].name == "Interaction Energy E(t)"
    assert fig.data[1].name == "Noether Invariant Q(t)"
    assert fig.data[2].name == "Rotor Unitarity |R|²"
    assert "Reversibility" in fig.data[3].name


def test_diagnostic_figures() -> None:
    # U(1) invariance plot
    u1_sym = {
        "u1_alphas": [0.0, 1.0, 2.0],
        "u1_residuals": [0.0, 1e-15, 2e-15],
    }
    u1_fig = u1_rotation_invariance_figure(u1_sym)
    assert isinstance(u1_fig, go.Figure)
    assert len(u1_fig.data) == 1

    # Spectral dynamics plot
    spec_data = {
        "psd_freqs": [0.1, 0.2, 0.3],
        "psd_power": [1.0, 0.5, 0.1],
        "fft_freqs": [0.1, 0.2, 0.3],
        "fft_amplitude": [0.8, 0.4, 0.05],
    }
    spec_fig = spectral_dynamics_figure(spec_data)
    assert isinstance(spec_fig, go.Figure)
    assert len(spec_fig.data) == 2

    # Quantum mode comparison plot
    q_data = {
        "time": [0.0, 0.1, 0.2],
        "r_statevector": [0.5, 0.6, 0.7],
        "r_shot_mean": [0.48, 0.59, 0.71],
        "r_shot_upper": [0.55, 0.65, 0.78],
        "r_shot_lower": [0.41, 0.53, 0.64],
    }
    q_fig = quantum_mode_comparison_figure(q_data)
    assert isinstance(q_fig, go.Figure)
    assert len(q_fig.data) == 3


def test_cards_and_controls() -> None:
    data = {
        "order_parameter": [0.5, 0.8, 0.9],
        "theta": [[0, 1], [0.1, 1.1], [0.2, 1.2]],
        "time": [0.0, 0.1, 0.2],
    }
    cards = metric_cards(data, frame=1)
    assert cards is not None

    empty_cards = metric_cards(None, frame=0)
    assert empty_cards == []

    assert equation_card() is not None
    assert hero_section() is not None
    header = header_section()
    assert header is not None
    footer = footer_section()
    assert footer is not None
    assert sidebar_controls() is not None
    assert timeline_controls() is not None
