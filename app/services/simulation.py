"""Simulation routines and benchmark interfacing for the Kuramoto model."""

from __future__ import annotations

import json
from typing import Any, Optional

import numpy as np
try:
    from kuramoto.model import order_parameter
except ImportError:
    def order_parameter(phases: np.ndarray) -> np.ndarray:
        """Compute Kuramoto order parameter r(t) for phase time series."""
        return np.abs(np.mean(np.exp(1j * phases), axis=-1))

from app.services.distributions import DistributionRegistry
from app.services.solvers import SolverRegistry
from app.services.topology import TopologyRegistry, parse_custom_adjacency
from app.services.validation import validate_simulation_inputs


def build_cli_simulation_json(
    n_oscillators: int,
    coupling: float,
    simulation_time: float,
    dt: float,
    seed: int,
    frequency_distribution: str,
    network_type: str,
    solver: str = "rk45",
    frequency_mean: float = 0.0,
    frequency_std: float = 1.0,
    custom_frequencies: str = "",
) -> str:
    """Construct a JSON configuration payload conforming to the kuramoto CLI specification."""
    timesteps = max(2, int(np.round(simulation_time / dt)))
    dist_type = frequency_distribution.strip().lower()

    freq_dict: dict[str, Any] = {
        "type": "normal",
        "mean": frequency_mean,
        "std": frequency_std,
    }
    if dist_type in {"uniform", "flat"}:
        half_width = frequency_std * np.sqrt(3)
        freq_dict = {
            "type": "uniform",
            "low": frequency_mean - half_width,
            "high": frequency_mean + half_width,
        }
    elif dist_type in {"custom"}:
        try:
            tokens = [
                float(item.strip())
                for item in custom_frequencies.split(",")
                if item.strip()
            ]
            freq_dict = {"type": "custom", "values": tokens}
        except Exception:
            freq_dict = {"type": "normal", "mean": frequency_mean, "std": frequency_std}

    payload = {
        "n_oscillators": int(n_oscillators),
        "coupling_strength": float(coupling),
        "timesteps": timesteps,
        "dt": float(dt),
        "seed": int(seed),
        "topology": network_type.strip().lower().replace(" ", "_"),
        "solver": solver.strip().lower(),
        "frequency_distribution": freq_dict,
    }
    return json.dumps(payload)


def generate_frequencies(
    n: int,
    distribution: str = "Normal",
    seed: int = 0,
    mean: float = 0.0,
    std: float = 1.0,
    custom_values: str = "",
) -> np.ndarray:
    """Generate natural frequencies omega for n oscillators using the DistributionRegistry."""
    dist_name = (distribution or "Normal").strip().lower().replace(" ", "_")
    parsed_custom: Optional[list[float]] = None
    if custom_values:
        try:
            parsed_custom = [
                float(item.strip()) for item in custom_values.split(",") if item.strip()
            ]
        except Exception:
            parsed_custom = None

    return DistributionRegistry.sample(
        name=dist_name,
        n=n,
        seed=seed,
        mean=mean,
        std=std,
        custom_values=parsed_custom,
    )


def build_adjacency(
    network_type: str,
    n: int,
    seed: int = 0,
    custom_text: str = "",
) -> np.ndarray:
    """Build adjacency matrix for the specified network topology using TopologyRegistry."""
    net = (
        (network_type or "all_to_all")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

    if net in {"custom", "custom_matrix", "custom_adjacency"}:
        return parse_custom_adjacency(custom_text, n_expected=n)

    return TopologyRegistry.generate(net, n=n, seed=seed)


def generate_dataset(
    n_oscillators: int,
    coupling: float,
    simulation_time: float,
    dt: float,
    seed: int,
    solver: str,
    frequencies: np.ndarray,
    adjacency: np.ndarray,
    **kwargs: Any,
) -> dict[str, np.ndarray]:
    """Generate simulation time series, phases, and order parameter using SolverRegistry."""
    solver_key = (solver or "rk45").strip().lower()

    times, phases = SolverRegistry.solve(
        solver_name=solver_key,
        omega=frequencies,
        adj_matrix=adjacency,
        k_coupling=coupling,
        t_span=simulation_time,
        dt=dt,
        seed=seed,
        **kwargs,
    )

    r = order_parameter(phases)

    return {
        "time": times,
        "theta": phases,
        "order_parameter": r,
        "frequencies": frequencies,
        "adjacency": adjacency,
    }


def collect_config(
    n_oscillators: int | None,
    coupling: float | None,
    simulation_time: float | None,
    dt: float | None,
    seed: int | None,
    frequency_distribution: str | None,
    network_type: str | None,
    solver: str | None,
    frequency_mean: float | None = None,
    frequency_std: float | None = None,
    custom_frequencies: str | None = None,
    custom_adjacency: str | None = None,
    track_symmetries: bool | list[str] | str | None = None,
) -> dict[str, Any]:
    """Validate and package input arguments for simulation run matching CLI configurations."""
    validated = validate_simulation_inputs(
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

    frequencies = generate_frequencies(
        n=validated["n_oscillators"],
        distribution=validated["frequency_distribution"],
        seed=validated["seed"],
        mean=validated["frequency_mean"],
        std=validated["frequency_std"],
        custom_values=validated["custom_frequencies"],
    )

    adjacency = build_adjacency(
        network_type=validated["network_type"],
        n=validated["n_oscillators"],
        seed=validated["seed"],
        custom_text=validated["custom_adjacency"],
    )

    return {
        **validated,
        "frequencies": frequencies,
        "adjacency": adjacency,
    }
