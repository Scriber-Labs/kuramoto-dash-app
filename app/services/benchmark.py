"""Benchmark serialization and export services."""

from __future__ import annotations

import json
from typing import Any, BinaryIO

import numpy as np


def package_simulation_payload(dataset: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Package raw numpy dataset arrays and config into serializable JSON dictionary."""
    return {
        "time": np.asarray(dataset["time"]).tolist(),
        "theta": np.asarray(dataset["theta"]).tolist(),
        "order_parameter": np.asarray(dataset["order_parameter"]).tolist(),
        "frequencies": np.asarray(dataset["frequencies"]).tolist(),
        "adjacency": np.asarray(dataset["adjacency"]).tolist(),
        "config": {
            "solver": config.get("solver", "RK45"),
            "network_type": config.get("network_type", "All-to-All"),
            "frequency_distribution": config.get("frequency_distribution", "Normal"),
            "coupling": config.get("coupling", 2.0),
            "dt": config.get("dt", 0.05),
            "seed": config.get("seed", 42),
            "n_oscillators": config.get("n_oscillators", 24),
            "simulation_time": config.get("simulation_time", 20.0),
        },
    }


def export_dataset_npz(data: dict[str, Any], file_object: BinaryIO) -> None:
    """Serialize simulation state into compressed .npz archive conforming to the benchmark schema."""
    metadata = json.dumps(data.get("config", {}))
    np.savez_compressed(
        file_object,
        time=np.asarray(data["time"], dtype=float),
        theta=np.asarray(data["theta"], dtype=float),
        order_parameter=np.asarray(data["order_parameter"], dtype=float),
        natural_frequencies=np.asarray(data["frequencies"], dtype=float),
        adjacency=np.asarray(data["adjacency"], dtype=float),
        metadata=metadata,
    )
