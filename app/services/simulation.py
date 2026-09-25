"""Simulation routines and benchmark interfacing for the Kuramoto model."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from kuramoto.api import generate_kuramoto_dataset
from kuramoto.model import order_parameter
from kuramoto.solvers import RotorSolver
from kuramoto.topologies import load_topology

from app.services.validation import validate_simulation_inputs


def build_cli_simulation_json(
    n_oscillators: int,
    coupling: float,
    simulation_time: float,
    dt: float,
    seed: int,
    frequency_distribution: str,
    network_type: str,
    frequency_mean: float = 0.0,
    frequency_std: float = 1.0,
    custom_frequencies: str = "",
) -> str:
    """Construct a JSON configuration payload conforming to the kuramoto CLI specification."""
    timesteps = max(2, int(np.round(simulation_time / dt)))
    dist_type = frequency_distribution.strip().lower()

    freq_dict: dict[str, Any] = {"type": "normal", "mean": frequency_mean, "std": frequency_std}
    if dist_type in {"uniform", "flat"}:
        half_width = frequency_std * np.sqrt(3)
        freq_dict = {"type": "uniform", "low": frequency_mean - half_width, "high": frequency_mean + half_width}
    elif dist_type in {"custom"}:
        try:
            tokens = [float(item.strip()) for item in custom_frequencies.split(",") if item.strip()]
            freq_dict = {"type": "custom", "values": tokens}
        except Exception:
            freq_dict = {"type": "normal", "mean": frequency_mean, "std": frequency_std}

    payload = {
        "n_oscillators": int(n_oscillators),
        "coupling_strength": float(coupling),
        "timesteps": timesteps,
        "dt": float(dt),
        "seed": int(seed),
        "topology": network_type.strip().lower(),
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
    """Generate natural frequencies omega for n oscillators given a distribution."""
    rng = np.random.default_rng(seed)
    dist = (distribution or "Normal").strip().lower()

    if dist in {"normal", "gaussian"}:
        return rng.normal(loc=mean, scale=std, size=n)

    if dist in {"uniform", "flat"}:
        half_width = std * np.sqrt(3)
        return rng.uniform(low=mean - half_width, high=mean + half_width, size=n)

    if dist in {"bimodal"}:
        half = n // 2
        rest = n - half
        left = rng.normal(loc=mean - std, scale=std * 0.3, size=half)
        right = rng.normal(loc=mean + std, scale=std * 0.3, size=rest)
        values = np.concatenate([left, right])
        rng.shuffle(values)
        return values

    if dist in {"golden ratio", "golden_ratio", "golden"}:
        phi = (1.0 + np.sqrt(5.0)) / 2.0
        indices = np.arange(n)
        sequence = np.mod(indices * phi, 1.0) * 2.0 - 1.0
        return mean + sequence * std

    if dist in {"custom"}:
        try:
            tokens = [float(item.strip()) for item in custom_values.split(",") if item.strip()]
            if tokens:
                if len(tokens) >= n:
                    return np.array(tokens[:n], dtype=float)
                repeats = int(np.ceil(n / len(tokens)))
                return np.tile(tokens, repeats)[:n].astype(float)
        except (ValueError, TypeError):
            pass
        return rng.normal(loc=mean, scale=std, size=n)

    return rng.normal(loc=mean, scale=std, size=n)


def build_adjacency(network_type: str, n: int, seed: int = 0) -> np.ndarray:
    """Build adjacency matrix for the specified network topology."""
    net = (network_type or "All-to-All").strip().lower()

    if net in {"ring", "nearest neighbor", "nearest_neighbor"}:
        return np.asarray(load_topology("ring", n=n), dtype=float)

    if net in {"random", "random sparse", "random_sparse", "erdos_renyi"}:
        return np.asarray(load_topology("random", n=n, p=0.3, seed=seed), dtype=float)

    # Default to all-to-all (complete graph)
    return np.asarray(load_topology("complete", n=n), dtype=float)


def parse_adjacency_text(text: str, n: int) -> np.ndarray:
    """Parse custom adjacency text matrix into a numpy array."""
    try:
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        matrix = [[float(v) for v in line.replace(",", " ").split()] for line in lines]
        array = np.array(matrix, dtype=float)
        if array.shape == (n, n):
            return array
    except Exception:
        pass
    return build_adjacency("All-to-All", n)


def _euler_solve(
    n: int,
    frequencies: np.ndarray,
    coupling: float,
    adjacency: np.ndarray,
    timesteps: int,
    dt: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Solve Kuramoto ODE using Euler integration."""
    rng = np.random.default_rng(seed)
    theta = np.zeros((timesteps, n), dtype=float)
    theta[0] = rng.uniform(0.0, 2.0 * np.pi, size=n)
    time = np.arange(timesteps, dtype=float) * dt

    for t in range(1, timesteps):
        prev = theta[t - 1]
        phase_diffs = prev[None, :] - prev[:, None]
        interaction = np.sum(adjacency * np.sin(phase_diffs), axis=1)
        dtheta = frequencies + (coupling / n) * interaction
        theta[t] = prev + dt * dtheta

    return time, theta


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
    """Generate simulation time series, phases, and order parameter using benchmark routines."""
    timesteps = max(2, int(np.round(simulation_time / dt)))
    solver_key = (solver or "RK45").strip().upper()

    if solver_key == "EULER":
        time, theta = _euler_solve(
            n=n_oscillators,
            frequencies=frequencies,
            coupling=coupling,
            adjacency=adjacency,
            timesteps=timesteps,
            dt=dt,
            seed=seed,
        )
    elif solver_key == "ROTOR":
        try:
            rotor_solver = RotorSolver(n_oscillators=n_oscillators, dim=2, seed=seed)
            t_eval = np.arange(timesteps, dtype=float) * dt
            time, theta = rotor_solver.simulate(K=coupling, t_eval=t_eval)
        except Exception:
            # Fallback to standard RK45 if Clifford GA prerequisites not met
            dataset = generate_kuramoto_dataset(
                n_oscillators=n_oscillators,
                natural_frequencies=frequencies,
                coupling=coupling,
                timesteps=timesteps,
                dt=dt,
                adjacency=adjacency,
                seed=seed,
            )
            time = dataset["time"]
            theta = dataset["theta"]
    else:
        # Standard RK45 integration via kuramoto CLI/API engine
        dataset = generate_kuramoto_dataset(
            n_oscillators=n_oscillators,
            natural_frequencies=frequencies,
            coupling=coupling,
            timesteps=timesteps,
            dt=dt,
            adjacency=adjacency,
            seed=seed,
        )
        time = dataset["time"]
        theta = dataset["theta"]

    r = order_parameter(theta)

    return {
        "time": time,
        "theta": theta,
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
    )

    return {
        **validated,
        "frequencies": frequencies,
        "adjacency": adjacency,
    }
