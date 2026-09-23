"""Configuration constants and defaults for the Kuramoto Dash application."""

from __future__ import annotations

from typing import Any

# Simulation default parameters
DEFAULTS: dict[str, Any] = {
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

# Network and oscillator visual colorscale
NETWORK_COLORSCALE = [
    [0.0, "#7652f5"],
    [0.35, "#5280ff"],
    [0.7, "#14b5ff"],
    [1.0, "#22f792"],
]

# Validation boundaries
MIN_OSCILLATORS = 2
MAX_OSCILLATORS = 100
MIN_COUPLING = 0.0
MAX_COUPLING = 20.0
MIN_SIMULATION_TIME = 0.1
MAX_SIMULATION_TIME = 500.0
MIN_DT = 0.001
MAX_DT = 1.0
