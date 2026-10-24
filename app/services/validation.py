"""Input validation services for simulation parameters."""

from __future__ import annotations

from typing import Any

import numpy as np

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


def check_nyquist_sampling(
    dt: float,
    frequencies: np.ndarray | list[float] | None = None,
    coupling: float = 0.0,
    mean_freq: float = 0.0,
    std_freq: float = 1.0,
) -> dict[str, Any]:
    """Evaluate whether the time step dt satisfies Nyquist-Shannon sampling criterion.

    Parameters
    ----------
    dt : float
        Integration time step in seconds.
    frequencies : np.ndarray | list[float] | None
        Sampled natural frequencies of oscillators (in rad/s).
    coupling : float
        Global coupling constant K.
    mean_freq : float
        Mean natural frequency if frequencies array is not yet generated.
    std_freq : float
        Standard deviation of natural frequency.

    Returns
    -------
    dict[str, Any]
        Dictionary containing:
        - 'status': 'undersampled' | 'oversampled' | 'optimal'
        - 'level': 'warning' | 'info' | 'success'
        - 'sampling_rate': Sampling frequency f_s in Hz (1 / dt)
        - 'max_frequency': Max dynamic frequency f_max in Hz
        - 'nyquist_rate': Minimum required sampling rate 2 * f_max
        - 'nyquist_dt': Maximum dt to avoid aliasing (1 / (2 * f_max))
        - 'sampling_ratio': Ratio of f_s to Nyquist rate (f_s / (2 * f_max))
        - 'message': Human-readable explanation and warning banner text.
    """
    if dt <= 0:
        return {
            "status": "undersampled",
            "level": "critical",
            "sampling_rate": 0.0,
            "max_frequency": 0.0,
            "nyquist_rate": 0.0,
            "nyquist_dt": 0.0,
            "sampling_ratio": 0.0,
            "message": "⚠️ Time step dt must be strictly positive.",
        }

    # Determine maximum angular frequency omega_max
    if frequencies is not None and len(frequencies) > 0:
        freq_arr = np.asarray(frequencies, dtype=float)
        omega_max = float(np.max(np.abs(freq_arr)))
    else:
        # Statistical estimate based on 3-sigma bound
        omega_max = float(abs(mean_freq) + 3.0 * abs(std_freq))

    # Incorporate coupling interaction contribution to peak phase velocity d(theta)/dt
    # In Kuramoto model, |d(theta)/dt| <= |omega_i| + K * sum(A_ij) / N <= |omega_i| + K
    effective_omega_max = max(omega_max + max(0.0, float(coupling)), 0.1)

    # Convert angular frequency (rad/s) to cyclic frequency (Hz)
    f_max = effective_omega_max / (2.0 * np.pi)
    nyquist_rate = 2.0 * f_max
    nyquist_dt = 1.0 / nyquist_rate if nyquist_rate > 0 else 1.0

    sampling_rate = 1.0 / dt
    sampling_ratio = sampling_rate / nyquist_rate if nyquist_rate > 0 else 1.0

    if dt > nyquist_dt:
        status = "undersampled"
        level = "warning"
        message = (
            f"⚠️ Undersampling (Nyquist Violation): dt = {dt:.4f}s > dt_nyquist = {nyquist_dt:.4f}s "
            f"(f_s = {sampling_rate:.1f} Hz < 2·f_max = {nyquist_rate:.1f} Hz). "
            f"Risk of temporal aliasing, artificial phase jumps, or solver instability."
        )
    elif sampling_ratio > 40.0:
        status = "oversampled"
        level = "info"
        message = (
            f"ℹ️ Heavy Oversampling: dt = {dt:.4f}s is {sampling_ratio:.1f}× above Nyquist rate "
            f"(dt_nyquist = {nyquist_dt:.4f}s). Long horizons may increase compute time and memory usage."
        )
    else:
        status = "optimal"
        level = "success"
        message = (
            f"✓ Nyquist Criterion Satisfied: dt = {dt:.4f}s provides {sampling_ratio:.1f}× oversampling "
            f"(f_s = {sampling_rate:.1f} Hz vs 2·f_max = {nyquist_rate:.1f} Hz)."
        )

    return {
        "status": status,
        "level": level,
        "sampling_rate": sampling_rate,
        "max_frequency": f_max,
        "nyquist_rate": nyquist_rate,
        "nyquist_dt": nyquist_dt,
        "sampling_ratio": sampling_ratio,
        "message": message,
    }


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
