"""Unit tests for callback registrations and execution handlers."""

from __future__ import annotations

from dash import Dash

from app.callbacks import (
    register_callbacks,
    register_dataset_callbacks,
    register_simulation_callbacks,
    register_visualization_callbacks,
)
from app.callbacks.dataset import handle_advance_animation, handle_toggle_animation
from app.callbacks.simulation import handle_run_or_reset
from app.callbacks.visualization import handle_update_visuals
from app.services import collect_config, generate_dataset, package_simulation_payload


def test_register_callbacks() -> None:
    app = Dash(__name__)
    register_callbacks(app)
    assert len(app.callback_map) > 0


def test_simulation_callback_execution() -> None:
    # Test reset action
    data, max_f, val, status = handle_run_or_reset(
        triggered_id="reset-btn",
        n_oscillators=10,
        coupling=2.0,
        simulation_time=5.0,
        dt=0.1,
        seed=42,
        frequency_distribution="Normal",
        network_type="All-to-All",
        solver="RK45",
        frequency_mean=0.0,
        frequency_std=1.0,
        custom_frequencies="",
    )
    assert data is None
    assert max_f == 1
    assert val == 0
    assert "Ready" in status

    # Test run action
    data, max_f, val, status = handle_run_or_reset(
        triggered_id="run-btn",
        n_oscillators=6,
        coupling=2.0,
        simulation_time=2.0,
        dt=0.1,
        seed=42,
        frequency_distribution="Normal",
        network_type="Ring",
        solver="RK45",
        frequency_mean=0.0,
        frequency_std=1.0,
        custom_frequencies="",
    )
    assert data is not None
    assert "time" in data
    assert max_f > 0
    assert "Generated" in status


def test_visualization_callback_execution() -> None:
    # Test empty state
    res_empty = handle_update_visuals(data=None, frame=0)
    assert len(res_empty) == 7

    # Test populated state
    cfg = collect_config(4, 1.0, 1.0, 0.1, 42, "Normal", "Ring", "RK45")
    ds = generate_dataset(**cfg)
    payload = package_simulation_payload(ds, cfg)

    res_populated = handle_update_visuals(data=payload, frame=2)
    assert len(res_populated) == 7
    # Verify all figure outputs are valid Plotly figures
    for fig in res_populated[:6]:
        assert hasattr(fig, "to_plotly_json")


def test_dataset_callback_handlers() -> None:
    data = {"time": [0.0, 0.1, 0.2, 0.3]}
    assert handle_advance_animation(data, 0) == 1
    assert handle_advance_animation(data, 3) == 0

    disabled, text = handle_toggle_animation("run-btn", True)
    assert disabled is False
    assert text == "Pause animation"

    disabled, text = handle_toggle_animation("reset-btn", False)
    assert disabled is True
    assert text == "Play animation"
