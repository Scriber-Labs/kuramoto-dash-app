"""Input validation services for simulation parameters."""

from __future__ import annotations

from typing import Any

from app.config import (
    DEFAULTS,
    MAX_COUPLING,
    MAX_DT,
    MAX_OSCILLATORS,
    MAX_SIMULATION_TIME,
    MIN_COUPLING,
    MIN_DT,
    MIN_OSCILLATORS,
    MIN_SIMULATION_TIME,
)


def validate_simulation_inputs(
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
) -> dict[str, Any]:
    """Validate and sanitize user input simulation parameters.

    Raises
    ------
    ValueError
        If any parameter violates domain constraints or boundaries.
    """
    net_type = (network_type or DEFAULTS["network_type"]).strip()

    # If Tree of Life is selected, n_oscillators is fixed to 10
    if net_type.lower() in {"tree_of_life", "tree of life", "etz hayim"}:
        n = 10
    else:
        try:
            n = int(
                n_oscillators
                if n_oscillators is not None
                else DEFAULTS["n_oscillators"]
            )
        except (TypeError, ValueError) as err:
            raise ValueError("Oscillator count must be an integer.") from err

        if n < MIN_OSCILLATORS:
            raise ValueError(f"The model needs at least {MIN_OSCILLATORS} oscillators.")
        if n > MAX_OSCILLATORS:
            raise ValueError(
                f"The dashboard supports at most {MAX_OSCILLATORS} oscillators per run."
            )

    try:
        total_time = float(
            simulation_time
            if simulation_time is not None
            else DEFAULTS["simulation_time"]
        )
        step = float(dt if dt is not None else DEFAULTS["dt"])
    except (TypeError, ValueError) as err:
        raise ValueError("Simulation time and dt must be numeric.") from err

    if total_time <= 0 or step <= 0:
        raise ValueError("Simulation time and time step must be positive.")
    if total_time < MIN_SIMULATION_TIME or total_time > MAX_SIMULATION_TIME:
        raise ValueError(
            f"Simulation time must be between {MIN_SIMULATION_TIME} and {MAX_SIMULATION_TIME}."
        )
    if step < MIN_DT or step > MAX_DT:
        raise ValueError(f"Time step dt must be between {MIN_DT} and {MAX_DT}.")

    try:
        k = float(coupling if coupling is not None else DEFAULTS["coupling"])
    except (TypeError, ValueError) as err:
        raise ValueError("Coupling constant K must be numeric.") from err

    if k < MIN_COUPLING or k > MAX_COUPLING:
        raise ValueError(
            f"Coupling constant must be between {MIN_COUPLING} and {MAX_COUPLING}."
        )

    try:
        seed_val = int(seed if seed is not None else DEFAULTS["seed"])
        if seed_val < 0:
            seed_val = 0
    except (TypeError, ValueError):
        seed_val = 0

    mean_val = float(
        frequency_mean if frequency_mean is not None else DEFAULTS["frequency_mean"]
    )
    std_val = float(
        frequency_std if frequency_std is not None else DEFAULTS["frequency_std"]
    )
    if std_val <= 0:
        raise ValueError("Frequency standard deviation must be positive.")

    freq_dist = frequency_distribution or DEFAULTS["frequency_distribution"]
    solv = solver or DEFAULTS["solver"]
    cust_freq = str(
        custom_frequencies
        if custom_frequencies is not None
        else DEFAULTS["custom_frequencies"]
    )
    cust_adj = str(
        custom_adjacency
        if custom_adjacency is not None
        else DEFAULTS["custom_adjacency"]
    )

    return {
        "n_oscillators": n,
        "coupling": k,
        "simulation_time": total_time,
        "dt": step,
        "seed": seed_val,
        "frequency_distribution": freq_dist,
        "network_type": net_type,
        "solver": solv,
        "frequency_mean": mean_val,
        "frequency_std": std_val,
        "custom_frequencies": cust_freq,
        "custom_adjacency": cust_adj,
    }
