"""Benchmark serialization and export services."""

from __future__ import annotations

import json
from typing import Any, BinaryIO

import numpy as np

from app.services.diagnostics import analyze_graph_topology, analyze_lie_symmetries
from app.services.validation import check_nyquist_sampling

MAX_PAYLOAD_FRAMES: int = 1000


def package_simulation_payload(
    dataset: dict[str, Any], config: dict[str, Any], max_frames: int = MAX_PAYLOAD_FRAMES
) -> dict[str, Any]:
    """Package raw numpy dataset arrays and config into serializable JSON dictionary.

    Includes smart decimation for long horizons to prevent browser memory exhaustion
    and UI freezing while preserving initial and final boundary points.
    """
    adj = np.asarray(dataset["adjacency"])
    graph_stats = analyze_graph_topology(adj)

    time_arr = np.asarray(dataset["time"], dtype=float)
    theta_arr = np.asarray(dataset["theta"], dtype=float)
    r_arr = np.asarray(dataset["order_parameter"], dtype=float)
    freqs_arr = np.asarray(dataset["frequencies"], dtype=float)

    total_steps = len(time_arr)
    # Apply downsampling stride if steps exceed max_frames to guarantee UI responsiveness
    if total_steps > max_frames:
        stride = int(np.ceil(total_steps / max_frames))
        indices = np.arange(0, total_steps, stride)
        if indices[-1] != total_steps - 1:
            indices = np.append(indices, total_steps - 1)
        
        time_downsampled = time_arr[indices]
        theta_downsampled = theta_arr[indices]
        r_downsampled = r_arr[indices]
    else:
        stride = 1
        time_downsampled = time_arr
        theta_downsampled = theta_arr
        r_downsampled = r_arr

    solver_val = str(config.get("solver", "rk45"))
    nyquist_info = check_nyquist_sampling(
        dt=float(config.get("dt", 0.05)),
        frequencies=freqs_arr,
        coupling=float(config.get("coupling", 2.0)),
        mean_freq=float(config.get("frequency_mean", 0.0)),
        std_freq=float(config.get("frequency_std", 1.0)),
        solver=solver_val,
    )

    track_syms = bool(
        config.get("track_symmetries", False)
        or solver_val.strip().lower() == "rotor"
    )
    symmetries_data = None
    if track_syms:
        symmetries_data = analyze_lie_symmetries(
            times=time_downsampled,
            phases=theta_downsampled,
            adj_matrix=adj,
            coupling=float(config.get("coupling", 2.0)),
            omega=freqs_arr,
        )

    return {
        "time": time_downsampled.tolist(),
        "theta": theta_downsampled.tolist(),
        "order_parameter": r_downsampled.tolist(),
        "frequencies": freqs_arr.tolist(),
        "adjacency": adj.tolist(),
        "graph_stats": graph_stats,
        "symmetries": symmetries_data,
        "nyquist": nyquist_info,
        "stride": stride,
        "raw_frame_count": total_steps,
        "config": {
            "solver": solver_val,
            "track_symmetries": track_syms,
            "network_type": config.get("network_type", "all_to_all"),
            "frequency_distribution": config.get("frequency_distribution", "normal"),
            "coupling": config.get("coupling", 2.0),
            "dt": config.get("dt", 0.05),
            "seed": config.get("seed", 27),
            "n_oscillators": config.get("n_oscillators", 24),
            "simulation_time": config.get("simulation_time", 50.0),
            "custom_adjacency": config.get("custom_adjacency", ""),
        },
    }


def export_dataset_npz(data: dict[str, Any], file_object: BinaryIO) -> None:
    """Serialize simulation state into compressed .npz archive conforming to the benchmark schema."""
    metadata = json.dumps(data.get("config", {}))
    stats = json.dumps(data.get("graph_stats", {}))
    symmetries_meta = json.dumps(data.get("symmetries", {})) if data.get("symmetries") else ""

    save_kwargs: dict[str, Any] = {
        "time": np.asarray(data["time"], dtype=float),
        "theta": np.asarray(data["theta"], dtype=float),
        "order_parameter": np.asarray(data["order_parameter"], dtype=float),
        "natural_frequencies": np.asarray(data["frequencies"], dtype=float),
        "adjacency": np.asarray(data["adjacency"], dtype=float),
        "metadata": metadata,
        "graph_stats": stats,
    }
    if symmetries_meta:
        save_kwargs["symmetries"] = symmetries_meta

    np.savez_compressed(file_object, **save_kwargs)
