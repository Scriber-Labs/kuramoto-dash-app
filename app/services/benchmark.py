"""Benchmark serialization and export services."""

from __future__ import annotations

import json
from typing import Any, BinaryIO

import numpy as np

from app.services.diagnostics import analyze_graph_topology
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

    nyquist_info = check_nyquist_sampling(
        dt=float(config.get("dt", 0.05)),
        frequencies=freqs_arr,
        coupling=float(config.get("coupling", 2.0)),
        mean_freq=float(config.get("frequency_mean", 0.0)),
        std_freq=float(config.get("frequency_std", 1.0)),
    )

    return {
        "time": time_downsampled.tolist(),
        "theta": theta_downsampled.tolist(),
        "order_parameter": r_downsampled.tolist(),
        "frequencies": freqs_arr.tolist(),
        "adjacency": adj.tolist(),
        "graph_stats": graph_stats,
        "nyquist": nyquist_info,
        "stride": stride,
        "raw_frame_count": total_steps,
        "config": {
            "solver": config.get("solver", "rk45"),
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

    np.savez_compressed(
        file_object,
        time=np.asarray(data["time"], dtype=float),
        theta=np.asarray(data["theta"], dtype=float),
        order_parameter=np.asarray(data["order_parameter"], dtype=float),
        natural_frequencies=np.asarray(data["frequencies"], dtype=float),
        adjacency=np.asarray(data["adjacency"], dtype=float),
        metadata=metadata,
        graph_stats=stats,
    )
