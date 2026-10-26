"""Unit tests for configuration, validation, multi-paradigm solvers, and benchmark services."""

from __future__ import annotations

import io
import json

import numpy as np
import pytest

from app.services.benchmark import export_dataset_npz, package_simulation_payload
from app.services.cli_bridge import build_cli_config
from app.services.diagnostics import (
    DiagnosticRegistry,
    analyze_graph_topology,
    analyze_lie_symmetries,
    analyze_spectral_dynamics,
    compute_quantum_mode_comparison,
)
from app.services.simulation import (
    build_adjacency,
    collect_config,
    generate_dataset,
    generate_frequencies,
)
from app.services.solvers import SolverRegistry
from app.services.topology import TopologyRegistry, parse_custom_adjacency
from app.services.validation import check_nyquist_sampling, validate_simulation_inputs


def test_nyquist_sampling_evaluation() -> None:
    # High frequency / large dt -> undersampled warning
    res_under = check_nyquist_sampling(dt=0.8, frequencies=[10.0, -10.0], coupling=2.0)
    assert res_under["status"] == "undersampled"
    assert res_under["level"] == "warning"
    assert "Undersampling" in res_under["message"]
    assert res_under["sampling_ratio"] < 1.0

    # Euler solver under stiff coupling and undersampling -> specific Euler instability warning
    res_euler_stiff = check_nyquist_sampling(
        dt=0.8, frequencies=[10.0, -10.0], coupling=5.0, solver="Euler"
    )
    assert res_euler_stiff["status"] == "undersampled"
    assert "Fixed-Step Euler Instability" in res_euler_stiff["message"]

    # Euler solver near boundary -> marginal warning
    res_euler_marg = check_nyquist_sampling(
        dt=0.08, frequencies=[1.0, -1.0], coupling=2.0, solver="Euler"
    )
    assert res_euler_marg["status"] in {"marginal", "optimal"}

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
    assert res["adaptive_rtol"] == 1e-5
    assert res["adaptive_atol"] == 1e-7
    assert res["shots"] == 1024


def test_validation_errors() -> None:
    with pytest.raises(ValueError, match="Oscillator count must be an integer"):
        validate_simulation_inputs(
            n_oscillators="invalid",  # type: ignore[arg-type]
            coupling=1.0,
            simulation_time=10.0,
            dt=0.05,
            seed=0,
            frequency_distribution="Normal",
            network_type="All-to-All",
            solver="RK45",
        )

    with pytest.raises(ValueError, match="at least 2 oscillators"):
        validate_simulation_inputs(
            n_oscillators=1,
            coupling=1.0,
            simulation_time=10.0,
            dt=0.05,
            seed=0,
            frequency_distribution="Normal",
            network_type="All-to-All",
            solver="RK45",
        )

    with pytest.raises(ValueError, match="must be positive"):
        validate_simulation_inputs(
            n_oscillators=10,
            coupling=1.0,
            simulation_time=-5.0,
            dt=0.05,
            seed=0,
            frequency_distribution="Normal",
            network_type="All-to-All",
            solver="RK45",
        )


def test_multi_paradigm_solvers() -> None:
    solvers = [
        "rk45",
        "euler_fast",
        "vectorized_geometric",
        "rkmk4",
        "dopri54",
        "midpoint_geometric",
        "predictor_corrector",
        "adaptive_embedded",
        "quantum_statevector",
        "quantum_expectation",
        "shot_sampling",
    ]
    for s_name in solvers:
        cfg = collect_config(
            n_oscillators=4,
            coupling=2.0,
            simulation_time=0.5,
            dt=0.05,
            seed=42,
            frequency_distribution="Normal",
            network_type="All-to-All",
            solver=s_name,
            adaptive_rtol=1e-5,
            adaptive_atol=1e-7,
            shots=256,
        )
        ds = generate_dataset(**cfg)
        assert len(ds["time"]) > 0
        assert ds["theta"].shape == (len(ds["time"]), 4)
        assert len(ds["order_parameter"]) == len(ds["time"])


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
    assert "psd_freqs" in spec
    assert "fft_freqs" in spec


def test_lie_symmetries_and_reversibility() -> None:
    times = np.linspace(0, 2, 20)
    phases = np.outer(np.linspace(0, 1, 20), np.array([0.0, 0.5, 1.0, 1.5]))
    adj = np.ones((4, 4)) - np.eye(4)
    omega = np.array([-0.5, -0.1, 0.1, 0.5])

    sym = analyze_lie_symmetries(
        times=times,
        phases=phases,
        adj_matrix=adj,
        coupling=2.0,
        omega=omega,
        dt=0.1,
    )
    assert "interaction_energy" in sym
    assert "noether_charge" in sym
    assert "rotor_unitarity" in sym
    assert "u1_alphas" in sym
    assert "reversibility_residuals" in sym
    assert len(sym["reversibility_residuals"]) == len(times)


def test_quantum_mode_comparison_service() -> None:
    omega = np.array([-0.5, 0.5])
    adj = np.array([[0.0, 1.0], [1.0, 0.0]])
    q_comp = compute_quantum_mode_comparison(
        omega=omega,
        adj_matrix=adj,
        k_coupling=2.0,
        t_span=1.0,
        dt=0.1,
        seed=42,
        shots=128,
    )
    assert "r_statevector" in q_comp
    assert "r_shot_mean" in q_comp
    assert len(q_comp["r_statevector"]) == len(q_comp["time"])


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
