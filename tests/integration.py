"""End-to-end integration tests for Kuramoto Dash simulation pipeline."""

from __future__ import annotations

import io

import numpy as np

from app.callbacks.visualization import handle_update_visuals
from app.services import (
    collect_config,
    export_dataset_npz,
    generate_dataset,
    package_simulation_payload,
)


def test_end_to_end_simulation_and_export_pipeline() -> None:
    # 1. Parameter collection & validation
    config = collect_config(
        n_oscillators=8,
        coupling=2.5,
        simulation_time=3.0,
        dt=0.05,
        seed=100,
        frequency_distribution="Normal",
        network_type="All-to-All",
        solver="RK45",
        frequency_mean=0.0,
        frequency_std=1.0,
    )
    assert config["n_oscillators"] == 8
    assert config["frequencies"].shape == (8,)
    assert config["adjacency"].shape == (8, 8)

    # 2. Simulation execution
    dataset = generate_dataset(**config)
    n_pts = len(dataset["time"])
    assert n_pts >= 60
    assert dataset["theta"].shape == (n_pts, 8)
    assert dataset["order_parameter"].shape == (n_pts,)

    # 3. Packaging into client state store format
    payload = package_simulation_payload(dataset, config)
    assert payload["config"]["seed"] == 100
    assert len(payload["time"]) == n_pts

    # 4. Visualization figures generation
    figures_and_cards = handle_update_visuals(payload, frame=30)
    assert len(figures_and_cards) == 7

    # 5. Export to compressed benchmark .npz
    buffer = io.BytesIO()
    export_dataset_npz(payload, buffer)
    buffer.seek(0)

    loaded = np.load(buffer)
    np.testing.assert_array_equal(loaded["time"], dataset["time"])
    np.testing.assert_array_equal(loaded["theta"], dataset["theta"])
    np.testing.assert_array_equal(loaded["order_parameter"], dataset["order_parameter"])
    np.testing.assert_array_equal(loaded["natural_frequencies"], dataset["frequencies"])
    np.testing.assert_array_equal(loaded["adjacency"], dataset["adjacency"])
