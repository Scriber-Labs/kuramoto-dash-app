"""Unit tests for configuration, validation, simulation, and benchmark services."""

from __future__ import annotations

import io
import json

import numpy as np
import pytest

from app.services.benchmark import export_dataset_npz, package_simulation_payload
from app.services.cli_bridge import build_cli_config
from app.services.diagnostics import (
    analyze_graph_topology,
    analyze_spectral_dynamics,
)
from app.services.simulation import (
    build_adjacency,
    collect_config,
    generate_dataset,
    generate_frequencies,
)
from app.services.topology import TopologyRegistry, parse_custom_adjacency
from app.services.validation import check_nyquist_sampling, validate_simulation_inputs


def test_nyquist_sampling_evaluation() -> None:
    # High frequency / large dt -> undersampled warning
    res_under = check_nyquist_sampling(dt=0.8, frequencies=[10.0, -10.0], coupling=2.0)
    assert res_under["status"] == "undersampled"
    assert res_under["level"] == "warning"
    assert "Undersampling" in res_under["message"]
    assert res_under["sampling_ratio"] < 1.0

    # Very small dt -> oversampled info
    res_over = check_nyquist_sampling(dt=0.0005, frequencies=[0.5, -0.5], coupling=0.2)
    assert res_over["status"] == "oversampled"
    assert res_over["level"] == "info"
    assert res_over["sampling_ratio"] > 40.0

    # Normal dt -> optimal success
    res_opt = check_nyquist_sampling(dt=0.05, frequencies=[1.0, -1.0], coupling=1.0)
    assert res_opt["status"] == "optimal"
    assert res_opt["level"] == "success"
    assert "Satisfied" in res_opt["message"]


def test_long_horizon_payload_decimation() -> None:
    # Create dataset with 2500 steps
    time_long = np.linspace(0, 125, 2500)
    theta_long = np.zeros((2500, 4))
    r_long = np.ones(2500)
    freqs = np.array([0.1, 0.2, -0.1, -0.2])
    adj = np.ones((4, 4)) - np.eye(4)

    dataset = {
        "time": time_long,
        "theta": theta_long,
        "order_parameter": r_long,
        "frequencies": freqs,
        "adjacency": adj,
    }
    config = {
        "dt": 0.05,
        "coupling": 1.0,
        "seed": 27,
    }

    payload = package_simulation_payload(dataset, config, max_frames=500)
    assert len(payload["time"]) <= 501
    assert payload["raw_frame_count"] == 2500
    assert payload["stride"] > 1
    assert "nyquist" in payload
    assert payload["nyquist"]["status"] in {"optimal", "oversampled", "undersampled"}


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
    assert res["simulation_time"] == 50.0
    assert res["dt"] == 0.05
    assert res["seed"] == 27
    assert res["frequency_distribution"] == "Normal"


def test_validation_errors() -> None:
    with pytest.raises(ValueError, match="at least 2 oscillators"):
        validate_simulation_inputs(1, 2.0, 10.0, 0.05, 42, "Normal", "Ring", "RK45")

    with pytest.raises(ValueError, match="supports at most 500"):
        validate_simulation_inputs(501, 2.0, 10.0, 0.05, 42, "Normal", "Ring", "RK45")

    with pytest.raises(ValueError, match="positive"):
        validate_simulation_inputs(10, 2.0, -5.0, 0.05, 42, "Normal", "Ring", "RK45")

    with pytest.raises(
        ValueError, match="Frequency standard deviation must be positive"
    ):
        validate_simulation_inputs(
            10, 2.0, 10.0, 0.05, 42, "Normal", "Ring", "RK45", frequency_std=-1.0
        )


def test_generate_frequencies_distributions() -> None:
    n = 16
    for dist in ["Normal", "Uniform", "Bimodal", "Golden Ratio", "Custom"]:
        freqs = generate_frequencies(
            n=n, distribution=dist, seed=42, custom_values="-1, 0, 1"
        )
        assert isinstance(freqs, np.ndarray)
        assert len(freqs) == n
        assert np.all(np.isfinite(freqs))


def test_build_adjacency_topologies() -> None:
    n = 8
    for net in ["All-to-All", "Ring", "Random", "Small-World"]:
        adj = build_adjacency(net, n=n, seed=42)
        assert adj.shape == (n, n)
        assert np.all((adj == 0) | (adj == 1))
        # Adjacency should be symmetric and diagonal should be 0
        np.testing.assert_array_equal(adj, adj.T)
        np.testing.assert_array_equal(np.diag(adj), np.zeros(n))


def test_tree_of_life_topology() -> None:
    adj = build_adjacency("Tree of Life", n=10, seed=42)
    assert adj.shape == (10, 10)
    layout = TopologyRegistry.get_layout("tree_of_life", 10, adj)
    assert len(layout) == 10
    labels = TopologyRegistry.get_labels("tree_of_life", 10)
    assert len(labels) == 10
    assert labels[0] == "Keter"


def test_custom_adjacency() -> None:
    text = "0 1 1\n1 0 1\n1 1 0"
    parsed = parse_custom_adjacency(text, 3)
    assert parsed.shape == (3, 3)
    np.testing.assert_array_equal(parsed, np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]]))


def test_simulation_solvers() -> None:
    for solver_name in ["RK45", "Euler", "Rotor"]:
        cfg = collect_config(
            n_oscillators=6,
            coupling=2.0,
            simulation_time=1.0,
            dt=0.1,
            seed=42,
            frequency_distribution="Normal",
            network_type="All-to-All",
            solver=solver_name,
        )
        ds = generate_dataset(**cfg)
        assert "time" in ds
        assert "theta" in ds
        assert "order_parameter" in ds
        assert ds["theta"].shape == (len(ds["time"]), 6)
        assert len(ds["order_parameter"]) == len(ds["time"])
        assert np.all((ds["order_parameter"] >= 0) & (ds["order_parameter"] <= 1.05))


def test_diagnostics_and_graph_metrics() -> None:
    adj = build_adjacency("Tree of Life", n=10)
    topo = analyze_graph_topology(adj)
    assert topo["n_nodes"] == 10
    assert topo["is_connected"] is True
    assert topo["density"] > 0

    times = np.linspace(0, 10, 100)
    order = np.cos(times) ** 2
    spec = analyze_spectral_dynamics(times, order, dt=0.1)
    assert "dt" in spec


def test_cli_config_builder() -> None:
    cfg = build_cli_config(
        n_oscillators=10,
        coupling_strength=1.5,
        topology="small_world",
        timesteps=200,
        dt=0.05,
        seed=42,
        solver="rotor",
    )
    assert cfg["n_oscillators"] == 10
    assert cfg["coupling_strength"] == 1.5
    assert cfg["solver"] == "rotor"
    assert cfg["topology"] == "small_world"


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
    assert "graph_stats" in loaded

    meta = json.loads(str(loaded["metadata"]))
    assert meta["solver"] == "RK45"
    assert meta["network_type"] == "Ring"
