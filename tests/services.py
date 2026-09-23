"""Unit tests for configuration, validation, simulation, and benchmark services."""

from __future__ import annotations

import io
import json

import numpy as np
import pytest

from app.services.benchmark import export_dataset_npz, package_simulation_payload
from app.services.simulation import (
    build_adjacency,
    collect_config,
    generate_dataset,
    generate_frequencies,
    parse_adjacency_text,
)
from app.services.validation import validate_simulation_inputs


def test_validation_defaults() -> None:
    res = validate_simulation_inputs(
        n_oscillators=None,
        coupling=None,
        simulation_time=None,
        dt=None,
        seed=None,
        frequency_distribution=None,
        network_type=None,
        solver=None,
    )
    assert res["n_oscillators"] == 24
    assert res["coupling"] == 2.0
    assert res["simulation_time"] == 20.0
    assert res["dt"] == 0.05
    assert res["seed"] == 42
    assert res["frequency_distribution"] == "Normal"


def test_validation_errors() -> None:
    with pytest.raises(ValueError, match="at least 2 oscillators"):
        validate_simulation_inputs(1, 2.0, 10.0, 0.05, 42, "Normal", "Ring", "RK45")

    with pytest.raises(ValueError, match="supports at most 100"):
        validate_simulation_inputs(101, 2.0, 10.0, 0.05, 42, "Normal", "Ring", "RK45")

    with pytest.raises(ValueError, match="positive"):
        validate_simulation_inputs(10, 2.0, -5.0, 0.05, 42, "Normal", "Ring", "RK45")

    with pytest.raises(ValueError, match="Frequency standard deviation must be positive"):
        validate_simulation_inputs(
            10, 2.0, 10.0, 0.05, 42, "Normal", "Ring", "RK45", frequency_std=-1.0
        )


def test_generate_frequencies_distributions() -> None:
    n = 16
    for dist in ["Normal", "Uniform", "Bimodal", "Golden Ratio", "Custom"]:
        freqs = generate_frequencies(n=n, distribution=dist, seed=42, custom_values="-1, 0, 1")
        assert isinstance(freqs, np.ndarray)
        assert len(freqs) == n
        assert np.all(np.isfinite(freqs))


def test_build_adjacency_topologies() -> None:
    n = 8
    for net in ["All-to-All", "Ring", "Random"]:
        adj = build_adjacency(net, n=n, seed=42)
        assert adj.shape == (n, n)
        assert np.all((adj == 0) | (adj == 1))
        # Adjacency should be symmetric and diagonal should be 0
        np.testing.assert_array_equal(adj, adj.T)
        np.testing.assert_array_equal(np.diag(adj), np.zeros(n))


def test_parse_adjacency_text() -> None:
    text = "0 1 1\n1 0 1\n1 1 0"
    parsed = parse_adjacency_text(text, 3)
    assert parsed.shape == (3, 3)
    assert np.all(parsed == np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]]))


def test_simulation_rk45_and_euler() -> None:
    cfg_rk45 = collect_config(
        n_oscillators=6,
        coupling=2.0,
        simulation_time=2.0,
        dt=0.1,
        seed=42,
        frequency_distribution="Normal",
        network_type="All-to-All",
        solver="RK45",
    )
    ds_rk45 = generate_dataset(**cfg_rk45)
    assert "time" in ds_rk45
    assert "theta" in ds_rk45
    assert "order_parameter" in ds_rk45
    assert ds_rk45["theta"].shape == (len(ds_rk45["time"]), 6)
    assert len(ds_rk45["order_parameter"]) == len(ds_rk45["time"])
    assert np.all((ds_rk45["order_parameter"] >= 0) & (ds_rk45["order_parameter"] <= 1.05))

    cfg_euler = collect_config(
        n_oscillators=6,
        coupling=2.0,
        simulation_time=2.0,
        dt=0.1,
        seed=42,
        frequency_distribution="Normal",
        network_type="All-to-All",
        solver="Euler",
    )
    ds_euler = generate_dataset(**cfg_euler)
    assert ds_euler["theta"].shape == (len(ds_euler["time"]), 6)
    assert len(ds_euler["order_parameter"]) == len(ds_euler["time"])


def test_benchmark_export() -> None:
    cfg = collect_config(
        n_oscillators=4,
        coupling=1.5,
        simulation_time=1.0,
        dt=0.1,
        seed=42,
        frequency_distribution="Normal",
        network_type="Ring",
        solver="RK45",
    )
    ds = generate_dataset(**cfg)
    payload = package_simulation_payload(ds, cfg)

    buffer = io.BytesIO()
    export_dataset_npz(payload, buffer)
    buffer.seek(0)

    loaded = np.load(buffer)
    assert "time" in loaded
    assert "theta" in loaded
    assert "order_parameter" in loaded
    assert "natural_frequencies" in loaded
    assert "adjacency" in loaded
    assert "metadata" in loaded

    meta = json.loads(str(loaded["metadata"]))
    assert meta["solver"] == "RK45"
    assert meta["network_type"] == "Ring"
